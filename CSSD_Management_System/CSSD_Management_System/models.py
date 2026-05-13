from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


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
    ROLE_CHOICES = [
        ('System Administrator', 'System Administrator'),
        ('CSSD Technician', 'CSSD Technician'),
        ('Department Nurse', 'Department Nurse'),
        ('Hospital Administrator', 'Hospital Administrator'),
    ]

    username = None
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    department = models.CharField(max_length=100, blank=True)

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

    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=100)
    quantity = models.IntegerField()
    state = models.CharField(max_length=50, choices=STATE_CHOICES, default='Unassigned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.state})"

class SterilizationBatch(models.Model):
    STATUS_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    operator = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    temperature = models.FloatField()
    cycle_duration = models.FloatField()  # in minutes
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='In Progress')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Batch {self.id} - {self.status} (op: {self.operator.email})"

class InventoryItem(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    current_stock = models.IntegerField(default=0)
    min_threshold = models.IntegerField(default=10)

    @property
    def status(self):
        if self.current_stock == 0:
            return 'Out of Stock'
        elif self.current_stock <= self.min_threshold:
            return 'Limited'
        return 'Available'

    @property
    def percentage(self):
        if self.min_threshold == 0:
            return 100
        return min((self.current_stock / self.min_threshold) * 100, 100)

    def __str__(self):
        return self.name

class InstrumentRequest(models.Model):
    PRIORITY_CHOICES = [
        ('Normal', 'Normal'),
        ('Urgent', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('Requested', 'Requested'),
        ('Collected', 'Collected'),
        ('Cleaned', 'Cleaned'),
        ('Sterilized', 'Sterilized'),
        ('Packed', 'Packed'),
        ('Delivered', 'Delivered'),
    ]

    requester = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='requests')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='Normal')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Requested')
    department = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    last_operator = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='processed_requests'
    )
    # Link to sterilization batch (required before marking Sterilized)
    batch = models.ForeignKey(SterilizationBatch, null=True, blank=True, on_delete=models.SET_NULL, related_name='requests')

    is_archived = models.BooleanField(default=False)

    # Timestamps for timeline
    submitted_at = models.DateTimeField(auto_now_add=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    cleaned_at = models.DateTimeField(null=True, blank=True)
    sterilized_at = models.DateTimeField(null=True, blank=True)
    packed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"REQ-{self.id:04d} - {self.status}"

    def get_eta(self):
        """Calculates ETA based on current status and average processing times."""
        # Define average durations in minutes for each remaining step
        durations = {
            'Requested': 120,  # 2 hours total
            'Collected': 90,   # 1.5 hours remaining
            'Cleaned': 60,     # 1 hour remaining
            'Sterilized': 30,  # 30 mins remaining (packing/delivery)
            'Packed': 15,      # 15 mins remaining
            'Delivered': 0
        }
        
        if self.status == 'Delivered':
            return "Ready"
        remaining_minutes = durations.get(self.status, 0)
        # Use the current time or last update time as a base
        eta_time = timezone.now() + timedelta(minutes=remaining_minutes)

        
        return f"Ready by ~{eta_time.strftime('%I:%M %p')}"

class RequestItem(models.Model):
    request = models.ForeignKey(InstrumentRequest, on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.inventory_item.name}"

class Notification(models.Model):
    """Simple in-app notification for nurses when their request status changes."""
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    request = models.ForeignKey(InstrumentRequest, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notif for {self.recipient.email}: {self.message}"
