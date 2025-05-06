from django.urls import path
from .views import graph_view

urlpatterns = [
    path('', graph_view, name='graph_view'),
]
