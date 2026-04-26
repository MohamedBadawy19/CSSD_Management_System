from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import InventoryItem

class EmailLoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _('Incorrect email or password. Please try again.'),
        'inactive': _('This account is inactive. Please contact the administrator.'),
    }
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'autofocus': True, 'class': 'form-input',
            'placeholder': 'Email', 'id': 'inputEmail'
        })
    )
    password = forms.CharField(
        label=_("Password"), strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password', 'class': 'form-input',
            'placeholder': 'Password', 'id': 'password'
        }),
    )
