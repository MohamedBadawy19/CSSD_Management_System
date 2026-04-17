from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label=_("Email"), widget=forms.EmailInput(attrs={'autofocus': True, 'class': 'form-input', 'placeholder': 'Email'}))
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-input', 'placeholder': 'Password'}),
    )
