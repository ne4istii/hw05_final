# # posts/tests/tests_url.py
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

import shutil
import tempfile
from time import sleep

from posts.models import Post, Group


User = get_user_model()


class StaticURLTests(TestCase):
    
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        response = self.guest_client.get(reverse('about-author'))  
        self.assertEqual(response.status_code, 404)  
    
    def test_technologies(self):
        response = self.guest_client.get(reverse('about-spec'))  
        self.assertEqual(response.status_code, 404) 


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.author_john = User.objects.create_user(
            username='John',
            email='jlennon@beatles.com',
        )
        cls.author_paul = User.objects.create_user(
            username='Paul',
            email='paul@beatles.com',
            password='paul'
        )
        cls.group = Group.objects.create(
            title='Музыканты',
            slug='music',
            description='Популярные музыканты'
        )
        cls.group_id = Group.objects.first().id
        cls.post_john = Post.objects.create(
            text = (
                'Пробуем тестировать доступность страницы для John.'
            ),
            author = cls.author_john,
            group = cls.group,
        )
        cls.post_paul = Post.objects.create(
            text = (
                'Пробуем тестировать доступность страниц для Paul.'
            ),
            author = cls.author_paul,
            group = cls.group,
        )
        cls.post_john_id = cls.author_john.posts.first().id
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()
    
    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client_john = Client()
        self.authorized_client_paul = Client()
        self.authorized_client_john.force_login(self.author_john)
        self.authorized_client_paul.force_login(self.author_paul)
        self.templates_url_names = {
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html': reverse('group_posts',
                kwargs = {
                    'slug': self.group.slug
            }),
            'profile.html': reverse('profile', 
                kwargs = {
                    'username': self.author_john
            }),
            'post.html': reverse('post_view',
                kwargs = {
                    'username': self.author_john, 
                    'post_id': self.post_john_id
            }), 
        }
        self.template_post_edit_comment = {
            'new.html': reverse('post_edit',
            kwargs = {
                    'username': self.author_john, 
                    'post_id': self.post_john_id
            }),
            'comments.html': reverse('add_comment',
            kwargs = {
                    'username': self.author_john, 
                    'post_id': self.post_john_id
        })
        }   

    def test_urls_uses_correct_template(self):
        """URL-адреса из словаря templates_url_names используют
        соответствующий шаблон."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client_john.get(reverse_name)
                self.assertTemplateUsed(response, template) 

    def test_post_edit_uses_correct_template(self):
        """URL-адрес /username/post_id/edit и /username/post_id/comment 
        использует соответствующий шаблон."""
        for template, reverse_name in self.template_post_edit_comment.items():
            response = self.authorized_client_john.get(reverse_name)
            self.assertTemplateUsed(response, template)

    def test_urls_availability_anonymous_or_redirect_login_page(self):
        """URL-адреса из словаря templates_url_names доступны или
        редиректится на страницу логина для /new/."""
        new_post_url = reverse('new_post')
        login_url = reverse('login')
        redirect_url = f'{login_url}?next={new_post_url}'
        for reverse_name in self.templates_url_names.values():
            with self.subTest():
                response = self.guest_client.get(reverse_name, follow=True)
                if response.status_code == 200:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertRedirects(response, redirect_url)

    def test_post_edit_and_comment_availability_anonymous(self):
        """URL-адрес /username/post_id/edit и /username/post_id/comment  
        для анонимного пользователя редиректится на страницу логина."""
        for reverse_name in self.template_post_edit_comment.values():
            with self.subTest():
                response = self.guest_client.get(reverse_name, follow=True)
                login_url = reverse('login')
                redirect_url = f'{login_url}?next={reverse_name}'
                self.assertRedirects(response, redirect_url)

    def test_post_edit_availability_authorized_author(self):
        """URL-адрес /username/post_id/edit доступен для автора поста."""
        response = self.authorized_client_john.get(
            reverse('post_edit', 
                kwargs={
                    'username': self.author_john, 
                    'post_id': self.post_john_id
        }))
        self.assertEqual(response.status_code, 200)
        
    def test_post_edit_availability_authorized_not_author(self):
        """URL-адрес /username/post_id/edit редиректится 
        для не автора поста."""
        response = self.authorized_client_paul.get(
            reverse('post_edit', 
                kwargs={
                    'username': self.author_john, 
                    'post_id': self.post_john_id
        }))
        self.assertRedirects(response, 
            reverse('post_view', 
                kwargs={
                    'username': self.author_john, 
                    'post_id': self.post_john_id
        }))

    def test_appearance_img_tag_and_show_error_when_upload_nonimage(self):
        '''Пост с картинкой отображается корректно, с тегом <img>.'''
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image = SimpleUploadedFile(
            name='image.gif',
            content=image, 
        )
        form_data_image = {
            'author': self.author_john, 
            'text': 'Text with image',
            'group': self.group_id,
            'image': image
        }
        self.authorized_client_john.post(
                reverse('post_edit', 
                kwargs={
                    'username': self.author_john, 
                    'post_id': self.post_john_id
                }),
                form_data_image
        )
        urls_with_image = {
            'index.html': reverse('index'),
            'group.html': reverse('group_posts',
                kwargs={
                    'slug': self.group.slug
            }),
            'profile.html': reverse('profile', 
                kwargs={
                    'username': self.author_john
            }),
            'post.html': reverse('post_view',
                kwargs={
                    'username': self.author_john, 
                    'post_id': self.post_john_id
            }), 
        }
        # Проверим наличие тега <img> на страницах из словаря urls_with_image.
        for value in urls_with_image.values():
            with self.subTest(value=value):
                self.assertContains(
                    self.authorized_client_john.get(value), 
                    '<img'
                )

    def test_show_error_when_upload_nonimage(self):
        '''Проверим загрузку в форму /post_edit/ не image-файла.'''
        file = (
            b'123xxyz'
        )
        file = SimpleUploadedFile(
            name='file.pdf',
            content=file
        )
        form_data_file = {
            'author': self.author_john, 
            'text': 'Text with file',
            'group': self.group_id,
            'image': file
        }
        response = self.authorized_client_john.post(
                reverse('post_edit', 
                kwargs={
                    'username': self.author_john, 
                    'post_id': self.post_john_id
                }),
                form_data_file
        )
        self.assertFormError(response, 
            'form', 
            'image', 
            'Загрузите правильное изображение. '
            'Файл, который вы загрузили, поврежден '
            'или не является изображением.'
        )

    def test_templatetag_cache(self):
        '''Проверяем работу templatetag кэша на главной странице'''
        key = make_template_fragment_key('index_page')
        self.guest_client.get(reverse('index'))
        # Проверяем, что в кэш есть данные
        self.assertIsNotNone(cache.get(key))
        # Изменяем данные поста self.post_john
        form_data = {
            'author': self.author_john, 
            'text': 'Text with file',
            'group': self.group_id,
        }
        self.authorized_client_john.post(
                reverse('post_edit', 
                kwargs={
                    'username': self.author_john, 
                    'post_id': self.post_john_id
                }),
                form_data
        )
        self.assertNotIn(form_data['text'], cache.get(key))
        # Проверяем обновится ли кэш после 20 сек
        sleep(20)
        self.guest_client.get(reverse('index'))
        # Проверяем, содержит ли кэш новые данные поста
        self.assertIn(form_data['text'], cache.get(key))
        