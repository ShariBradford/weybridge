from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.forms import ModelForm
from django.shortcuts import reverse

from shop.models import Product

class Cart(models.Model):
    STATUS_OPEN = 1
    STATUS_PENDING = 2
    STATUS_COMPLETED = 3
    STATUS_EXPIRED = 4

    STATUS_CHOICES = (
        (STATUS_OPEN, 'Open'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_EXPIRED, 'Expired'),
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

    def get_absolute_url(self):
        return reverse('cart:cart_details')

    def refresh_cart(self,user):
        """
            Refresh cart items (e.g., if an item has gone on sale since adding to cart, 
            the line total will need to be updated).
        """
        updated = False

        print(f"Cart has {self.items.aggregate(Sum('quantity'))['quantity__sum']} item(s) in it.")

        if self.item_count != self.items.aggregate(Sum('quantity'))['quantity__sum']:
            self.item_count = self.items.aggregate(Sum('quantity'))['quantity__sum']
            updated = True

        for item in self.items.all():
            if item.line_total != item.product.get_sale_price() * item.quantity:
                item.line_total = item.product.get_sale_price() * item.quantity
                item.save()
                updated = True

        if updated:
            self.total = self.items.aggregate(Sum('line_total'))['line_total__sum']
            self.updated_by = user
            self.save()    

    def get_item_count(self,user):
        """
            Get updated item count based on cartitems. Does not update the model instance.
        """
        print(f"Cart has {self.items.aggregate(Sum('quantity'))['quantity__sum']} item(s) in it.")

        return self.items.aggregate(Sum('quantity'))['quantity__sum']    

class CartItem(models.Model):
    product = models.ForeignKey(Product,related_name="item", on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart',related_name="items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    line_total = models.DecimalField(max_digits=12,decimal_places=2,default=0.00, blank=True, null=True)
    is_taxable = models.BooleanField(default=False)
    tax_rate = models.DecimalField(max_digits=12,decimal_places=10,default=0.00, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} Quantity {self.quantity} in Cart #{self.cart.id}"

    def get_line_total(self):
        price = self.product.price
        subtotal = (self.quantity * price)
        if self.is_taxable:
            subtotal *= (1 + self.tax_rate)

        return subtotal

    