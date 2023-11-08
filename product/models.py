from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Product(models.Model):
    product_type = models.CharField(verbose_name="Product_type", max_length=20)
    product_name = models.CharField(verbose_name="Product_name", max_length=20)
    price = models.CharField(verbose_name="Price", max_length=20)
    turnaround_time = models.CharField(verbose_name="Turnaroud_time", max_length=20)
    # number_of_antibody = models.CharField(verbose_name="Number_of_antibody", max_length=20)

    def __str__(self):
        return self.product_name

class Addon(models.Model):
    name = models.CharField(verbose_name="Addon_name", max_length=20)
    desc = models.CharField(verbose_name="Addon_desc", max_length=200)
    price = models.DecimalField(verbose_name="Price", max_digits=10, decimal_places=2)
    product = models.ManyToManyField(Product, verbose_name="Product", related_name="addons")
    turnaround_time = models.CharField(verbose_name="Turnaroud_time", max_length=20)

    def __str__(self):
        return self.name


class ExpressionHost(models.Model):
    host_name = models.CharField(verbose_name="Host_name", max_length=20)
    product = models.ManyToManyField(Product, verbose_name="Product", related_name="hosts")

    def __str__(self):
        return self.host_name


class PurificationMethod(models.Model):
    method_name = models.CharField(verbose_name="Method_name", max_length=20)
    product = models.ManyToManyField(Product, verbose_name="Product", related_name="purification_methods")

    def __str__(self):
        return self.method_name


class ExpressionScale(models.Model):
    scale = models.CharField(verbose_name="Scale", max_length=20)
    product = models.ManyToManyField(Product, verbose_name="Product", related_name="expression_scales")

    def __str__(self):
        return self.scale

class Vector(models.Model):
    user = models.ForeignKey(User, verbose_name="User", on_delete=models.SET_NULL, null=True, blank=True)
    vector_name = models.CharField(verbose_name="Vector_name", max_length=20)

    vector_map = models.TextField(verbose_name="Vector_Seq")
    NC5 = models.TextField(verbose_name="5NC")
    NC3 = models.TextField(verbose_name="3NC")

    create_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=255, default='Need_To_Validate')

    forbid_seq = models.CharField(max_length=255, null=True, blank=True)
    combined_seq = models.TextField(null=True, blank=True)
    saved_seq = models.TextField(null=True, blank=True)

    forbidden_check_list = models.CharField(max_length=255, null=True, blank=True)
    contained_forbidden_list = models.CharField(max_length=255, null=True, blank=True)
    gc_content = models.FloatField(null=True, blank=True)

    def is_company_vector(self):
        return self.user is None

    def __str__(self):
        return self.vector_name

class GeneSynEnzymeCutSite(models.Model):
    enzyme_name = models.CharField(verbose_name="酶切位点", max_length=256)
    enzyme_seq = models.CharField(verbose_name="酶切序列", max_length=256)
    usescope = models.CharField(verbose_name="使用范围", max_length=256)

class Species(models.Model):
    species_name = models.CharField(verbose_name="物种名称", max_length=256)
    species_note = models.CharField(verbose_name="物种备注", max_length=256)

    def __str__(self):
        return self.species_name