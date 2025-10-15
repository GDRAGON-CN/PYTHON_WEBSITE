from django.contrib import admin
from .models import Product, Category,Order,OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    exclude = ('discount_percent',)  # ẩn trường tính tự động này khỏi form admin

admin.site.register(Category)
admin.site.register(Order)
admin.site.register(OrderItem)


