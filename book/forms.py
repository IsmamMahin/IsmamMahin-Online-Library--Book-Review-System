from django import forms
from .models import Book, Comment
from django.contrib.auth.models import User

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'description', 'cover_image', 'category', 'tag']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = User 
        fields = ['username', 'first_name', 'last_name', 'email']