#posts/tests/test_views.py
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Follow, Post, Group

User = get_user_model()


class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='John',
        )
        cls.author_paul = User.objects.create_user(
            username='Paul',
        )
        cls.author_mike = User.objects.create_user(
            username='Mike',
        )
        cls.group = Group.objects.create(
            title='Музыканты',
            slug='music',
            description='Популярные музыканты'
        )
        cls.post_paul = Post.objects.create(
            text = (
                'Followers'
            ),
            author = cls.author_paul,
            group = cls.group,
        )
        cls.post = Post.objects.create(
            text = (
                'Проверяем работу view-функций'
            ),
            author = cls.user,
            group = cls.group,
        )
        cls.post_id = cls.user.posts.first().id
        cls.site = Site.objects.create(
            domain='127.0.0.1:8000'
        )
        cls.flat_about_author = FlatPage.objects.create(
            title='Об авторе',
            url=reverse('about-author'),
            content='Об авторе'
        )
        cls.flat_about_spec = FlatPage.objects.create(
            title='О техно',
            url=reverse('about-spec'),
            content='О техно'
        )
        site = Site.objects.get(pk=1)
        cls.flat_about_author.sites.add(site)
        cls.flat_about_spec.sites.add(site)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html': reverse('group_posts', 
                kwargs={'slug': self.group.slug}  
        )}
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template) 
  
    def test_homepage_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(
            response.context.get('page')[0].text, 
            self.post.text
        )
        self.assertEqual(
            response.context.get('paginator').object_list.count(), 
            Post.objects.count()
        )

    def test_posts_group_pages_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
                reverse('group_posts', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(
            response.context.get('page')[0].text, 
            self.post.text
        )
        self.assertEqual(
            response.context.get('page')[0].group.title, 
            self.post.group.title
        )

    def test_new_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }        
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
    
    def test_post_view_show_correct_context(self):
        """Шаблон post_view сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post_view', 
                kwargs={'username': self.user, 'post_id': self.post_id
        }))
        self.assertEqual(
            response.context.get('post').author, 
            self.post.author
        )
        self.assertEqual(
            response.context.get('post').text, 
            self.post.text
        )
        self.assertEqual(
            response.context.get('posts').count(), 
            Post.objects.filter(author__username=self.user).count()
        )

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.user}))
        self.assertEqual(
            response.context.get('page')[0].text, 
            self.post.text
        )
        self.assertEqual(
            response.context.get('author'), 
            self.post.author
        )
        self.assertEqual(
            response.context.get('paginator').object_list.count(), 
            Post.objects.filter(author__username=self.user).count()
        )

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post_edit', 
                kwargs={'username': self.user, 'post_id': self.post_id
        }))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(
            response.context.get('post').text, 
            self.post.text
        )

    def test_flatpages_show_correct_context(self):
        """Шаблон about_author сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('about-author')) 
        self.assertEqual(
            response.context.get('flatpage').title, 
            self.flat_about_author.title
        )
        self.assertEqual(
            response.context.get('flatpage').url, 
            self.flat_about_author.url
        )
        self.assertEqual(
            response.context.get('flatpage').content, 
            self.flat_about_author.content
        )
    
    def test_server_return_404_when_page_not_found(self):
        """Сервер возвращает код 404, если страница не найдена."""
        wrong_username = 'alex'
        response = self.guest_client.get(
            reverse('profile', kwargs={'username': wrong_username}))
        self.assertEqual(response.status_code, 404)

    def test_authorized_client_can_follow_author(self):
        '''Проверка подписки на автора для авторизованного пользователя.'''
        unfollow = Follow.objects.filter(
            author__username=self.author_paul
            ).count()
        # Авторизованный User <John> подписался на author <Paul>
        self.authorized_client.get(
            reverse('profile_follow',
            kwargs = {'username': self.author_paul}
        ))
        # Проверка подписки
        follow = Follow.objects.filter(
            author__username=self.author_paul
            ).count()
        self.assertEqual(follow, unfollow + 1)

    def test_follow_index_show_correct_context_authorized_user(self):
        '''Шаблон follow_index сформирован с правильным контекстом.'''
        # Авторизованный User <John> подписался на author <Paul>
        self.authorized_client.get(
            reverse('profile_follow',
            kwargs = {'username': self.author_paul}
        ))
         # Проверка контекста /follow/ для John
        response = self.authorized_client.get(
            reverse('follow_index')
        )
        self.assertEqual(
            response.context.get('page')[0].text, 
            self.post_paul.text
        )

    def test_authorized_client_can_unfollow_author(self):
        '''Проверка отписки от автора для авторизованного пользователя.'''
        # Авторизованный User <John> подписался на author <Paul>
        self.authorized_client.get(
            reverse('profile_follow',
            kwargs = {'username': self.author_paul}
        ))
        follow = Follow.objects.filter(
            author__username=self.author_paul
            ).count()
        # Проверка подписки
        self.authorized_client.get(
            reverse('profile_unfollow',
            kwargs = {'username': self.author_paul}
        ))
        unfollow = Follow.objects.filter(
            author__username=self.author_paul
            ).count()
        self.assertEqual(unfollow, follow - 1)

    def test_follow_index_show_correct_context_non_follow_author(self):
        '''Новая запись пользователя не появляется в ленте тех, 
        кто не подписан на него.'''
        # Авторизованный User <John> подписался на author <Paul>
        self.authorized_client.get(
            reverse('profile_follow',
            kwargs = {'username': self.author_paul}
        ))
        # Проверка контектса /follow/ для <Mike>, должен быть пустой
        self.authorized_client_mike = Client()
        self.authorized_client_mike.force_login(self.author_mike)
        response_mike = self.authorized_client_mike.get(
            reverse('follow_index')
        )
        with self.assertRaises(IndexError):
            response_mike.context['page'][0].text
