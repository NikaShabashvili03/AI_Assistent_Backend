from . import UserSerializer
from rest_framework import serializers
from ..models import Log

class LogSerializer(serializers.ModelSerializer):
    triggered_by = UserSerializer(read_only=True)

    class Meta:
        model = Log
        fields = [
            'id',
            'model_name',
            'object_id',
            'action',
            'timestamp',
            'changes',
            'triggered_by',
        ]