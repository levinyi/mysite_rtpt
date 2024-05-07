from django.db import models
from django.contrib.auth.models import User
from product.models import Product, Addon, ExpressionScale, ExpressionHost, PurificationMethod, Species, Vector


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project_name = models.CharField(verbose_name="Project_name", max_length=20, null=True, blank=True)
    adding_time = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = (
        ('COMPLETED', 'Completed'),
        ('INCOMPLETE', 'Incomplete'),
        ('READYTOSUBMIT', 'ReadyToSubmit'),
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='INCOMPLETE')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    purification_method = models.ForeignKey(PurificationMethod, on_delete=models.CASCADE)
    express_host = models.ForeignKey(ExpressionHost, on_delete=models.CASCADE,null=True, blank=True)
    scale = models.ForeignKey(ExpressionScale,on_delete=models.CASCADE, null=True, blank=True)
    antibody_number = models.PositiveSmallIntegerField(verbose_name="Number", null=True, blank=True)
    analysis = models.ForeignKey(Addon, on_delete=models.CASCADE, null=True, blank=True)
    total_price = models.PositiveSmallIntegerField(verbose_name="Total_Price")
    sequence_file = models.CharField(verbose_name="序列文件", max_length=200, null=True, blank=True)

    def __str__(self):
        return str(self.id)


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
