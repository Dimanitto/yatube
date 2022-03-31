from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Group, Post
from http import HTTPStatus


User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.urls = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
        }
        cls.private_urls = {
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_all_urls_for_auth_user(self):
        """Аутентифицированному пользователю доступны все страницы"""
        # Залогинемся под автором поста
        self.authorized_client.force_login(self.post.author)
        # Сложим два словаря адрессов
        all_urls = {**self.urls, **self.private_urls}
        for adress in all_urls:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_home_group_profile_post(self):
        """Доступность страниц для всех"""
        for adress in self.urls:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_edit(self):
        """Доступность редактировать пост автору"""
        # Пришлось авторизироваться под пользователем auth, т.к
        # без него проверка шла через HasNoName, который не является
        # автором, т.к у него нету поста
        self.authorized_client.force_login(self.post.author)
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_create(self):
        """Доступность создать пост авторизированному клиенту"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблон по адресам
        for adress, template in self.urls.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
        # Сложим все адресса и шаблоны чтобы проверить доступ
        # аутентифицированному пользователю
        # (должны быть доступны все страницы)
        all_urls = {**self.urls, **self.private_urls}
        # Т.к проверка идет от авторизованного пользователя
        # не имеющего поста, будет код 302 т.е редирект
        # значит нам нужно залогинется под автором auth снова
        self.authorized_client.force_login(self.post.author)
        for adress, template in all_urls.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

        def test_page_404(self):
            """Запрос к несуществующей странице вернет ошибку 404"""
            response = self.guest_client.get('/unexisting_page/')
            # Страница 404 отдает кастомный шаблон
            self.assertTemplateUsed(response, 'core/404.html')
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_anonimous_redirect(self):
        """У анонимного пользователя при
        создании/редактировании происходит редирект"""
        urls = (
            f'/posts/{self.post.pk}/edit/',
            '/create/'
        )
        for adress in urls:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_auth_user_non_author_redirect(self):
        """У авторизованного пользователя (не автора поста)
        происходит редирект"""
        url = f'/posts/{self.post.pk}/edit/'
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_create_comment(self):
        """Доступность создать комментарий только
        авторизированному клиенту"""
        url = f'/posts/{self.post.pk}/comment/'
        response = self.authorized_client.get(url)
        # Т.к там идет редирект сразу код проверки 302
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Проверим что не авторизованный пользователь перейдет
        # на страницу входа
        response = self.guest_client.get(url)
        self.assertEqual(response.url, f'/auth/login/?next={url}')
