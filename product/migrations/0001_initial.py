# Generated by Django 4.1 on 2023-09-06 02:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_type', models.CharField(max_length=20, verbose_name='Product_type')),
                ('product_name', models.CharField(max_length=20, verbose_name='Product_name')),
                ('price', models.CharField(max_length=20, verbose_name='Price')),
                ('turnaround_time', models.CharField(max_length=20, verbose_name='Turnaroud_time')),
            ],
        ),
        migrations.CreateModel(
            name='purification_method',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method_name', models.CharField(max_length=20, verbose_name='Method_name')),
                ('product', models.ManyToManyField(related_name='purification_methods', to='product.product', verbose_name='Product')),
            ],
        ),
        migrations.CreateModel(
            name='ExpressionScale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scale', models.CharField(max_length=20, verbose_name='Scale')),
                ('product', models.ManyToManyField(related_name='expression_scales', to='product.product', verbose_name='Product')),
            ],
        ),
        migrations.CreateModel(
            name='expression_host',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host_name', models.CharField(max_length=20, verbose_name='Host_name')),
                ('product', models.ManyToManyField(related_name='hosts', to='product.product', verbose_name='Product')),
            ],
        ),
        migrations.CreateModel(
            name='Addon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='Addon_name')),
                ('desc', models.CharField(max_length=200, verbose_name='Addon_desc')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Price')),
                ('turnaround_time', models.CharField(max_length=20, verbose_name='Turnaroud_time')),
                ('product', models.ManyToManyField(related_name='addons', to='product.product', verbose_name='Product')),
            ],
        ),
    ]
