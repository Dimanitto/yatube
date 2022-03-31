from django.test import TestCase, Client
from http import HTTPStatus
from django.contrib.auth import get_user_model


User = get_user_model()


class TaskURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_url_about_tech(self):
        """Доступность страниц о авторе и технологии для всех"""
        urls = (
            '/about/author/',
            '/about/tech/'
        )
        for adress in urls:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)
