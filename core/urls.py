from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.simple_register, name='simple_register'),
    path('event-access/', views.event_access, name='event_access'),
    path('create/', views.create_event, name='create_event'),
    path('my-events/', views.my_events, name='my_events'),
    path('event/<str:access_code>/', views.event_detail, name='event_detail'),
    path('event/<str:access_code>/playlist/', views.final_playlist, name='final_playlist'),
    path('event/<str:access_code>/download/', views.download_playlist, name='download_playlist'),
]