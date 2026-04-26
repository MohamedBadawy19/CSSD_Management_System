from django.conf import settings
from django.db import models


class InstrumentSet(models.Model):
    STATE_CHOICES = [
        ("Unassigned", "Unassigned"),
        ("Requested", "Requested"),
        ("Collected", "Collected"),
        ("Cleaned", "Cleaned"),
        ("Sterilized", "Sterilized"),
        ("Packed", "Packed"),
        ("Delivered", "Delivered"),
    ]

    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=100)
    quantity = models.IntegerField()
    state = models.CharField(max_length=50, choices=STATE_CHOICES, default="Unassigned")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.state})"


class SterilizationBatch(models.Model):
    STATUS_CHOICES = [
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
    ]

    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    temperature = models.FloatField()
    cycle_duration = models.FloatField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="In Progress")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Batch {self.id} - {self.status} (op: {self.operator.email})"

# Create your models here.
