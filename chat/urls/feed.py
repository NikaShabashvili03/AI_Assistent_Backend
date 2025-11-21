from django.urls import path
from chat.views.feed import FeedListView

urlpatterns = [
    path('list', FeedListView.as_view(), name='list'),
]