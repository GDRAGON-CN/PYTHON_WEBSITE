from django.db import models
from django.forms import ValidationError
from django.contrib.auth.models import User
# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=200,null=True)
    slug = models.SlugField(max_length=200,unique=True)
    def __str__(self):
        return self.name
    
class Product(models.Model):
    category = models.ManyToManyField(Category,related_name='product')
    name = models.CharField(max_length=200,null=True)
    old_price = models.IntegerField()
    new_price = models.IntegerField(null=True, blank=True)
    discount_percent = models.FloatField(default=0, blank=True)
    sold_number = models.IntegerField(default=0)
    rating = models.FloatField(default=0)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    country=models.CharField(max_length=200,null=True)
    brand=models.CharField(max_length=200,null=True)
    detail = models.TextField(null=True,blank=True)
    exclude = ('discount_percent',)
    def __str__(self):
        return self.name
    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url
    
    def clean(self):
        if self.new_price is not None and self.old_price is not None:
            if self.new_price >= self.old_price:
                raise ValidationError("Giá mới phải nhỏ hơn giá cũ!")
            
    def save(self, *args, **kwargs):
        if self.old_price and self.new_price and self.new_price < self.old_price:
            self.discount_percent = round((1 - self.new_price / self.old_price) * 100, 1)
        else:
            self.discount_percent = 0
        super().save(*args, **kwargs)

class Purchase(models.Model):
    quantity=models.IntegerField(max_length=2)

class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)

    def __str__(self):
        return str(self.id)

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total

class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)  # ← Quan trọng!

    @property
    def get_total(self):
        if self.product.new_price:
            return self.product.new_price * self.quantity
        else:
            return self.product.old_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"