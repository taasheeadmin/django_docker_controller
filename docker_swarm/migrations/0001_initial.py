# Generated by Django 5.2.1 on 2025-05-26 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NodeInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instance_id', models.CharField(max_length=100, unique=True)),
                ('node_id', models.CharField(blank=True, max_length=100, null=True)),
                ('private_ip', models.GenericIPAddressField()),
                ('status', models.CharField(default='provisioning', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ScalingState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(default='global', max_length=100, unique=True)),
                ('pending_capacity', models.PositiveIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
