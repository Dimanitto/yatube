import shutil
import tempfile
from django.core.cache import cache
from http import HTTPStatus
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Group, Post, Comment, Follow
from django import forms


User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='tester')
        # Создадим запись в БД
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок, файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        self.authorized_client.force_login(self.post.author)
        # Собираем в словарь пары "reverse(name): имя_html_шаблона"
        templates_pages_names = {
            reverse('posts:index'):
            'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'tester'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': 1}):
            'posts/create_post.html',
            reverse('posts:post_create'):
            'posts/create_post.html',
        }
        # Проверяем, что при обращении к name вызывается
        # соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверяем, что словарь context страницы index
    # содержит ожидаемые значения
    def test_index_detail_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:index')))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        # Проверим все объекты контекста
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.text, 'Тестовая пост')
        self.assertEqual(first_object.image, 'posts/small.gif')

    def test_group_list_detail_pages_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(reverse('posts:group_posts',
                                kwargs={'slug': 'test-slug'}))
                    )
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым отфильтрованным
        first_object = response.context['group']
        second_object = response.context['page_obj'][0]
        task_group_0 = first_object.title
        self.assertEqual(task_group_0, 'Тестовая группа')
        self.assertEqual(second_object.image, 'posts/small.gif')

    def test_profile_detail_show_correct_context(self):
        """Шаблон profile отфильтрован по пользователю"""
        response = (self.authorized_client.
                    get(reverse('posts:profile',
                                kwargs={'username': 'tester'}))
                    )
        first_object = response.context['client']
        second_object = response.context['page_obj'][0]
        task_client_0 = first_object.username
        task_post_0 = second_object.text
        # Проверим пост и пользователя
        self.assertEqual(task_client_0, 'tester')
        self.assertEqual(task_post_0, 'Тестовая пост')
        self.assertEqual(second_object.image, 'posts/small.gif')

    def test_post_detail_show_correct_context(self):
        """Шаблон post detail отфильтрован по id"""
        response = (self.authorized_client.
                    get(reverse('posts:post_detail',
                                kwargs={'post_id': 1}))
                    )
        first_object = response.context['count']
        second_object = response.context['post']
        task_count_0 = first_object
        task_post_0 = second_object.text
        # Проверим что пост один
        self.assertEqual(task_count_0, 1)
        self.assertEqual(task_post_0, 'Тестовая пост')
        self.assertEqual(second_object.image, 'posts/small.gif')

    def test_edit_post_show_correct_context(self):
        """Шаблон create post форма редактирования поста"""
        # Снова нужно авторизироваться под автором поста (tester),
        # без этого мы не сможем редактировать пост от имени (auth)
        self.authorized_client.force_login(self.post.author)
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                                kwargs={'post_id': 1}))
                    )
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон create post форма создания поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_additional_verification_create(self):
        """Проверка пост не попал в другую группу"""
        # Создадим группу с постом различную чтобы сравнить
        group = Group.objects.create(
            title='Заголовок для 2 тестовой группы',
            slug='test_slug2'
        )
        Post.objects.create(
            author=self.user,
            text='Test post 2',
            group=group,
        )
        # Т.к мы создали второй пост с другой группой
        # проверим что на странице группы этот пост один
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': group.slug}))
        count = response.context["page_obj"].object_list
        # Теперь всего постов 2, и только один должен быть
        # на странице группы
        self.assertEqual(len(count), Post.objects.count() - 1)
        self.assertEqual(response.status_code, 200)

    def test_comment_succesful(self):
        """Комментарий появляется на странице поста"""
        Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Test comment'
        )
        response = (self.authorized_client.
                    get(reverse('posts:post_detail',
                                kwargs={'post_id': 1}))
                    )
        first_object = response.context['comments']
        # Из-за QuerySet пришлось добавить .get()
        # Без нее была бы ошибка, как ниже
        # <QuerySet [<Comment: Test comment>]> != 'Test comment'
        self.assertEqual(first_object.get().text, 'Test comment')
        # Проверим и автора
        self.assertEqual(first_object.get().author, self.user)
        # Проверим и пост относящийся к комментарию
        self.assertEqual(first_object.get().post.text, self.post.text)

    def test_cache(self):
        """Проверка кеширования главной страницы"""
        # Логика теста: при удалении записи из базы, она остаётся
        # в response.content главной страницы до тех пор,
        # пока кэш не будет очищен принудительно.
        response = self.authorized_client.get(reverse('posts:index'))
        count_before_del = Post.objects.count()
        instance = Post.objects.get(text='Тестовая пост')
        # Удалим едиственный пост
        instance.delete()
        first_obj = response.content
        # Удалим принудительно кеш, не ждать же нам 20 секунд)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        second_obj = response.content
        count_after_del = Post.objects.count()
        # Проверим что content до удаления и после кеширования разный
        self.assertNotEqual(first_obj, second_obj)
        # Кол-во постов = 0
        self.assertEqual(count_after_del, count_before_del - 1)

    def test_new_post_in_feed_who_followed(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан"""
        # Подпишемся на tester'a у него 1 пост
        Follow.objects.create(
            user=self.user,
            author=self.post.author
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        # Проверим пост и пользователя что он есть в ленте
        self.assertEqual(first_object.author.username, 'tester')
        self.assertEqual(first_object.text, 'Тестовая пост')
        self.assertEqual(first_object.image, 'posts/small.gif')

    def test_new_post_not_appear_in_feed_who_unfollowed(self):
        """Новая запись пользователя не появляется в ленте тех, кто
        не подписан на него"""
        # Создадим второго авторизованного не подписанного на автора
        self.user = User.objects.create_user(username='auth_without')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        # Т.к он ни на кого не подписан в ленте у него 0 постов
        # QuerySet будет пустым без единого объекта
        # object_list он вернет список для того чтобы подсчитать кол-во
        second_object = response.context['page_obj']
        self.assertEqual(second_object.object_list.count(), 0)

    def test_auth_user_can_follow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей"""
        count = Follow.objects.count()
        # Создадим подписку
        Follow.objects.create(
            user=self.user,
            author=self.post.author
        )
        url = f'/profile/{self.user}/follow/'
        # Проверим поочереди для авторизованного и для гостя
        response = self.authorized_client.get(url)
        # Т.к там идет редирект сразу код проверки 302
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Проверим что кол-во подписок увеличилось
        self.assertEqual(Follow.objects.count(), count + 1)
        # Все поля соотвествуют
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.post.author
            ).exists()
        )
        self.guest_client = Client()
        response = self.guest_client.get(url)
        # Проверим что не авторизованный пользователь перейдет
        # на страницу входа
        self.assertEqual(response.url, f'/auth/login/?next={url}')

    def test_auth_user_can_unfollow(self):
        """Авторизованный пользователь может удалять подписки"""
        # Создадим подписку
        Follow.objects.create(
            user=self.user,
            author=self.post.author
        )
        count = Follow.objects.count()
        # Удалим подписку
        Follow.objects.filter(
            user=self.user,
            author=self.post.author
        ).delete()
        self.assertEqual(Follow.objects.count(), count - 1)
        url = f'/profile/{self.user}/unfollow/'
        # Проверим поочереди для авторизованного и для гостя
        response = self.authorized_client.get(url)
        # Т.к там идет редирект сразу код проверки 302
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.guest_client = Client()
        response = self.guest_client.get(url)
        # Проверим что не авторизованный пользователь перейдет
        # на страницу входа
        self.assertEqual(response.url, f'/auth/login/?next={url}')


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='tester')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        # Создадим 13 записей в БД
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовая пост {i}',
                # Привяжем созданную выше группу к посту
                group=cls.group,
            )

    def setUp(self):
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        urls = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'tester'}),
        )
        for url in urls:
            response = self.authorized_client.get(url)
            # Проверка: количество постов на первой странице равно 10.
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        urls = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'tester'}),
        )
        for url in urls:
            response = self.authorized_client.get(url + '?page=3')
            self.assertEqual(len(response.context['page_obj']), 3)
