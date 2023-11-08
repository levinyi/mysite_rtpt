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
    origional_seq = models.TextField(verbose_name="SeqAA NT")
    vector = models.ForeignKey(Vector, on_delete=models.CASCADE)
    species = models.ForeignKey(Species, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=255, default='Need_To_Validate')
    create_date = models.DateTimeField(auto_now_add=True)

    forbid_seq = models.CharField(verbose_name="ForbiddenSeqs", max_length=255, null=True, blank=True)
    combined_seq = models.TextField(null=True, blank=True)
    saved_seq = models.TextField(null=True, blank=True)

    gc_content = models.FloatField(null=True, blank=True)
    forbidden_check_list = models.CharField(max_length=255, null=True, blank=True)
    contained_forbidden_list = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.gene_name

class OrderInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gene_infos = models.ManyToManyField(GeneInfo)
    order_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, default='Pending')

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    genes = models.ManyToManyField(GeneInfo)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}'s shopping cart"
