from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()


class TaskCreateFormTests(TestCase):
    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_new_user(self):
        """Валидная форма создает нового пользователя"""
        # возьмем кол-во пользователей (оно равно нулю)
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Test',
            'last_name': 'Testirovich',
            'username': 'F4ntazer',
            'email': 'test@yandex.ru',
            'password1': 'QWErty7349',
            'password2': 'QWErty7349'
        }
        # Отправляем POST-запрос
        self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        # Проверяем, увеличилось ли число пользователей
        self.assertEqual(User.objects.count(), users_count + 1)
