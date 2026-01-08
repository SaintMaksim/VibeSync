from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Event, Track, TrackSuggestion
from .utils import search_tracks


def event_detail(request, access_code):
    event = get_object_or_404(Event, access_code=access_code, is_active=True)

    #Обработка предложения трека
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "suggest":
            #Сохраняем трек если ещё не существует
            track, created = Track.objects.get_or_create(
                lastfm_id=request.POST["lastfm_id"],
                defaults={
                    "title": request.POST["title"],
                    "artist": request.POST["artist"],
                    "tags": request.POST.get("tags", ""),
                }
            )
            #Создаём предложение
            TrackSuggestion.objects.get_or_create(
                event=event,
                track=track,
                defaults={"suggested_by": request.user if request.user.is_authenticated else None}
            )
            messages.success(request, f"Трек «{track.title}» добавлен!")
            return redirect('core:event_detail', access_code=access_code)

        else:
            #Обычный поиск
            query = request.POST.get("query", "").strip()
            if query:
                search_results = search_tracks(query, limit=5)
                context = {
                    'event': event,
                    'suggestions': event.suggestions.select_related('track').order_by('-votes_score'),
                    'search_results': search_results,
                    'query': query,
                }
                return render(request, 'core/event_detail.html', context)

    suggestions = event.suggestions.select_related('track').order_by('-votes_score')
    return render(request, 'core/event_detail.html', {'event': event, 'suggestions': suggestions})