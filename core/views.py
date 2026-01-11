from django.db import IntegrityError
from django.contrib import messages
from .models import Event, Track, TrackSuggestion
from .utils import search_tracks
from .utils import balance_playlist, parse_genres_from_tags
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Count, F
from django.contrib.auth import login, logout
from .forms import EventForm
import secrets
import string

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

    # Аннотируем предложения рейтингом
    base_suggestions = event.suggestions.annotate(
        calculated_score=Count('liked_by') - Count('disliked_by')
    ).select_related('track')

    if request.method == "POST":
        action = request.POST.get("action")

        # Голосование за трек
        if action == "vote":
            suggestion_id = request.POST.get("suggestion_id")
            vote_type = request.POST.get("vote_type")
            try:
                suggestion = TrackSuggestion.objects.get(id=suggestion_id, event=event)

                if not request.user.is_authenticated:
                    messages.error(request, "Только зарегистрированные пользователи могут голосовать.")
                else:
                    if vote_type == "like":
                        # Если уже лайкал — убираем лайк
                        if request.user in suggestion.liked_by.all():
                            suggestion.liked_by.remove(request.user)
                        else:
                            # Иначе добавляем лайк и убираем дизлайк (если был)
                            suggestion.liked_by.add(request.user)
                            suggestion.disliked_by.remove(request.user)

                    elif vote_type == "dislike":
                        # Если уже дизлайкал — убираем дизлайк
                        if request.user in suggestion.disliked_by.all():
                            suggestion.disliked_by.remove(request.user)
                        else:
                            # Иначе добавляем дизлайк и убираем лайк (если был)
                            suggestion.disliked_by.add(request.user)
                            suggestion.liked_by.remove(request.user)

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

        # Предложение нового трека
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

        # Поиск треков
        else:
            query = request.POST.get("query", "").strip()
            search_results = search_tracks(query, limit=5) if query else []
            suggestions = base_suggestions.order_by('-calculated_score')
            return render(request, 'core/event_detail.html', {
                'event': event,
                'suggestions': suggestions,
                'search_results': search_results,
                'query': query,
            })

    # GET-запрос
    suggestions = base_suggestions.order_by('-calculated_score')
    return render(request, 'core/event_detail.html', {
        'event': event,
        'suggestions': suggestions,
    })

def final_playlist(request, access_code):
    event = get_object_or_404(Event, access_code=access_code, host=request.user)

    annotated_suggestions = event.suggestions.annotate(
        calculated_score=Count('liked_by') - Count('disliked_by')
    ).select_related('track')

    # Получаем сбалансированный QuerySet напрямую
    balanced_suggestions = balance_playlist(annotated_suggestions, event.max_genre_percent)

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


def home(request):
    return render(request, 'core/home.html')

def logout_view(request):
    logout(request)
    return redirect('core:home')

def generate_random_password(length=32):
    """Генерирует случайный пароль заданной длины"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def simple_register(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Пожалуйста, введите ваше имя.")
            return render(request, 'core/simple_register.html')

        if len(name) < 2:
            messages.error(request, "Имя должно содержать минимум 2 символа.")
            return render(request, 'core/simple_register.html')

        # Очищаем имя от лишних символов
        import re
        clean_name = re.sub(r'[^a-zA-Zа-яА-Я0-9\s]', '', name)
        username_base = clean_name.lower().replace(" ", "_")

        # Гарантированно уникальное имя
        username = username_base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{username_base}_{counter}"
            counter += 1
            # Защита от бесконечного цикла
            if counter > 1000:
                username = f"user_{User.objects.count() + 1}"
                break

        # Генерируем пароль
        password = generate_random_password()
        try:
            user = User.objects.create_user(
                username=username,
                first_name=name[:30],
                password=password
            )
            login(request, user)
            messages.success(request, f"Добро пожаловать, {name}!")
            return redirect('core:home')
        except IntegrityError:
            # На случай гонки (очень редко)
            messages.error(request, "Ошибка регистрации. Попробуйте другое имя.")
            return render(request, 'core/simple_register.html')

    return render(request, 'core/simple_register.html')


def create_event(request):
    if not request.user.is_authenticated:
        return redirect('core:home')

    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.host = request.user
            event.is_active = True
            event.save()
            messages.success(request, f"Мероприятие создано! Ссылка для гостей: /event/{event.access_code}/")
            return redirect('core:my_events')
    else:
        form = EventForm()

    return render(request, 'core/create_event.html', {'form': form})

def event_access(request):
    """Перенаправление на мероприятие по коду"""
    code = request.GET.get('code', '').strip()
    if code:
        return redirect('core:event_detail', access_code=code)
    return redirect('core:home')

def my_events(request):
    if not request.user.is_authenticated:
        return redirect('core:home')

    events = Event.objects.filter(host=request.user).order_by('-created_at')
    return render(request, 'core/my_events.html', {'events': events})