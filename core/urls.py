from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('event/<str:access_code>/', views.event_detail, name='event_detail'),
]