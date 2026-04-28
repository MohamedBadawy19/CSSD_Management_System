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
        return temp

    def clean_cycle_duration(self):
        duration = self.cleaned_data.get('cycle_duration')
        if duration is not None and duration <= 0:
            raise forms.ValidationError('Cycle duration must be greater than 0 minutes.')
        return duration