import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'

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
    """Ищет треки в Last.fm по названию. Возвращает список словарей с данными трека"""
    if not LASTFM_API_KEY:
        print("Ошибка: LASTFM_API_KEY не задан в .env")
        return []

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
        #Last.fm может вернуть один объект вместо списка, если найден 1 трек
        if isinstance(track_list, dict):
            track_list = [track_list]

        for item in track_list:
            #Извлекаем теги
            tags = []
            toptags = item.get('toptags', {})
            if isinstance(toptags, dict):
                tag_data = toptags.get('tag', [])
                if isinstance(tag_data, list):
                    tags = [tag.get('name', '') for tag in tag_data if tag.get('name')]
                elif isinstance(tag_data, dict):
                    tags = [tag_data.get('name', '')] if tag_data.get('name') else []

            tracks.append({
                'title': item.get('name', '').strip(),
                'artist': item.get('artist', '').strip(),
                'lastfm_id': f"{item.get('artist', '').strip()} - {item.get('name', '').strip()}",
                'duration': None,
                'tags': ', '.join(tags[:5]),
            })
        return tracks

    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Last.fm API error: {e}")
        return []

def parse_genres_from_tags(tags_str):
    """Преобразует строку тегов в список жанров"""
    if not tags_str:
        return []
    genres = [g.strip().lower() for g in tags_str.split(',') if g.strip()]
    return list(dict.fromkeys(genres))
