from django.contrib import admin
from .models import Event, Track, TrackSuggestion

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'access_code', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'access_code', 'host__username')

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('artist', 'title', 'lastfm_id')
    search_fields = ('title', 'artist', 'tags')

@admin.register(TrackSuggestion)
class TrackSuggestionAdmin(admin.ModelAdmin):
    list_display = ('event', 'track', 'suggested_by', 'votes_score')
    list_filter = ('event',)