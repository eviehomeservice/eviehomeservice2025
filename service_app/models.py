from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from cloudinary.models import CloudinaryField

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    steps = models.TextField()
    notes = models.TextField(blank=True)
    fixed_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prepay_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=[('RMB', '人民币'), ('CAD', '加元')], default='CAD')
    provider_name = models.CharField(max_length=100)
    provider_contact = models.CharField(max_length=100)
    provider_email = models.EmailField(blank=True)
    provider_wechat = models.CharField(max_length=50, blank=True)
    provider_phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
    ]
    
    service = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    service_date = models.DateField()

    def clean(self):
        if self.service_date < timezone.now().date():
            raise ValidationError({'service_date': "服务日期不能是过去的时间"})
        
    service_address = models.TextField()
    contact_email = models.EmailField(blank=True)
    contact_wechat = models.CharField(max_length=50, blank=True)
    contact_phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_proof = CloudinaryField('payment_proof', blank=True, null=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 新增评分字段
    feedback = models.TextField(blank=True)  # 新增反馈字段
    order_token = models.CharField(max_length=32, unique=True)
    
    def __str__(self):
        return f"{self.customer_name} - {self.service.name}"
