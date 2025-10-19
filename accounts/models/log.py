from django.db import models
from django.utils.timezone import now
from accounts.models import User

class Log(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100) 
    action = models.CharField(max_length=6, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=now)
    changes = models.TextField(blank=True, null=True)  
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='logs',
        null=True,
        blank=True,
    )


    def __str__(self):
        return f"{self.model_name} [{self.object_id}] {self.action} at {self.timestamp}"