from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name='Группа',
        max_length=200,
        help_text='Дайте короткое название группе',
    )
    slug = models.SlugField(
        verbose_name='Ссылка',
        unique=True,
        help_text=(
            'Укажите название ссылки для группы. Используйте '
            'только латиницу, цифры, дефисы и знаки '
            'подчёркивания'
        ),
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Дайте подробное описание группе',
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Пост',
        help_text='Напишите текст к посту',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE, 
        related_name='posts',
        help_text='Выберите автора поста',
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='posts',
        help_text='Назначьте группу для поста',
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='posts/',
        blank=True, 
        null=True
    )  

    class Meta:
        ordering = ('-pub_date',)  
    
    def __str__(self): 
        return self.text[:15]      


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        on_delete=models.CASCADE, 
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE, 
        related_name='comments',
        help_text='Автор комментария',
    )
    text = models.TextField(
        verbose_name='Комментарий',
        help_text='Напишите комментарий к посту',
    )
    created = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )
    
    def __str__(self): 
        return self.text[:15]  


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE, 
        related_name='follower',
        help_text='Подписчик',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE, 
        related_name='following',
        help_text='Автор',
    )
