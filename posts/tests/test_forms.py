from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post


User = get_user_model()


class PostFormTests(TestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='kurt')
        cls.group_rock = Group.objects.create(
            title='Rock',
            slug='rock',
            description='Все о роке'
        )
        cls.group_rap = Group.objects.create(
            title='Rap',
            slug='rap',
            description='Все о рэпе'
        )
        cls.form_data = {
            'text': 'Курт Кобейн жив',
            'group': '1'
        }
        cls.post = Post.objects.create(
            text = (
                'Добавляем пост для редактирования'
            ),
            author = cls.user,
            group = cls.group_rock,
        )
        cls.group_id = Group.objects.first().id
        cls.post_id = cls.user.posts.first().id
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_forms_labels(self):
        """Проверяем labels формы PostForm."""
        field_labels = {
            'text': 'Текст',
            'group': 'Группа',
        }
        for value, expected in field_labels.items():
            with self.subTest(value=value):
                self.assertEqual(
                    PostFormTests.form.fields[value].label, expected)

    def test_forms_help_text(self):
        """Проверяем help_texts формы PostForm."""
        field_help_texts = {
            'text': 'Добавьте текст для новой записи',
            'group': 'Выберите группу или оставьте ее пустой',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    PostFormTests.form.fields[value].help_text, expected)
    
    def test_create_new_post(self):
        """Валидная форма на странице /new/ создает запись в Posts 
        и редиректит на главную страницу.
        """
        posts = Post.objects.all()
        expected_posts_count = posts.count() + 1
        expected_group_rock_count = self.group_rock.posts.count() + 1
        expected_group_rap_count = self.group_rap.posts.count()
        with self.subTest():
            response = self.authorized_client.post(
                reverse('new_post'),
                data=self.form_data,
                follow=True,
            )
            # Проверяем общее кол-во постов
            self.assertEqual(
                Post.objects.count(), expected_posts_count
            )
            # Проверяем сработал ли редирект на главную страницу
            self.assertRedirects(
                response, reverse('index')
            )
            # Проверяем число постов с группой "Rock"
            self.assertEqual(
                Post.objects.filter(group__title=self.group_rock).count(), 
                expected_group_rock_count
            )
            # Проверяем не попал ли новый пост в другую группу "Rap"
            self.assertEqual(
                Post.objects.filter(group__title=self.group_rap).count(), 
                expected_group_rap_count
            )

    def test_edit_post(self):
        """Валидная форма на /username/post_id/edit/ изменяет запись в Posts 
        и редиректит на страницу просмотра поста.
        """
        form_new_data = {
            'text': 'Курт Кобейн жив',
            'group': self.group_id
        }
        post_text_before_edit = self.post.text
        with self.subTest():
            response = self.authorized_client.post(
                reverse('post_edit', 
                    kwargs={'username': self.user, 'post_id': self.post_id}),
                data=form_new_data,
                follow=True,
            )
            # Проверяем изменился ли текст поста в БД
            self.assertNotEqual(
                Post.objects.first(), post_text_before_edit
            )
            # Проверяем сработал ли редирект на главную страницу
            self.assertRedirects(
                response, reverse('post_view', 
                    kwargs={'username': self.user, 'post_id': self.post_id}
            ))

    def test_form_error_new_post(self):
        """Проверим, что форма нового поста 
        вернула ошибку с ожидаемым текстом.
        """
        form_data_empty = {
            'text': '',
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data_empty,
            follow=True
        )
        self.assertFormError(
            response, 'form', 'text', 'Обязательное поле.'
        )
