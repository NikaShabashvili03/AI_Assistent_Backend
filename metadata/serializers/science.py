from rest_framework import serializers
from ..models import Science

class ScienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Science
        fields = ['id', 'name', 'created_at']
