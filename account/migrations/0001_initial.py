# Generated by Django 4.1 on 2023-09-06 02:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=200)),
                ('last_name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('company', models.CharField(max_length=254)),
                ('department', models.CharField(blank=True, max_length=200)),
                ('phone', models.CharField(max_length=200, null=True)),
                ('register_time', models.DateField(auto_now_add=True)),
                ('photo', models.ImageField(blank=True, upload_to='')),
                ('level', models.SmallIntegerField(blank=True, default=1)),
                ('shipping_address', models.CharField(max_length=500)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
