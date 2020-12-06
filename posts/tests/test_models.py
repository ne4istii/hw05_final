# posts/tests/tests_models.py
from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post, Group

User = get_user_model()


class GroupModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='друзья',
            slug='friends',
            description='посты о друзьях'
        )

    def test_verbose_name(self):
        group = GroupModelTest.group
        field_verboses = {
            'title': 'Группа',
            'slug': 'Ссылка',
            'description': 'Описание',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        group = GroupModelTest.group
        field_help_texts = {
            'title': 'Дайте короткое название группе',
            'slug': (
                'Укажите название ссылки для группы. Используйте '
                'только латиницу, цифры, дефисы и знаки '
                'подчёркивания'
            ),
            'description': 'Дайте подробное описание группе',

        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected)
    
    def test_object_name_is_title_field(self):
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEquals(expected_object_name, str(group))


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='john',
            email='jlennon@beatles.com',
            password='john'
        )
        cls.group = Group.objects.create(
            title='Музыканты',
            slug='music',
            description='Популярные музыканты'
        )
        cls.post = Post.objects.create(
            text = (
                'Пробуем тестировать соответствие полей verbose '
                'и help_text в модели Post'
            ),
            author = cls.user,
            group = cls.group,
        )

    def test_model_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Пост',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_model_help_text(self):
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Напишите текст к посту',
            'author': 'Выберите автора поста',
            'group': 'Назначьте группу для поста',

        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_model_object_name_is_text_field(self):
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEquals(expected_object_name, str(post))
