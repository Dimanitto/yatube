from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        task = PostModelTest.post
        # Вообще не понял для чего эти первые 15 символов поста
        # т.к еще в модели сделали [:15]
        # посты на сайте теперь не полностью выходят (не красиво)
        expected_object_name = task.text[:15]
        self.assertEqual(expected_object_name, str(task))
