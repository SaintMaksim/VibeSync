from django.contrib import admin
from .models import Event, Track, TrackSuggestion

class TrackSuggestionInline(admin.TabularInline):
    model = TrackSuggestion
    extra = 0
    readonly_fields = ('event', 'suggested_by', 'votes_score', 'suggested_at')
    can_delete = True

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'lastfm_id', 'tags', 'get_suggestion_count')
    list_filter = ('artist',)
    search_fields = ('title', 'artist', 'tags')
    actions = ['delete_with_suggestions']
    inlines = [TrackSuggestionInline]

    def get_suggestion_count(self, obj):
        return obj.suggestions.count()
    get_suggestion_count.short_description = 'Предложений'

    @admin.action(description='Удалить выбранные треки и все предложения')
    def delete_with_suggestions(self, request, queryset):
        suggestion_ids = TrackSuggestion.objects.filter(track__in=queryset).values_list('id', flat=True)
        TrackSuggestion.objects.filter(id__in=suggestion_ids).delete()
        deleted_count = queryset.delete()[0]
        self.message_user(request, f'Удалено {deleted_count} треков и все связанные предложения.')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'access_code', 'is_active', 'ends_at')
    list_filter = ('is_active', 'host')
    search_fields = ('title', 'access_code')

@admin.register(TrackSuggestion)
class TrackSuggestionAdmin(admin.ModelAdmin):
    list_display = ('track', 'event', 'suggested_by', 'votes_score')
    list_filter = ('event', 'suggested_by')
    search_fields = ('track__title', 'track__artist')