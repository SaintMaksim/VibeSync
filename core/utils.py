import os
import requests
import pandas as pd
from django.db.models import Count
from dotenv import load_dotenv
from core.models import TrackSuggestion

load_dotenv()

LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'

def get_track_info(artist, title):
    """Получает детали трека (теги, длительность) через track.getInfo."""
    if not LASTFM_API_KEY:
        return {}

    params = {
        'method': 'track.getInfo',
        'api_key': LASTFM_API_KEY,
        'artist': artist,
        'track': title,
        'format': 'json',
    }

    try:
        response = requests.get(LASTFM_API_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        track_data = data.get('track', {})

        # Извлекаем длительность
        duration = None
        dur_str = track_data.get('duration')
        if dur_str and dur_str.isdigit():
            duration = int(dur_str)

        # Извлекаем теги
        tags = []
        toptags = track_data.get('toptags', {})
        if isinstance(toptags, dict):
            tag_list = toptags.get('tag', [])
            if isinstance(tag_list, list):
                tags = [tag.get('name', '') for tag in tag_list if tag.get('name')]
            elif isinstance(tag_list, dict) and tag_list.get('name'):
                tags = [tag_list['name']]

        return {
            'duration': duration,
            'tags': ', '.join(tags[:5]),
        }
    except Exception as e:
        print(f"track.getInfo error for {artist} - {title}: {e}")
        return {}


def balance_playlist(suggestions_queryset, max_genre_percent):
    """Улучшенный алгоритм: рейтинг важнее жанров"""
    if not suggestions_queryset.exists():
        return TrackSuggestion.objects.none()

    # Сортируем по рейтингу (главный приоритет)
    suggestions_list = list(suggestions_queryset.select_related('track'))
    suggestions_list.sort(key=lambda x: x.calculated_score, reverse=True)

    # Анализ жанров
    total_tracks = len(suggestions_list)
    max_genre_count = max(1, int(total_tracks * max_genre_percent / 100))

    selected_suggestions = []
    genre_counts = {}

    for suggestion in suggestions_list:
        genres = extract_genres_from_tags(suggestion.track.tags)

        if not genres or genres == ['unknown']:
            # Треки без жанров — всегда добавляем
            selected_suggestions.append(suggestion)
            continue

        # Проверяем: можно ли добавить хотя бы один жанр этого трека?
        can_add = False
        for genre in genres:
            current_count = genre_counts.get(genre, 0)
            if current_count < max_genre_count:
                can_add = True
                break

        if can_add:
            selected_suggestions.append(suggestion)
            # Обновляем счётчики для всех жанров трека
            for genre in genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        # Если нельзя добавить — пропускаем (но это редкость)

    # Возвращаем QuerySet
    selected_ids = [s.id for s in selected_suggestions]
    return TrackSuggestion.objects.filter(
        id__in=selected_ids
    ).annotate(
        calculated_score=Count('liked_by') - Count('disliked_by')
    ).select_related('track').order_by('-calculated_score')

def search_tracks(query: str, limit: int = 5):
    """
    Ищет треки в Last.fm по названию и дополняет их тегами через track.getInfo.
    Возвращает список словарей с данными трека.
    """
    if not LASTFM_API_KEY:
        print("Ошибка: LASTFM_API_KEY не задан в .env")
        return []

    # Шаг 1: Поиск треков
    params = {
        'method': 'track.search',
        'track': query,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit,
    }

    try:
        response = requests.get(LASTFM_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        tracks = []
        track_list = data.get('results', {}).get('trackmatches', {}).get('track', [])
        if isinstance(track_list, dict):
            track_list = [track_list]

        for item in track_list:
            artist = item.get('artist', '').strip()
            title = item.get('name', '').strip()
            if not artist or not title:
                continue

            # Шаг 2: Получаем инфу трека (теги, длительность)
            extra_info = get_track_info(artist, title)

            tracks.append({
                'title': title,
                'artist': artist,
                'lastfm_id': f"{artist} - {title}",
                'duration': extra_info.get('duration'),
                'tags': extra_info.get('tags', ''),
            })

        return tracks

    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Last.fm API error in search_tracks: {e}")
        return []

POPULAR_GENRES = {
    'rock', 'pop', 'hip hop', 'rap', 'electronic', 'jazz', 'classical',
    'metal', 'folk', 'country', 'blues', 'reggae', 'punk', 'indie',
    'r&b', 'soul', 'funk', 'disco', 'techno', 'house', 'ambient',
    'neofolk', 'chill', 'lo-fi', 'alternative', 'experimental'
}


def extract_genres_from_tags(tags_str):
    """Извлекает только жанры из тегов"""
    if not tags_str:
        return []

    all_tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]
    # Фильтруем только известные жанры
    genres = [tag for tag in all_tags if tag in POPULAR_GENRES]
    return genres if genres else ['unknown']


GENRE_TO_MOOD = {
    # Энергичные
    'rock': 8, 'metal': 9, 'punk': 8, 'techno': 7, 'hip hop': 6,
    'rap': 6, 'electronic': 7, 'disco': 7, 'funk': 6,

    # Спокойные
    'jazz': 3, 'classical': 2, 'ambient': 1, 'lo-fi': 2, 'chill': 2,
    'folk': 4, 'acoustic': 3, 'neofolk': 3,

    # Средние
    'pop': 5, 'indie': 5, 'alternative': 5, 'r&b': 4, 'soul': 4
}


def get_mood_score(track):
    """Возвращает оценку настроения от 1 (спокойный) до 9 (энергичный)"""
    genres = extract_genres_from_tags(track.tags)
    if not genres or genres == ['unknown']:
        return 5  # нейтральное

    # Берём среднее значение по всем жанрам
    scores = [GENRE_TO_MOOD.get(genre, 5) for genre in genres]
    return sum(scores) // len(scores)