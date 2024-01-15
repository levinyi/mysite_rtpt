# Generated by Django 4.1 on 2024-01-15 08:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import product.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GeneSynEnzymeCutSite",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("enzyme_name", models.CharField(max_length=256, verbose_name="酶切位点")),
                ("enzyme_seq", models.CharField(max_length=256, verbose_name="酶切序列")),
                ("usescope", models.CharField(max_length=256, verbose_name="使用范围")),
            ],
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "product_type",
                    models.CharField(max_length=20, verbose_name="Product_type"),
                ),
                (
                    "product_name",
                    models.CharField(max_length=20, verbose_name="Product_name"),
                ),
                ("price", models.CharField(max_length=20, verbose_name="Price")),
                (
                    "turnaround_time",
                    models.CharField(max_length=20, verbose_name="Turnaroud_time"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Species",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("species_name", models.CharField(max_length=256, verbose_name="物种名称")),
                ("species_note", models.CharField(max_length=256, verbose_name="物种备注")),
            ],
        ),
        migrations.CreateModel(
            name="Vector",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "vector_id",
                    models.CharField(
                        blank=True, max_length=20, null=True, verbose_name="Vector_ID"
                    ),
                ),
                (
                    "vector_name",
                    models.CharField(max_length=20, verbose_name="Vector_name"),
                ),
                ("vector_map", models.TextField(verbose_name="Vector_Seq")),
                ("NC5", models.TextField(verbose_name="v5NC")),
                ("NC3", models.TextField(verbose_name="v3NC")),
                ("iu20", models.TextField(blank=True, null=True, verbose_name="iu20")),
                ("id20", models.TextField(blank=True, null=True, verbose_name="id20")),
                (
                    "vector_file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=product.models.user_directory_path,
                        verbose_name="用户上传的vector文件",
                    ),
                ),
                (
                    "vector_png",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to=product.models.user_directory_path,
                        verbose_name="改造后的Vector_png",
                    ),
                ),
                (
                    "create_date",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("status", models.CharField(default="Received", max_length=255)),
                ("combined_seq", models.TextField(blank=True, null=True)),
                ("saved_seq", models.TextField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PurificationMethod",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "method_name",
                    models.CharField(max_length=20, verbose_name="Method_name"),
                ),
                (
                    "product",
                    models.ManyToManyField(
                        related_name="purification_methods",
                        to="product.product",
                        verbose_name="Product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ExpressionScale",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("scale", models.CharField(max_length=20, verbose_name="Scale")),
                (
                    "product",
                    models.ManyToManyField(
                        related_name="expression_scales",
                        to="product.product",
                        verbose_name="Product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ExpressionHost",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "host_name",
                    models.CharField(max_length=20, verbose_name="Host_name"),
                ),
                (
                    "product",
                    models.ManyToManyField(
                        related_name="hosts",
                        to="product.product",
                        verbose_name="Product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Addon",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=20, verbose_name="Addon_name")),
                ("desc", models.CharField(max_length=200, verbose_name="Addon_desc")),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name="Price"
                    ),
                ),
                (
                    "turnaround_time",
                    models.CharField(max_length=20, verbose_name="Turnaroud_time"),
                ),
                (
                    "product",
                    models.ManyToManyField(
                        related_name="addons",
                        to="product.product",
                        verbose_name="Product",
                    ),
                ),
            ],
        ),
    ]
