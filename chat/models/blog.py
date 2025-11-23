from django.db import models

class Blog(models.Model):
    blog_title = models.CharField(max_length=255)
    summary = models.TextField()
    key_ideas = models.JSONField(default=list) 
    original_chapter_title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.blog_title