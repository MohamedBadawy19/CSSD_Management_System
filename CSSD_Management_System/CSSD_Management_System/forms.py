from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

from .models import InventoryItem, InstrumentSet, SterilizationBatch


# ── Login ──────────────────────────────────────────────────────────────────
class EmailLoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _('Incorrect email or password. Please try again.'),
        'inactive': _('This account is inactive. Please contact the administrator.'),
    }
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'autofocus': True, 'class': 'form-input',
            'placeholder': 'Email', 'id': 'inputEmail',
        })
    )
    password = forms.CharField(
        label=_("Password"), strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password', 'class': 'form-input',
            'placeholder': 'Password', 'id': 'password',
        }),
    )


# ── US-04: Register New Instrument Set ─────────────────────────────────────
class InstrumentSetForm(forms.ModelForm):
    """
    US-04 — Register New Instrument Set.

    Validates:
    • Required fields: name, type, quantity.
    • AC-2: Duplicate name check (case-insensitive) → raises ValidationError.
    New sets always start in state 'Unassigned' (model default).
    """

    TYPE_CHOICES = [
        ('', '-- Select Type --'),
        ('General', 'General'),
        ('Orthopedic', 'Orthopedic'),
        ('Cardiac', 'Cardiac'),
        ('Neurology', 'Neurology'),
        ('ENT', 'ENT'),
        ('Ophthalmic', 'Ophthalmic'),
        ('Gynaecology', 'Gynaecology'),
        ('Other', 'Other'),
    ]

    type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_type'}),
    )

    class Meta:
        model = InstrumentSet
        fields = ['name', 'type', 'quantity']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Major Surgical Set',
                'id': 'id_name',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'placeholder': 'e.g. 5',
                'id': 'id_quantity',
            }),
        }
        labels = {
            'name': 'Set Name',
            'type': 'Type / Category',
            'quantity': 'Quantity',
        }

    def clean_name(self):
        """AC-2: Reject duplicate set names (case-insensitive)."""
        name = self.cleaned_data.get('name', '').strip()
        qs = InstrumentSet.objects.filter(name__iexact=name)
        # Exclude current instance when editing (not needed for creation, but safe)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f'An instrument set named "{name}" already exists. '
                'Please use a unique name.'
            )
        return name

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is not None and qty < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return qty


# ── US-12/13/14: Sterilization Batch ───────────────────────────────────────
class SterilizationBatchForm(forms.ModelForm):
    """
    US-12/13/14 — Create Sterilization Batch.
    AC-1: Includes multiple instrument set selection.
    AC-2: Status defaults to 'In Progress' (model default).
    Validates temperature ≥ 121°C and cycle_duration > 0.
    """

    instrument_sets = forms.ModelMultipleChoiceField(
        queryset=InstrumentSet.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Instrument Sets',
        help_text='Select one or more instrument sets to include in this batch.',
    )

    class Meta:
        model = SterilizationBatch
        fields = ['temperature', 'cycle_duration', 'instrument_sets']
        widgets = {
            'temperature': forms.NumberInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g. 134',
                'step': '0.1', 'min': '0', 'id': 'id_temperature',
            }),
            'cycle_duration': forms.NumberInput(attrs={
                'class': 'form-input', 'placeholder': 'Duration in minutes',
                'step': '1', 'min': '1', 'id': 'id_cycle_duration',
            }),
        }
        labels = {
            'temperature': 'Temperature (°C)',
            'cycle_duration': 'Cycle Duration (minutes)',
        }

    def clean_temperature(self):
        temp = self.cleaned_data.get('temperature')
        if temp is None:
            raise forms.ValidationError('Temperature is required.')
        if temp < 121:
            raise forms.ValidationError(
                f'Temperature {temp}°C is below the minimum 121°C required for sterilization.'
            )
        return temp

    def clean_cycle_duration(self):
        duration = self.cleaned_data.get('cycle_duration')
        if duration is None:
            raise forms.ValidationError('Cycle duration is required.')
        if duration <= 0:
            raise forms.ValidationError('Cycle duration must be greater than 0.')
        return duration


# ── InventoryItem (stock tracking) ─────────────────────────────────────────
class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'category', 'current_stock', 'min_threshold']

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if InventoryItem.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError('An inventory item with this name already exists.')
        return name

