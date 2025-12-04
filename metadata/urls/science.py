from django.urls import path
from metadata.views.science import ScienceListView

urlpatterns = [
    path('list', ScienceListView.as_view(), name='list'),
]