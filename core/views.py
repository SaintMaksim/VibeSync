from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Event, Track, TrackSuggestion
from .utils import search_tracks


def event_detail(request, access_code):
    event = get_object_or_404(Event, access_code=access_code, is_active=True)

    if request.method == "POST":
        action = request.POST.get("action")

        #Голосование за трек
        if action == "vote":
            suggestion_id = request.POST.get("suggestion_id")
            vote_type = request.POST.get("vote_type")
            try:
                suggestion = TrackSuggestion.objects.get(id=suggestion_id, event=event)
                if vote_type == "like":
                    suggestion.votes_score += 1
                elif vote_type == "dislike":
                    suggestion.votes_score -= 1
                suggestion.save()
                #Обновление без сообщения, просто перезагрузка
            except TrackSuggestion.DoesNotExist:
                messages.error(request, "Предложение не найдено.")
            return redirect('core:event_detail', access_code=access_code)

        #Предложение нового трека
        elif action == "suggest":
            track, created = Track.objects.get_or_create(
                lastfm_id=request.POST["lastfm_id"],
                defaults={
                    "title": request.POST["title"],
                    "artist": request.POST["artist"],
                    "tags": request.POST.get("tags", ""),
                }
            )
            TrackSuggestion.objects.get_or_create(
                event=event,
                track=track,
                defaults={"suggested_by": request.user if request.user.is_authenticated else None}
            )
            messages.success(request, f"Трек «{track.title}» добавлен!")
            return redirect('core:event_detail', access_code=access_code)

        #Поиск треков
        else:
            query = request.POST.get("query", "").strip()
            search_results = search_tracks(query, limit=5) if query else []
            suggestions = event.suggestions.select_related('track').order_by('-votes_score')
            return render(request, 'core/event_detail.html', {
                'event': event,
                'suggestions': suggestions,
                'search_results': search_results,
                'query': query,
            })

    #GET-запрос
    suggestions = event.suggestions.select_related('track').order_by('-votes_score')
    return render(request, 'core/event_detail.html', {
        'event': event,
        'suggestions': suggestions,
    })