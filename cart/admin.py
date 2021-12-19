from django.contrib import admin, messages
from django.utils.translation import ngettext
from .models import *

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

    # Don't allow cart items to be created, updated or deleted in the cart admin view
    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

# admin.site.register(Cart)
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ('user__first_name','user__last_name')
    readonly_fields = ('created_by','updated_by','created_at','updated_at')
    list_display = ('user', 'item_count', 'total', 'status', 'active', 'updated_at', 'id')
    fields = ('user', ('item_count', 'total'), ('status', 'active'), ('created_by','created_at'),('updated_by','updated_at'))
    ordering = ('-updated_at',)
    list_filter = ('updated_at','status', 'active')
    actions = ['mark_expired']
    inlines = [CartItemInline]

    def mark_expired(self, request, queryset):
        updated = queryset.update(status = Cart.STATUS_EXPIRED)
        self.message_user(
            request, 
            ngettext(
                f"{updated} item successfully marked as expired.", 
                f"{updated} items successfully marked as expired.", 
                updated
            ),
            level=messages.SUCCESS, 
            extra_tags='', 
            fail_silently=True
        )
        for obj in queryset:
            self.log_change(request, obj, f"Marked expired: '{str(obj)}'")
    mark_expired.short_description='Mark selected items expired'

    def save_model(self, request, obj, form, change):
        # print(f"Saving {obj.name}. Change = {change}")
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.created_by = request.user
            obj.updated_by = request.user

        obj.item_count = obj.get_item_count(request.user)

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

        # THIS DOES NOT WORK 
        print('Refreshing cart.')
        obj.cart.refresh_cart(request.user)