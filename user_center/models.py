from django.db import models
from django.contrib.auth.models import User
from product.models import Product, Addon, ExpressionScale, ExpressionHost, PurificationMethod


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


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shopping_cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE)
    STATUS_CHOICES = (
        ('CREATED', 'Created'),
        ('SHIPPING', 'Shipping'),
        ('DELIVERED', 'Delivered'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='CREATED')
    created_at = models.DateTimeField(auto_now_add=True)