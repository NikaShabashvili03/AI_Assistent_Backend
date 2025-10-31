from django.db import models


class AssistantTags(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.name}"
    
class Assistant(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    prompt = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    tag = models.ForeignKey(AssistantTags, on_delete=models.CASCADE, related_name="assistants")

    def __str__(self):
        return f"{self.name}"    
