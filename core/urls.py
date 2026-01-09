from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('event/<str:access_code>/', views.event_detail, name='event_detail'),
    path('event/<str:access_code>/playlist/', views.final_playlist, name='final_playlist'),
    path('event/<str:access_code>/download/', views.download_playlist, name='download_playlist'),
]