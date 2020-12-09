from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, 
        widget= forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(max_length=30, 
        widget= forms.TextInput(attrs={'class':'form-control'}))
    email = forms.EmailField(max_length=254, help_text='Required. Provide a valid email address.', 
        widget= forms.EmailInput(attrs={'class':'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )
