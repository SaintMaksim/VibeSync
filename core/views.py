from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Event, Track, TrackSuggestion
from .utils import search_tracks
from .utils import balance_playlist, parse_genres_from_tags
from django.http import HttpResponse


def download_playlist(request, access_code):
    event = get_object_or_404(Event, access_code=access_code, host=request.user)
    balanced = balance_playlist(event.suggestions.all(), event.max_genre_percent)

    response = HttpResponse(content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{event.title}_playlist.txt"'

    lines = [f"{i + 1}. {s.track.artist} — {s.track.title}"
             for i, s in enumerate(balanced)]
    response.write("\n".join(lines))
    return response

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

        # Удаление предложения (только для организатора)
        elif action == "delete_suggestion":
            suggestion_id = request.POST.get("suggestion_id")
            try:
                suggestion = TrackSuggestion.objects.get(id=suggestion_id, event=event)
                if request.user == event.host:
                    suggestion.delete()
                    messages.success(request, "Трек удалён из предложения.")
                else:
                    messages.error(request, "Только организатор может удалять треки.")
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


def final_playlist(request, access_code):
    event = get_object_or_404(Event, access_code=access_code, host=request.user)

    # Получаем сбалансированный QuerySet напрямую
    balanced_suggestions = balance_playlist(
        event.suggestions.select_related('track').all(),
        event.max_genre_percent
    )

    all_genres = []
    genre_to_tracks = {}

    for s in balanced_suggestions:
        genres = parse_genres_from_tags(s.track.tags)
        primary_genre = genres[0] if genres else 'unknown'#В случае если нет тега жанра то жанр "unknown"
        all_genres.append(primary_genre)

        if primary_genre not in genre_to_tracks:
            genre_to_tracks[primary_genre] = []
        genre_to_tracks[primary_genre].append(f"{s.track.artist} — {s.track.title}")

    from collections import Counter
    genre_counter = Counter(all_genres)
    chart_labels = list(genre_counter.keys())
    chart_data = list(genre_counter.values())

    context = {
        'event': event,
        'balanced_suggestions': balanced_suggestions,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'genre_to_tracks': genre_to_tracks,
    }
    return render(request, 'core/final_playlist.html', context)