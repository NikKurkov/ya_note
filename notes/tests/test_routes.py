# notes/tests/test_routes.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Импортируем класс модели заметок.
from notes.models import Note


# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаем пользователей
        cls.author = User.objects.create(username='Автор Заметки')
        cls.not_author = User.objects.create(username='Мимо Крокодил')
        # Создаем новую заметку с авторством author
        cls.notes = Note.objects.create(title='Заголовок', text='Текст', slug='test_note', author=cls.author)

    def test_pages_availability(self):
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_notes(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.not_author, HTTPStatus.NOT_FOUND),
        )
        # Проверяем доступности списка заметок для авторизированного пользователя
        with self.subTest(user=self.author, name='notes:list'):
            url = reverse('notes:list')
            self.client.force_login(self.author)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

        # Проверка остальных страниц
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.notes.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        # Сохраняем адрес логина:
        login_url = reverse('users:login')
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name in ('notes:list', 'notes:edit', 'notes:detail', 'notes:delete'):
            with self.subTest(name=name):
                # Получаем адрес страницы
                if name == 'notes:list':
                    # Для списка заметок не нужны аргументы
                    url = reverse(name)
                else:
                    # Для остальных страниц передаем slug заметки
                    url = reverse(name, args=(self.notes.slug,))
                # Получаем ожидаемый адрес редиректа
                redirect_url = f'{login_url}?next={url}'
                # Запрашиваем
                response = self.client.get(url)
                # Проверяем
                self.assertRedirects(response, redirect_url)