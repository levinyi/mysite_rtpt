from django.db import models
from django.contrib.auth.models import User
from product.models import Species, Vector
import uuid


class GeneInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gene_name = models.CharField(verbose_name="Gene name", max_length=200)
    
    original_seq = models.TextField(verbose_name="original_seq SeqAA NT")
    combined_seq = models.TextField(null=True, blank=True)
    saved_seq = models.TextField(null=True, blank=True)

    vector = models.ForeignKey(Vector, on_delete=models.SET_NULL, null=True)
    species = models.ForeignKey(Species, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=255, default='Need_To_Validate')
    create_date = models.DateTimeField(auto_now_add=True)

    forbid_seq = models.CharField(verbose_name="ForbiddenSeqs", max_length=255, null=True, blank=True)

    # gc_content = models.FloatField(null=True, blank=True)
    forbidden_check_list = models.CharField(max_length=255, null=True, blank=True)
    contained_forbidden_list = models.CharField(max_length=255, null=True, blank=True)

    i5nc = models.TextField(verbose_name="i5nc", null=True, blank=True)
    i3nc = models.TextField(verbose_name="i3nc", null=True, blank=True)

    # new fields
    original_highlights = models.JSONField(null=True, blank=True)
    modified_highlights = models.JSONField(null=True, blank=True)
    original_gc_content = models.FloatField(null=True, blank=True)
    modified_gc_content = models.FloatField(null=True, blank=True)

    # new fields
    analysis_results = models.JSONField(verbose_name="SequenceAnalyzer", null=True, blank=True)
    penalty_score = models.FloatField(verbose_name="penalty_score", null=True, blank=True)

    # new fields 20241125
    seq_type = models.CharField(max_length=255, null=True, blank=True)
    optimization_id = models.CharField(max_length=225, null=True, blank=True)
    optimization_method = models.CharField(max_length=255, null=True, blank=True)
    optimization_message = models.TextField(null=True, blank=True)
    optimization_status = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.gene_name


class OrderInfo(models.Model):
    def user_directory_path(instance, filename):
        # 文件将被上传到 MEDIA_ROOT/user_<id>/vector_file/<filename>
        return 'user_{0}/report_file/{1}'.format(instance.id, filename)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gene_infos = models.ManyToManyField(GeneInfo)
    order_time = models.DateTimeField(auto_now_add=True)
    inquiry_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=100, default='Pending')

    url = models.URLField(verbose_name="report url", blank=True)
    report_file = models.FileField(upload_to=user_directory_path, null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    genes = models.ManyToManyField(GeneInfo)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}'s shopping cart"


# not used????
class GeneOptimization(models.Model):
    gene = models.ForeignKey(GeneInfo, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vector = models.ForeignKey(Vector, on_delete=models.CASCADE)
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    status = models.CharField(max_length=255, default='pending')
    start_time = models.DateTimeField(verbose_name="start_time", auto_now_add=True, blank=True, null=True)
    end_time = models.DateField(verbose_name='end_time', blank=True, null=True)

    def __str__(self):
        return f"Optimization for {self.gene.gene_name}"