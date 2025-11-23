from django.urls import path
from chat.views.blog import BlogFeedView

urlpatterns = [
    path('list', BlogFeedView.as_view(), name='list'),
]