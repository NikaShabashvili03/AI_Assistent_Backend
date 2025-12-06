from rest_framework import serializers
from ..models import ConnectionRequest, Connection

class ConnectionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectionRequest
        fields = "__all__"
        read_only_fields = ("from_user", "status")


class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = "__all__"
