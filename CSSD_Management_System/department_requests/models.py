from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class InventoryItem(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    current_stock = models.IntegerField(default=0)
    min_threshold = models.IntegerField(default=10)

    @property
    def status(self):
        if self.current_stock == 0:
            return "Out of Stock"
        if self.current_stock <= self.min_threshold:
            return "Limited"
        return "Available"

    @property
    def percentage(self):
        if self.min_threshold == 0:
            return 100
        return min((self.current_stock / self.min_threshold) * 100, 100)

    def __str__(self):
        return self.name


class InstrumentRequest(models.Model):
    PRIORITY_CHOICES = [
        ("Normal", "Normal"),
        ("Urgent", "Urgent"),
    ]
    STATUS_CHOICES = [
        ("Requested", "Requested"),
        ("Collected", "Collected"),
        ("Cleaned", "Cleaned"),
        ("Sterilized", "Sterilized"),
        ("Packed", "Packed"),
        ("Delivered", "Delivered"),
    ]

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="requests"
    )
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default="Normal")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Requested")
    department = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    last_operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_requests",
    )
    batch = models.ForeignKey(
        "state_machine.SterilizationBatch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requests",
    )
    is_archived = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    cleaned_at = models.DateTimeField(null=True, blank=True)
    sterilized_at = models.DateTimeField(null=True, blank=True)
    packed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"REQ-{self.id:04d} - {self.status}"

    def get_eta(self):
        durations = {
            "Requested": 120,
            "Collected": 90,
            "Cleaned": 60,
            "Sterilized": 30,
            "Packed": 15,
            "Delivered": 0,
        }
        if self.status == "Delivered":
            return "Ready"
        eta_time = timezone.now() + timedelta(minutes=durations.get(self.status, 0))
        return f"Ready by ~{eta_time.strftime('%I:%M %p')}"


class RequestItem(models.Model):
    request = models.ForeignKey(
        InstrumentRequest, on_delete=models.CASCADE, related_name="items"
    )
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.inventory_item.name}"


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    request = models.ForeignKey(InstrumentRequest, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notif for {self.recipient.email}: {self.message}"

# Create your models here.
