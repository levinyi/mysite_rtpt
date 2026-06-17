import re
from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.utils import timezone


class VectorFileStorage(FileSystemStorage):
    """
    自定义存储类，保留文件名中的括号。
    Django 默认的 get_valid_name 会去掉括号等特殊字符，
    但载体文件名中的括号包含抗性信息（如 pCVa999(Kan)-xxx.gb），必须保留。
    """
    def get_valid_name(self, name):
        # 只去掉真正危险的字符（路径分隔符、空字节等），保留括号
        name = name.replace('\x00', '')
        # 去掉路径中的目录遍历
        name = re.sub(r'[/\\]', '', name)
        # 去掉首尾空格
        name = name.strip()
        return name


vector_storage = VectorFileStorage()


# Create your models here.
def user_directory_path(instance, filename):
    # 文件将被上传到 MEDIA_ROOT/user_<id>/vector_file/<filename>
    if not instance.user:
        return f'user/vector_file/{filename}'
    else:
        return 'user_{0}/vector_file/{1}'.format(instance.user.id, filename)

class Vector(models.Model):
    user = models.ForeignKey(User, verbose_name="User", on_delete=models.CASCADE, null=True, blank=True)
    # on_delete=models.SET_NULL,这里有bug，设置成SET_NULL后，如果user被删除了，那么这个vector的user就会变成null, 就会变成公司的vector了，就会展示在公司的vector列表里面，这是不对的
    # 直接设置成CASCADE吧，这样user被删除了，这个vector也会被删除，这样就不会出现这个问题了

    vector_id = models.CharField(verbose_name="Vector_ID", max_length=200, null=True, blank=True)
    vector_name = models.CharField(verbose_name="Vector_name", max_length=200)
    vector_map = models.TextField(verbose_name="Vector_Seq", blank=True, default='')  # 这里的vector_map是指序列，不是图片
    NC5 = models.TextField(verbose_name="v5NC", blank=True, default='')
    NC3 = models.TextField(verbose_name="v3NC", blank=True, default='')
    iu20 = models.TextField(verbose_name="iu20", null=True, blank=True)
    id20 = models.TextField(verbose_name="id20", null=True, blank=True)
    i5NC = models.TextField(verbose_name="i5NC", null=True, blank=True, help_text="v5NC移位碱基")
    i3NC = models.TextField(verbose_name="i3NC", null=True, blank=True, help_text="v3NC移位碱基")
    vector_file = models.FileField(verbose_name="用户上传的vector文件", upload_to=user_directory_path, storage=vector_storage, null=True, blank=True)
    vector_png = models.ImageField(verbose_name="改造后的Vector_png", upload_to=user_directory_path, null=True, blank=True)

    vector_gb = models.FileField(verbose_name="genebank file", upload_to=user_directory_path, storage=vector_storage, null=True, blank=True)

    # 载体改造自动化设计相关字段
    cloning_method = models.CharField(verbose_name="克隆方法", max_length=50, null=True, blank=True, help_text="Gibson/GoldenGate/T4")
    antibiotic_resistance = models.CharField(verbose_name="抗性", max_length=50, null=True, blank=True, help_text="Amp/Kan/Chlor/etc")
    design_status = models.CharField(verbose_name="设计状态", max_length=50, null=True, blank=True, default='Pending', help_text="Pending/Processing/Completed/Failed")
    design_error = models.TextField(verbose_name="设计错误信息", null=True, blank=True)
    primer_forward = models.TextField(verbose_name="正向引物序列", null=True, blank=True)
    primer_reverse = models.TextField(verbose_name="反向引物序列", null=True, blank=True)
    primer_forward_tm = models.FloatField(verbose_name="正向引物Tm", null=True, blank=True)
    primer_reverse_tm = models.FloatField(verbose_name="反向引物Tm", null=True, blank=True)
    colony_pcr_primers = models.TextField(verbose_name="菌落PCR引物(5对, JSON)", null=True, blank=True)

    create_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=255, default='Received')

    # 可见性与归属解耦：
    #   user=None  + is_public=True  -> 公司公开载体（客户目录可见）
    #   user=None  + is_public=False -> 公司内部载体（仅后台/管理员可见）
    #   user=客户  + is_public=False -> 客户私有载体（仅该客户可见）
    # 归属由“上传者身份”决定：管理员上传 -> user=None（公司）；客户上传 -> user=客户。
    is_public = models.BooleanField(default=False, verbose_name="是否对客户公开")

    def is_company_vector(self):
        return self.user is None

    def is_visible_to_customers(self):
        """是否出现在客户目录里（公司公开载体）。"""
        return self.is_public

    def __str__(self):
        return self.vector_name

class GeneSynEnzymeCutSite(models.Model):
    enzyme_name = models.CharField(verbose_name="酶切位点", max_length=256)
    enzyme_seq = models.CharField(verbose_name="酶切序列", max_length=256)
    usescope = models.CharField(verbose_name="使用范围", max_length=256)

class Species(models.Model):
    species_name = models.CharField(verbose_name="物种名称", max_length=256)
    species_note = models.CharField(verbose_name="物种备注", max_length=256, blank=True, null=True)

    species_codon_file = models.FileField(verbose_name="codon文件", upload_to='codon_usage_table/', blank=True, null=True)

    def __str__(self):
        return self.species_name