from django.contrib import admin
from .models import *

# admin.site.register(Product)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    filter_horizontal = ('categories',)
    readonly_fields = ('created_by','created_at','updated_by','updated_at')
    search_fields = ('name','description','sku')
    list_display = ('name', 'sku', 'price', 'is_on_sale', 'get_sale_price', 'inventory_stock','active')

    def save_model(self, request, obj, form, change):
        print(f"Saving {obj.name}. Change = {change}")
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.created_by = request.user
            obj.updated_by = request.user

        super(ProductAdmin,self).save_model(request, obj, form, change)

        # add the default photo
        if not hasattr(object,"product_photos"):
            i = ProductPhoto(product=obj)
            i.save()

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_date'
    readonly_fields = ('get_retail_price','created_by','created_at','updated_by','updated_at')
    search_fields = ('product',)
    list_display = ('product', 'sale_price', 'get_retail_price', 'start_date', 'end_date')
    autocomplete_fields = ('product',)
    fields = ('product', 'get_retail_price', 'sale_price', 'start_date', 'end_date')

    def save_model(self, request, obj, form, change):
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.created_by = request.user
            obj.updated_by = request.user

        super(PromotionAdmin,self).save_model(request, obj, form, change)

# admin.site.register(Rating)
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    radio_fields = {"number_of_stars": admin.HORIZONTAL}
    search_fields = ('review','product__name')
    readonly_fields = ('user','created_at','updated_by','updated_at')
    autocomplete_fields = ('product',)

    def save_model(self, request, obj, form, change):
        # print(f"Saving {obj.name}. Change = {change}")
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.user = request.user
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)

# admin.site.register(UserProfile)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ('bio','location','user__first_name','user__last_name','user__email')

# admin.site.register(Answer)
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    fields = ('question','content','answerer','date_answered','updated_by','updated_at')
    readonly_fields = ('answerer','date_answered','updated_by','updated_at')
    search_fields = ('question','content','answerer__first_name','answerer__last_name','product__name')
    date_hierarchy = 'date_answered'
    autocomplete_fields = ('question',)

    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ('question',)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        # print(f"Saving {obj.name}. Change = {change}")
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.answerer = request.user
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)

# admin.site.register(Question)
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fields = ('content','asker','product','date_asked')
    readonly_fields = ('date_asked',)
    search_fields = ('content','asker__first_name','asker__last_name','product__name')
    date_hierarchy = 'date_asked'

# admin.site.register(Category)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name','description','parent_category__name')
    readonly_fields = ('created_by','updated_by','created_at','updated_at')
    autocomplete_fields = ('parent_category',)
    list_display = ('name','parent_category')
    ordering = ('parent_category__name','name')
    list_filter = ('parent_category',)

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

admin.site.register(ProductPhoto)
