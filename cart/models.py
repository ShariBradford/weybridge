from django.db import models
from shop.models import Product
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User

class Cart(models.Model):
    STATUS_OPEN = 1
    STATUS_PENDING = 2
    STATUS_COMPLETED = 3

    STATUS_CHOICES = (
        (STATUS_OPEN, 'Open'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
    )
    user = models.ForeignKey(User,related_name="cart", on_delete=models.CASCADE)
    item_count = models.PositiveIntegerField(default=0)
    total = models.DecimalField(max_digits=12,decimal_places=2,default=0.00, blank=True, null=True)
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default = STATUS_OPEN,
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User,related_name="cart_updated", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User,related_name="cart_created", on_delete=models.CASCADE)

    def __str__(self):
        return f"User {self.user.first_name} has {self.item_count} item(s) in the cart for a total of ${self.total}"

class CartItem(models.Model):
    product = models.ForeignKey(Product,related_name="item", on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart',related_name="items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    line_total = models.DecimalField(max_digits=12,decimal_places=2,default=0.00, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} Quantity {self.quantity} in Cart #{self.cart.id}"