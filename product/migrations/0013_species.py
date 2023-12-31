# Generated by Django 4.0.4 on 2023-11-02 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0012_vector_gc_content'),
    ]

    operations = [
        migrations.CreateModel(
            name='Species',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('species_name', models.CharField(max_length=256, verbose_name='物种名称')),
                ('species_note', models.CharField(max_length=256, verbose_name='物种备注')),
            ],
        ),
    ]
