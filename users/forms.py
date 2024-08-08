from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    #nested namespace for configurations, user model is affected
    #fields define what fields will be in the form and the order
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
