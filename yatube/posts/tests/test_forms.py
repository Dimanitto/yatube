import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.contrib.auth import get_user_model
from ..forms import PostForm
from ..models import Group, Post
from django.test import Client, TestCase, override_settings
from django.urls import reverse


User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных для проверки сушествующего slug
        Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='first'
        )
        # Создаем форму, если нужна проверка атрибутов
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок, файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_task(self):
        """Валидная форма создает запись в Post"""
        # Подсчитаем количество записей в Task
        posts_count = Post.objects.count()
        form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Тестовый текст',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект после создания поста
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным слагом
        # и проверим что автор тот же
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                author=self.user,
            ).exists()
        )

    def test_edit_post(self):
        """При редактировании поста происходит
        изменение поста с post_id в БД"""
        # Для начала пришлось создать пост
        # чтобы в последуюущем его отредактировать
        form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Тестовый текст',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        count = Post.objects.count()
        # Измененные данные
        form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Измененный текст',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=('1')),
            data=form_data,
            follow=True
        )
        # Проверка изменился ли пост
        self.assertTrue(
            Post.objects.filter(
                text='Измененный текст',
                author=self.user,
            ).exists()
        )
        # Проверим и группу
        self.assertTrue(
            Group.objects.filter(
                title='Тестовый заголовок',
            ).exists()
        )
        # Проверим что кол-во постов не изменилось
        # после редактирования
        self.assertEqual(count, Post.objects.count())
        # После редактирования редирект
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )

    def test_create_task_with_image(self):
        """При отправке поста с картинкой создается запись в БД"""
        # Подсчитаем количество записей в Task
        tasks_count = Post.objects.count()
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
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
        form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект после создания поста
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        # Проверяем, что создалась запись с заданным слагом
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text='Тестовый текст',
                image='posts/small.gif'
            ).exists()
        )


class PostFormTests(TestCase):
    """Т.к у меня labels и help_texts были определены
    в формах - следует проверить """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()

    def test_text_group_label(self):
        """Проверим labels формы"""
        text_label = PostFormTests.form.fields['text'].label
        group_label = PostFormTests.form.fields['group'].label
        self.assertEqual(text_label, 'Текст поста')
        self.assertEqual(group_label, 'Группа')

    def test_text_group_help_text(self):
        """Проверим help_text формы"""
        text_help_text = PostFormTests.form.fields['text'].help_text
        group_help_text = PostFormTests.form.fields['group'].help_text
        self.assertEqual(text_help_text, 'Текст нового поста')
        self.assertEqual(
            group_help_text,
            'Группа, к которой будет относиться пост'
        )
