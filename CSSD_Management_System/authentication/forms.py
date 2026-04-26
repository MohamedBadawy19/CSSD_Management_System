from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class EmailLoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": _("Incorrect email or password. Please try again."),
        "inactive": _("This account is inactive. Please contact the administrator."),
    }

    username = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-input", "placeholder": "Email", "id": "inputEmail"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-input", "placeholder": "Password", "id": "password"}
        )
    )
