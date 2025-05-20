from django.contrib import admin
from .models import ServiceCategory, Order

class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'fixed_price', 'prepay_amount', 'currency')
    search_fields = ('name', 'description')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'service', 'status', 'created_at')
    list_filter = ('status', 'service')
    search_fields = ('customer_name', 'contact_phone')
    readonly_fields = ('created_at', 'updated_at', 'get_order_token')  # 修改这里
    
    def get_order_token(self, obj):
        return obj.order_token
    get_order_token.short_description = 'Order Token'  # 设置显示名称

admin.site.register(ServiceCategory, ServiceCategoryAdmin)
admin.site.register(Order, OrderAdmin)