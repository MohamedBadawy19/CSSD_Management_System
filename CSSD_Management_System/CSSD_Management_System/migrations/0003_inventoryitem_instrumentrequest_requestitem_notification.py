# Self-contained migration for all feature branches (Proj-17 through Proj-29).
# Depends only on 0002 which exists in c4e87b5 base.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CSSD_Management_System', '0002_alter_customuser_options_customuser_first_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('category', models.CharField(max_length=100)),
                ('current_stock', models.IntegerField(default=0)),
                ('min_threshold', models.IntegerField(default=10)),
            ],
        ),
        migrations.CreateModel(
            name='InstrumentRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.CharField(
                    choices=[('Normal', 'Normal'), ('Urgent', 'Urgent')],
                    default='Normal',
                    max_length=50,
                )),
                ('status', models.CharField(
                    choices=[
                        ('Requested', 'Requested'),
                        ('Collected', 'Collected'),
                        ('Cleaned', 'Cleaned'),
                        ('Sterilized', 'Sterilized'),
                        ('Packed', 'Packed'),
                        ('Delivered', 'Delivered'),
                    ],
                    default='Requested',
                    max_length=50,
                )),
                ('department', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('collected_at', models.DateTimeField(blank=True, null=True)),
                ('cleaned_at', models.DateTimeField(blank=True, null=True)),
                ('sterilized_at', models.DateTimeField(blank=True, null=True)),
                ('packed_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('requester', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='requests',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('last_operator', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='processed_requests',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('batch', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='requests',
                    to='CSSD_Management_System.sterilizationbatch',
                )),
            ],
        ),
        migrations.CreateModel(
            name='RequestItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=1)),
                ('request', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='CSSD_Management_System.instrumentrequest',
                )),
                ('inventory_item', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='CSSD_Management_System.inventoryitem',
                )),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=255)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('request', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='CSSD_Management_System.instrumentrequest',
                )),
            ],
        ),
    ]
