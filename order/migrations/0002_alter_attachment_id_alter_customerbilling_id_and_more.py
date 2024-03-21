# Generated by Django 5.0.1 on 2024-02-08 07:44

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='id',
            field=models.UUIDField(default=uuid.UUID('065c4867-4c39-755c-8004-8ae650e28f30'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='customerbilling',
            name='id',
            field=models.UUIDField(default=uuid.UUID('065c4867-4c39-755c-8000-1eb2bce11f3d'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='customercontact',
            name='id',
            field=models.UUIDField(default=uuid.UUID('065c4867-4c39-755c-8002-330f0e14744e'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='customerdelivery',
            name='id',
            field=models.UUIDField(default=uuid.UUID('065c4867-4c39-755c-8001-00fb4e74a1e8'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='customerorder',
            name='id',
            field=models.UUIDField(default=uuid.UUID('065c4867-4c39-755c-8003-0dec543522f7'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='customerorder',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='orderline',
            name='id',
            field=models.UUIDField(default=uuid.UUID('065c4867-4c39-755c-8005-5e227d9e3f63'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.CreateModel(
            name='OrderAction',
            fields=[
                ('id', models.UUIDField(default=uuid.UUID('065c4867-4c79-75f1-8000-5007e38c95a5'), editable=False, primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_history', to='order.customerorder')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_actions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderComment',
            fields=[
                ('id', models.UUIDField(default=uuid.UUID('065c4867-4c79-75f1-8001-56e184b631ac'), editable=False, primary_key=True, serialize=False)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_comments', to='order.customerorder')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_comments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
