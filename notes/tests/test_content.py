# notes/tests/test_content.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from datetime import datetime, timedelta

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()

class TestContent(TestCase):
    HOME_URL = reverse('notes:list');

    @classmethod
    def setUpTestData(cls):
        # Создаем пользователей
        cls.author = User.objects.create(username='Автор Заметки')
        cls.not_author = User.objects.create(username='Мимо Крокодил')
        # Вычисляем текущую дату.
        today = datetime.today()
        all_notes = [
            Note(
            title=f'Заметка {index}',
            text='Текст заметки.',
            slug=f'test_note_{index}',
            author=cls.author
            )
            for index in range(10)
        ]
        Note.objects.bulk_create(all_notes)

    # Заметки создаются в нужном количестве
    def test_notes_count(self):
        self.client.force_login(self.author)
        response = self.client.get(self.HOME_URL)
        self.assertEqual(response.status_code, 200)
        qs = response.context['object_list']
        self.assertEqual(qs.count(), 10)

    # Видны только свои заметки
    def test_only_own_notes_in_list(self):
        Note.objects.create(title='Чужая заметка', text='Текст заметки', slug='other_test_note', author=self.not_author)
        self.client.force_login(self.author)
        qs = self.client.get(reverse('notes:list')).context['object_list']
        slugs = {n.slug for n in qs}
        self.assertNotIn('other_test_note', slugs)

    # Detail-view: правильный контекст и статус
    def test_detail_view_content(self):
        note = Note.objects.first()
        self.client.force_login(self.author)
        resp = self.client.get(reverse('notes:detail', args=(note.slug,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['object'], note)
        self.assertContains(resp, note.title)

    # Если заметка не принадлежит автору — 404
    def test_detail_404_for_other_user(self):
        note = Note.objects.create(title='X', text='X', slug='x2', author=self.author)
        self.client.force_login(self.not_author)
        resp = self.client.get(reverse('notes:detail', args=(note.slug,)))
        self.assertEqual(resp.status_code, 404)
