from django.urls import path
from accounts.views.log import LogListView

urlpatterns = [
    path('list', LogListView.as_view(), name='log list'),
]