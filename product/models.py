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

def user_directory_path(instance, filename):
    # 文件将被上传到 MEDIA_ROOT/user_<id>/vector_file/<filename>
    if not instance.user:
        return 'user/vector_file/{1}'.format(filename)
    else:
        return 'user_{0}/vector_file/{1}'.format(instance.user.id, filename)

class Vector(models.Model):
    user = models.ForeignKey(User, verbose_name="User", on_delete=models.SET_NULL, null=True, blank=True)
    vector_id = models.CharField(verbose_name="Vector_ID", max_length=20, null=True, blank=True)
    vector_name = models.CharField(verbose_name="Vector_name", max_length=20)
    vector_map = models.TextField(verbose_name="Vector_Seq")
    NC5 = models.TextField(verbose_name="v5NC")
    NC3 = models.TextField(verbose_name="v3NC")
    iu20 = models.TextField(verbose_name="iu20", null=True, blank=True)
    id20 = models.TextField(verbose_name="id20", null=True, blank=True)
    vector_file = models.FileField(verbose_name="用户上传的vector文件", upload_to=user_directory_path, null=True, blank=True)
    vector_png = models.ImageField(verbose_name="改造后的Vector_png", upload_to=user_directory_path, null=True, blank=True)

    create_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=255, default='Received')

    # 这两个好像没有用到，可以删掉了
    combined_seq = models.TextField(null=True, blank=True)
    saved_seq = models.TextField(null=True, blank=True)

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