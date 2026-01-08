import os
import requests
from dotenv import load_dotenv

load_dotenv()

LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_API_URL = 'http://ws.audioscrobbler.com/2.0/'


def search_tracks(query: str, limit: int = 5):
    """Ищет треки в Last.fm по названию. Возвращает список словарей с данными трека."""
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