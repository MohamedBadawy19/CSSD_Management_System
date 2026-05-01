from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import SterilizationBatch

class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email',
        'id': 'inputEmail'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
        'id': 'inputPassword'
    }))

class SterilizationBatchForm(forms.ModelForm):
    """Form for creating a SterilizationBatch (US-19, US-24)."""

    class Meta:
        model = SterilizationBatch
        fields = ['temperature', 'cycle_duration']
        labels = {
            'temperature': 'Temperature (°C)',
            'cycle_duration': 'Cycle Duration (minutes)',
        }
        widgets = {
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'min': '121', 'step': '0.1'}),
            'cycle_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '1'}),
        }

    def clean_temperature(self):
        temp = self.cleaned_data.get('temperature')
        if temp is not None and temp < 121:
            raise forms.ValidationError(
                'Temperature must be at least 121°C for effective sterilization.'
            )
from .models import SterilizationBatch, InventoryItem

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

class SterilizationBatchForm(forms.ModelForm):
    class Meta:
        model = SterilizationBatch
        fields = ['temperature', 'cycle_duration']
        widgets = {
            'temperature': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 134', 'step': '0.1', 'min': '0'}),
            'cycle_duration': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Duration in minutes', 'step': '1', 'min': '1'}),
        }
        labels = {'temperature': 'Temperature (°C)', 'cycle_duration': 'Cycle Duration (minutes)'}

    def clean_temperature(self):
        temp = self.cleaned_data.get('temperature')
        if temp is None:
            raise forms.ValidationError('Temperature is required.')
        if temp < 121:
            raise forms.ValidationError(f'Temperature {temp}°C is below minimum 121°C required for sterilization.')
        return temp

    def clean_cycle_duration(self):
        duration = self.cleaned_data.get('cycle_duration')
        if duration is None:
            raise forms.ValidationError('Cycle duration is required.')
        if duration <= 0:
            raise forms.ValidationError('Cycle duration must be greater than 0.')
        return duration

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'category', 'current_stock', 'min_threshold']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if InventoryItem.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("An instrument set with this name already exists.")
        return name
