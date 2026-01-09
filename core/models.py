from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Event(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название мероприятия")
    description = models.TextField(blank=True, verbose_name="Описание")
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events", verbose_name="Организатор")
    access_code = models.CharField(max_length=12, unique=True, verbose_name="Код доступа")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Создано")
    ends_at = models.DateTimeField(verbose_name="Окончание голосования")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    max_genre_percent = models.PositiveSmallIntegerField(
        default=50,
        help_text="Максимальный процент треков одного жанра (от 1 до 100)",
        verbose_name="Макс. доля жанра (%)"
    )
    MOOD_CHOICES = [
        ('energetic_to_calm', 'Энергичный → Спокойный'),
        ('calm_to_energetic', 'Спокойный → Энергичный'),
        ('mixed', 'Смешанная'),
    ]
    mood_sequence = models.CharField(
        max_length=20,
        choices=MOOD_CHOICES,
        default='energetic_to_calm',
        verbose_name="Последовательность настроения"
    )

    def __str__(self):
        return f"{self.title} (код: {self.access_code})"

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"


class Track(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название трека")
    artist = models.CharField(max_length=200, verbose_name="Исполнитель")
    lastfm_id = models.CharField(max_length=100, unique=True, verbose_name="Last.fm ID")
    duration = models.PositiveIntegerField(null=True, blank=True, verbose_name="Длительность (сек)")
    tags = models.TextField(blank=True, verbose_name="Теги/жанры (через запятую)")

    def __str__(self):
        return f"{self.artist} — {self.title}"

    class Meta:
        verbose_name = "Трек"
        verbose_name_plural = "Треки"


class TrackSuggestion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="suggestions", verbose_name="Мероприятие")
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="suggestions", verbose_name="Трек")
    suggested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Предложил")
    votes_score = models.IntegerField(default=0, verbose_name="Рейтинг голосов")
    suggested_at = models.DateTimeField(default=timezone.now, verbose_name="Дата предложения")

    class Meta:
        unique_together = ('event', 'track')
        verbose_name = "Предложение трека"
        verbose_name_plural = "Предложения треков"

    def __str__(self):
        return f"{self.track} → {self.event}"