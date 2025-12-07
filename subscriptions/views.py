import stripe
from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone

from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
from .utils import activate_subscription, cancel_subscription, has_active_subscription

stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionPlansAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)


class CreateCheckoutSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        price_id = request.data.get("price_id")
        if not price_id:
            return Response({"error": "price_id required"}, status=400)

        user = request.user
        if not getattr(user, "stripe_customer_id", None):
            customer = stripe.Customer.create(email=user.email, metadata={"user_id": user.id})
            user.stripe_customer_id = customer["id"]
            user.save()

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=user.stripe_customer_id,
            success_url=request.data.get("success_url") or settings.STRIPE_SUCCESS_URL,
            cancel_url=request.data.get("cancel_url") or settings.STRIPE_CANCEL_URL,
            line_items=[{"price": price_id, "quantity": 1}],
            payment_method_types=["card"],
            allow_promotion_codes=True,
            metadata={"user_id": str(user.id)},
        )

        return Response({"checkout_url": session.url, "session_id": session.id})


class ChangeSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_price = request.data.get("new_price_id")
        if not new_price:
            return Response({"error": "new_price_id required"}, status=400)

        user = request.user
        if not getattr(user, "stripe_customer_id", None):
            return Response({"error": "No Stripe customer found"}, status=400)

        subs = stripe.Subscription.list(customer=user.stripe_customer_id, status="all", limit=10)
        active_sub = None
        for s in subs.auto_paging_iter():
            if s["status"] in ("active", "trialing", "past_due"):
                active_sub = s
                break

        if not active_sub:
            return Response({"error": "No active Stripe subscription"}, status=400)

        item_id = active_sub["items"]["data"][0]["id"]

        updated = stripe.Subscription.modify(
            active_sub["id"],
            cancel_at_period_end=False,
            items=[{
                "id": item_id,
                "price": new_price,
            }],
            proration_behavior="create_prorations"
        )

        try:
            plan = SubscriptionPlan.objects.get(stripe_price_id=new_price)
            UserSubscription.objects.filter(user=user, status="active").update(plan=plan)
        except SubscriptionPlan.DoesNotExist:
            pass

        return Response({"success": True, "stripe_subscription": updated})


class CancelSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if getattr(user, "stripe_customer_id", None):
            subs = stripe.Subscription.list(customer=user.stripe_customer_id, limit=10)
            active_sub = None
            for s in subs.auto_paging_iter():
                if s["status"] in ("active", "trialing"):
                    active_sub = s
                    break
            if active_sub:
                stripe.Subscription.delete(active_sub["id"])

        success = cancel_subscription(user)
        if success:
            return Response({"message": "Subscription cancelled"})
        return Response({"error": "No active subscription"}, status=400)


class CheckSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"active": has_active_subscription(request.user)})


class StripeWebhookAPIView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            return HttpResponse(status=400)

        etype = event["type"]
        obj = event["data"]["object"]

        if etype == "invoice.paid":
            invoice = obj
            lines = invoice.get("lines", {}).get("data", [])
            if lines:
                price_id = lines[0]["price"]["id"]
            else:
                price_id = None

            customer_id = invoice.get("customer")
            payment_intent = invoice.get("payment_intent")

            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(stripe_customer_id=customer_id)
            except User.DoesNotExist:
                return HttpResponse(status=200) 

            try:
                plan = SubscriptionPlan.objects.get(stripe_price_id=price_id)
            except SubscriptionPlan.DoesNotExist:
                plan = None

            if plan:
                activate_subscription(user, plan, stripe_subscription_id=invoice.get("subscription"), payment_intent_id=payment_intent)

        elif etype == "customer.subscription.deleted":
            subscription = obj
            customer_id = subscription.get("customer")
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(stripe_customer_id=customer_id)
                cancel_subscription(user)
            except User.DoesNotExist:
                pass

        elif etype == "checkout.session.completed":
            session = obj
            customer_id = session.get("customer")
            subscription_id = session.get("subscription")
            metadata = session.get("metadata", {}) or {}
            user_id = metadata.get("user_id")

            if user_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=user_id)
                    if not getattr(user, "stripe_customer_id", None):
                        user.stripe_customer_id = customer_id
                        user.save()
                    
                except User.DoesNotExist:
                    pass

        elif etype == "invoice.payment_failed":
            invoice = obj
            customer_id = invoice.get("customer")

        return HttpResponse(status=200)
