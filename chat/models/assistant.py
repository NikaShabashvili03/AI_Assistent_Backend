from django.db import models


class Assistant(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    prompt = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"