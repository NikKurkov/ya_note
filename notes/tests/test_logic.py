# notes/tests/test_logic
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()

class TestNoteCreation(TestCase):
    NOTE_TITLE = 'Заметка'
    NOTE_TEXT = 'Текст заметки'
    UNIQUE_SLUG = 'note-creation-unique'

    # Подготовка данных - заполнение фикстур
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        # Создаем пользователей.
        # Владелец заметки.
        cls.user = User.objects.create(username='Автор заметки')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Другой пользователь.
        cls.other_user = User.objects.create(username='Другой автор')
        cls.other_user_client = Client()
        cls.other_user_client.force_login(cls.other_user)

        # Данные для POST-запроса при создании заметки.
        cls.form_data = {'title': cls.NOTE_TITLE, 'text': cls.NOTE_TEXT, 'slug' : cls.UNIQUE_SLUG,}
        # Создаем заметку
        cls.note = Note.objects.create(title='Заметка', text='Текст заметки', author=cls.user, slug='initial-slug')

    # Анонимный пользователь не может создавать заметки
    def test_anonymous_user_cant_create_note(self):
        # Совершаем POST-запрос от анонимного пользователя.
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    # Зарегистрированный пользователь может создавать заметки
    def test_user_can_create_note(self):
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что редирект на страницу успешного создания заметки.
        self.assertRedirects(response, self.success_url)
        # Считаем количество заметок
        notes_count = Note.objects.count()
        # Убеждаемся, что стало 2.
        self.assertEqual(notes_count, 2)
        # Проверяем, что все атрибуты верные
        # И у последней созданной заметки правильный текст
        note = Note.objects.last()
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.author, self.user)

class TestNoteEditDelete(TestCase):
    NOTE_TITLE = 'Заметка'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'test-notez'
    NEW_NOTE_TITLE = 'Заметка 2'
    NEW_NOTE_TEXT = 'Текст заметки 2'
    NEW_NOTE_SLUG = 'test-notez2'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author,
            )
        cls.edit_url = reverse('notes:edit', args=(cls.NOTE_SLUG,))
        cls.delete_url = reverse('notes:delete', args=(cls.NOTE_SLUG,))
        cls.success_url = reverse('notes:success')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Другой пользователь')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.form_data = {'title': cls.NEW_NOTE_TITLE, 'text': cls.NEW_NOTE_TEXT, 'slug': cls.NEW_NOTE_SLUG}

    def test_author_can_delete_note(self):
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.reader_client.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NEW_NOTE_SLUG)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
