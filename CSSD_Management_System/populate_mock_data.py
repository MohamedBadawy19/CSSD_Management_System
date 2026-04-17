import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CSSD_Management_System.settings')
django.setup()

from CSSD_Management_System.models import CustomUser, InventoryItem, InstrumentRequest, RequestItem

def populate():
    # Setup roles if needed
    nurse, created = CustomUser.objects.get_or_create(email='nurse@test.com', defaults={
        'role': 'Department Nurse', 'department': 'Emergency Room'
    })
    
    # Inventory Items
    InventoryItem.objects.all().delete()
    
    items_data = [
        ('Scalpel Blades (#10)', 'Consumables', 8, 20),
        ('Sterilization Pouches', 'Consumables', 15, 50),
        ('Surgical Gloves (Size M)', 'Consumables', 45, 100),
        ('Surgical Drapes', 'Consumables', 25, 40),
        ('Indicator Tape', 'Consumables', 3, 10),
        ('Surgical Scissors', 'Instruments', 50, 10),
        ('Forceps Set', 'Instruments', 45, 10),
        ('Scalpel Kit', 'Instruments', 15, 20),
        ('Retractor', 'Instruments', 30, 5),
        ('Needle Holder', 'Instruments', 40, 10),
        ('Hemostats', 'Instruments', 60, 20),
        ('Suture Kit', 'Instruments', 18, 25),
        ('Clamps', 'Instruments', 80, 20),
    ]

    inventory_objects = {}
    for name, cat, stock, thresh in items_data:
        inventory_objects[name] = InventoryItem.objects.create(
            name=name, category=cat, current_stock=stock, min_threshold=thresh
        )

    # Clear requests
    InstrumentRequest.objects.all().delete()
    
    # Request 1: Packed
    req1 = InstrumentRequest.objects.create(
        requester=nurse,
        priority='Urgent',
        status='Packed',
        department='Emergency Room',
        notes='Required around noon',
    )
    # Timestamps
    req1.submitted_at = timezone.now() - timedelta(hours=4)
    req1.collected_at = timezone.now() - timedelta(hours=3, minutes=30)
    req1.cleaned_at = timezone.now() - timedelta(hours=2, minutes=45)
    req1.sterilized_at = timezone.now() - timedelta(hours=1, minutes=15)
    req1.packed_at = timezone.now() - timedelta(minutes=10)
    req1.save()

    RequestItem.objects.create(request=req1, inventory_item=inventory_objects['Surgical Scissors'], quantity=1)
    RequestItem.objects.create(request=req1, inventory_item=inventory_objects['Forceps Set'], quantity=1)
    RequestItem.objects.create(request=req1, inventory_item=inventory_objects['Scalpel Kit'], quantity=1)

    # Request 2: Collected
    req2 = InstrumentRequest.objects.create(
        requester=nurse,
        priority='Urgent',
        status='Collected',
        department='ICU Ward 3',
        notes='Required for surgery scheduled at 2:00 PM',
    )
    req2.submitted_at = timezone.now() - timedelta(minutes=45)
    req2.collected_at = timezone.now() - timedelta(minutes=20)
    req2.save()

    RequestItem.objects.create(request=req2, inventory_item=inventory_objects['Surgical Scissors'], quantity=1)
    RequestItem.objects.create(request=req2, inventory_item=inventory_objects['Forceps Set'], quantity=1)
    RequestItem.objects.create(request=req2, inventory_item=inventory_objects['Scalpel Kit'], quantity=1)
    RequestItem.objects.create(request=req2, inventory_item=inventory_objects['Clamps'], quantity=2)
    
    print("Database populated successfully.")

if __name__ == '__main__':
    populate()
