from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'System Administrator')
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    # Roles as constants
    ROLE_CHOICES = [
        ('System Administrator', 'System Administrator'),
        ('CSSD Technician', 'CSSD Technician'),
        ('Department Nurse', 'Department Nurse'),
        ('Hospital Administrator', 'Hospital Administrator'),
    ]

    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    department = models.CharField(max_length=100)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class InstrumentSet(models.Model):
    STATE_CHOICES = [
        ('Unassigned', 'Unassigned'),
        ('Requested', 'Requested'),
        ('Collected', 'Collected'),
        ('Cleaned', 'Cleaned'),
        ('Sterilized', 'Sterilized'),
        ('Packed', 'Packed'),
        ('Delivered', 'Delivered'),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100)
    quantity = models.IntegerField()
    state = models.CharField(max_length=50, choices=STATE_CHOICES, default='Unassigned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.state})"

class SterilizationBatch(models.Model):
    operator = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    temperature = models.FloatField()
    cycle_duration = models.FloatField()
    status = models.CharField(max_length=50, default='In Progress')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Batch {self.id} - {self.status}"


