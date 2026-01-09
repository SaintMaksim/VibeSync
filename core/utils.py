import os
import requests
import pandas as pd
from dotenv import load_dotenv

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

def balance_playlist(suggestions, max_genre_percent):
    """
    Формирует сбалансированный плейлист.
    suggestions: QuerySet[TrackSuggestion]
    max_genre_percent: int (например, 30)
    Возвращает: список отфильтрованных TrackSuggestion, отсортированных по votes_score
    """
    if not suggestions:
        return []

    data = []
    for s in suggestions:
        genres = parse_genres_from_tags(s.track.tags)
        if not genres:
            genres = ['unknown']
        for genre in genres:
            data.append({
                'suggestion_id': s.id,
                'track_title': s.track.title,
                'track_artist': s.track.artist,
                'genre': genre,
                'votes_score': s.votes_score,
            })

    df = pd.DataFrame(data)
    total_tracks = len(suggestions)
    max_genre_count = int(total_tracks * max_genre_percent / 100)
    genre_counts = df['genre'].value_counts()
    allowed_genres = genre_counts[genre_counts <= max_genre_count].index

    filtered_df = df[df['genre'].isin(allowed_genres)]
    final_suggestions = filtered_df.drop_duplicates(subset=['suggestion_id'])
    final_suggestions = final_suggestions.sort_values('votes_score', ascending=False)
    return final_suggestions['suggestion_id'].tolist()

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

def parse_genres_from_tags(tags_str):
    """Преобразует строку тегов в список жанров"""
    if not tags_str:
        return []
    genres = [g.strip().lower() for g in tags_str.split(',') if g.strip()]
    return list(dict.fromkeys(genres))
