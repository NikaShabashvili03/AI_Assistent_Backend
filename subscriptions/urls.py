from django.urls import path
from .views import (
    SubscriptionPlansAPIView,
    CreateCheckoutSessionAPIView,
    ChangeSubscriptionAPIView,
    CancelSubscriptionAPIView,
    CheckSubscriptionAPIView,
    StripeWebhookAPIView,
)

urlpatterns = [
    path("plans/", SubscriptionPlansAPIView.as_view(), name="plans"),
    path("checkout/create/", CreateCheckoutSessionAPIView.as_view(), name="create-checkout"),
    path("subscription/change/", ChangeSubscriptionAPIView.as_view(), name="change-subscription"),
    path("subscription/cancel/", CancelSubscriptionAPIView.as_view(), name="cancel-subscription"),
    path("subscription/check/", CheckSubscriptionAPIView.as_view(), name="check-subscription"),
    path("stripe/webhook/", StripeWebhookAPIView.as_view(), name="stripe-webhook"),
]
