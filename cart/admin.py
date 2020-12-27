from django.contrib import admin
from .models import *

# admin.site.register(Cart)
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    search_fields = ('user__first_name','user__last_name')
    readonly_fields = ('created_by','updated_by','created_at','updated_at')
    list_display = ('user', 'item_count', 'total', 'status', 'active', 'updated_at', 'id')
    fields = ('user', ('item_count', 'total'), ('status', 'active'), ('created_at','created_by'),('updated_by','updated_at'))
    ordering = ('-updated_at',)
    list_filter = ('updated_at','status', 'active')

    def save_model(self, request, obj, form, change):
        # print(f"Saving {obj.name}. Change = {change}")
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.created_by = request.user
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)

# admin.site.register(CartItem)
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    search_fields = ('product__name',)
    readonly_fields = ('created_at','updated_at')
    fields = ('product', 'quantity', 'line_total', ('created_at','updated_at'))
    list_display = ('product', 'cart', 'quantity', 'line_total')
    list_filter = ('updated_at',)
    ordering = ('product__name',)

    def save_model(self, request, obj, form, change):
        # print(f"Saving {obj.name}. Change = {change}")
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.created_by = request.user
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)