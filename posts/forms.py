from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        exclude = ('author', 'pub_date',)
        labels = {
            'group': 'Группа',
            'text': 'Текст',
        }
        help_texts = {
            'group': 'Выберите группу или оставьте ее пустой',
            'text': 'Добавьте текст для новой записи'
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        if text == '':
            raise forms.ValidationError(
                'Заполните текст к новой записи!'
            ) 
        return text


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        exclude = ('post', 'author', 'created')
        labels = {
            'text': 'Комментарий',
        }
        help_texts = {
            'text': 'Добавьте комментарий к записи'
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        if text == '':
            raise forms.ValidationError(
                'Заполните текст к новой записи!'
            ) 
        return text
