# Generated by Django 4.0.4 on 2023-11-23 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_center', '0010_rename_origional_seq_geneinfo_original_seq'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderinfo',
            name='inquiry_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]