# core/forms.py
from django import forms
from .models import Event
import random
import string

def generate_access_code():
    """Генерирует уникальный 6-символьный код"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'max_genre_percent']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название мероприятия'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Описание (необязательно)'}),
            'max_genre_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': 10, 'max': 100, 'value': 30}),
        }
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'max_genre_percent': 'Макс. доля одного жанра (%)',
        }

    def save(self, commit=True):
        event = super().save(commit=False)
        if not event.access_code:
            # Генерируем уникальный код
            while True:
                code = generate_access_code()
                if not Event.objects.filter(access_code=code).exists():
                    event.access_code = code
                    break
        if commit:
            event.save()
        return event