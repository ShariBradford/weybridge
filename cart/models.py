from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.db.models.expressions import F
from django.forms import ModelForm
from django.shortcuts import reverse, get_object_or_404

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="cart", on_delete=models.CASCADE)
    item_count = models.PositiveIntegerField(default=0)
    total = models.DecimalField(max_digits=12,decimal_places=2,default=0.00, blank=True, null=True)
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default = STATUS_OPEN,
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="cart_updated", on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="cart_created", on_delete=models.CASCADE)

    def __str__(self):
        return f"User {self.user.first_name} has {self.item_count} item(s) in the cart for a total of ${self.total}"

    def get_absolute_url(self):
        return reverse('cart:cart_details')

    def refresh_cart(self,user):
        """
            Refresh cart items (e.g., if an item has gone on sale since adding to cart, 
            the line total will need to be updated; if items have been added to the cart, 
            the item_count).
        """
        updated = False

        actual_item_count = self.items.aggregate(Sum('quantity'))['quantity__sum'] or 0
        print(f"Cart has {actual_item_count} item(s) in it.")
        if self.item_count != actual_item_count:
            self.item_count = actual_item_count
            updated = True

        for item in self.items.all():
            actual_line_total = item.product.get_sale_price() * item.quantity
            if item.line_total != actual_line_total:
                item.line_total = actual_line_total
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
        item_count = self.items.aggregate(Sum('quantity'))['quantity__sum'] or 0   
        print(f"Cart has {item_count} item(s) in it.")

        return item_count

    def is_product_in_cart(self,product_id):
        """
            Checks if given product is in the cart. Boolean.
        """

        return CartItem.objects.filter(cart=self,product_id=product_id).exists()

    def is_item_in_cart(self,item_id):
        """
            Checks if given item is in the cart. Boolean.
        """

        return self.items.filter(id=item_id)

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
        price = self.product.get_sale_price()
        subtotal = (self.quantity * price)
        if self.is_taxable:
            subtotal *= (1 + self.tax_rate)

        return subtotal

    