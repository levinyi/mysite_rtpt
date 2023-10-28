# Generated by Django 4.0.4 on 2023-10-28 00:46

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_alter_vector_vector_map'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneSynEnzymeCutSite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enzyme_name', models.CharField(max_length=256, verbose_name='酶切位点')),
                ('enzyme_seq', models.CharField(max_length=256, verbose_name='酶切序列')),
                ('usescope', models.CharField(max_length=256, verbose_name='使用范围')),
            ],
        ),
        migrations.RemoveField(
            model_name='vector',
            name='cloning_site',
        ),
        migrations.RemoveField(
            model_name='vector',
            name='is_ready_to_use',
        ),
        migrations.AddField(
            model_name='vector',
            name='combined_seq',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vector',
            name='create_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='vector',
            name='forbid_seq',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='vector',
            name='saved_seq',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vector',
            name='status',
            field=models.CharField(default='Need_To_Validate', max_length=255),
        ),
    ]
