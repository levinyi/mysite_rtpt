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

    # new field for sequence fragmentation
    fragments_data = models.JSONField(null=True, blank=True)
    # 格式: [
    #   {"index": 1, "seq": "ATCG...", "start": 0, "end": 1000, "penalty_score": 25.5},
    #   {"index": 2, "seq": "GCTA...", "start": 1000, "end": 2000, "penalty_score": 27.8}
    # ]

    # 限制性酶切位点自动决策相关字段
    restriction_decision = models.CharField(max_length=50, null=True, blank=True, help_text="accept/reject")
    restriction_process_route = models.CharField(max_length=50, null=True, blank=True, help_text="BsaI/BsmBI")
    restriction_message = models.TextField(null=True, blank=True, help_text="决策提示信息")
    restriction_requires_manual_review = models.BooleanField(default=False, help_text="是否需要人工评估")
    bsai_count = models.IntegerField(null=True, blank=True, help_text="BsaI位点数量")
    bsmbi_count = models.IntegerField(null=True, blank=True, help_text="BsmBI位点数量")
    bsai_positions = models.JSONField(null=True, blank=True, help_text="BsaI位点位置列表")
    bsmbi_positions = models.JSONField(null=True, blank=True, help_text="BsmBI位点位置列表")

    def __str__(self):
        return self.gene_name


class OrderInfo(models.Model):
    # Order status choices for production workflow
    STATUS_CHOICES = [
        ('Pending', 'Pending'),              # 待确认
        ('Confirmed', 'Confirmed'),          # 已确认
        ('InProduction', 'In Production'),   # 生产中
        ('QualityCheck', 'Quality Check'),   # 质检中
        ('Shipping', 'Shipping'),            # 配送中
        ('Completed', 'Completed'),          # 已完成
        ('Cancelled', 'Cancelled'),          # 已取消
    ]

    def user_directory_path(instance, filename):
        # 文件将被上传到 MEDIA_ROOT/user_<id>/vector_file/<filename>
        return 'user_{0}/report_file/{1}'.format(instance.id, filename)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gene_infos = models.ManyToManyField(GeneInfo)
    order_time = models.DateTimeField(auto_now_add=True)
    inquiry_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(
        max_length=100,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    url = models.URLField(verbose_name="report url", blank=True)
    report_file = models.FileField(upload_to=user_directory_path, null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    def is_completed(self):
        """Check if order is completed"""
        return self.status == 'Completed'

    def is_in_progress(self):
        """Check if order is in progress (not completed or cancelled)"""
        return self.status not in ['Completed', 'Cancelled']


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


class ProcessTask(models.Model):
    """
    Track async sequence processing tasks
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    task_id = models.CharField(max_length=255, unique=True, verbose_name="Celery Task ID")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vector = models.ForeignKey(Vector, on_delete=models.SET_NULL, null=True, blank=True)
    species = models.ForeignKey(Species, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0, verbose_name="Processed sequences")
    total = models.IntegerField(default=0, verbose_name="Total sequences")

    error_message = models.TextField(null=True, blank=True)
    gene_ids = models.JSONField(null=True, blank=True, help_text="List of created GeneInfo IDs")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"ProcessTask {self.task_id} - {self.status} ({self.progress}/{self.total})"

    def get_progress_percentage(self):
        """Calculate progress percentage"""
        if self.total == 0:
            return 0
        return int((self.progress / self.total) * 100)