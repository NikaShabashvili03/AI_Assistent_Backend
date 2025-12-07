from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import ConnectionRequest, Connection, User

class ReceivedConnectionRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = ConnectionRequest.objects.filter(
            to_user=request.user,
            status="pending"
        )

        data = []
        for req in requests:
            sender = req.from_user
            data.append({
                "request_id": req.id,
                "from_user_id": sender.id,
                "from_user_name": sender.firstname,
                "sent_at": req.created_at 
            })

        return Response({"received_requests": data})
    
class SendConnectionRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if request.user.id == user_id:
            return Response({"error": "Can't connect to yourself"}, status=400)

        try:
            to_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        u1, u2 = sorted([request.user, to_user], key=lambda u: u.id)

        connected = Connection.objects.filter(
            user1=u1,
            user2=u2
        ).exists()

        if connected:
            return Response({"error": "Already connected"}, status=400)

        req, created = ConnectionRequest.objects.get_or_create(
            from_user=request.user,
            to_user=to_user
        )

        if not created:
            return Response({"error": "Request already sent"}, status=400)

        return Response({"success": "Request sent"})


class AcceptConnectionRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        try:
            req = ConnectionRequest.objects.get(
                id=request_id,
                to_user=request.user,
                status="pending"
            )
        except ConnectionRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=404)

        req.status = "accepted"
        req.save()

        u1, u2 = sorted([req.from_user, req.to_user], key=lambda u: u.id)

        Connection.objects.create(user1=u1, user2=u2)

        return Response({"success": "Accepted"})

class DeclineConnectionRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        try:
            req = ConnectionRequest.objects.get(
                id=request_id,
                to_user=request.user,
                status="pending"
            )
        except ConnectionRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=404)

        req.status = "rejected"
        req.save()

        return Response({"success": "Declined"})

class ListConnections(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        connections = (
            Connection.objects.filter(user1=request.user) |
            Connection.objects.filter(user2=request.user)
        )

        data = []
        for c in connections:
            other = c.user2 if c.user1 == request.user else c.user1
            data.append({
                "id": other.id,
                "firstname": other.firstname
            })

        return Response({"connections": data})

class SuggestedConnections(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        existing_ids = self.get_user_connection_ids(user)

        sent = ConnectionRequest.objects.filter(
            from_user=user
        ).values_list("to_user_id", flat=True) 

        received = ConnectionRequest.objects.filter(
            to_user=user
        ).values_list("from_user_id", flat=True) 

        exclude_ids = set(existing_ids) | set(sent) | set(received) | {user.id}

        candidates = User.objects.exclude(id__in=exclude_ids)

        my_connections = existing_ids
        suggestions = []

        for u in candidates:
            user_connections = self.get_user_connection_ids(u)
            
            mutuals = len(my_connections.intersection(user_connections))

            suggestions.append({
                "id": u.id,
                "name": u.firstname,
                "mutual_connections": mutuals
            })

        suggestions = sorted(suggestions, key=lambda x: x["mutual_connections"], reverse=True)

        return Response({"suggestions": suggestions})

    def get_user_connection_ids(self, user):
        if hasattr(user, 'id'):
            user_id = user.id
        else:
            user_id = user

        ids1 = Connection.objects.filter(user1_id=user_id).values_list("user2_id", flat=True)
        ids2 = Connection.objects.filter(user2_id=user_id).values_list("user1_id", flat=True)

        return set(list(ids1) + list(ids2))