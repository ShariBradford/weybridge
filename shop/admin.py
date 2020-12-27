from django.contrib import admin
from .models import *

# admin.site.register(Product)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    fields = ('name', 'description', ('sku', 'inventory_stock'), 'categories', ('price', 'is_on_sale', 'get_sale_price'), 'collection','size_chart','active', 'get_default_photo_url')
    # fields = ('name', 'description', ('sku','inventory_stock'), 'price', 'categories', 'collection','size_chart','active')
    date_hierarchy = 'created_at'
    filter_horizontal = ('categories',)
    readonly_fields = ('created_by','created_at','updated_by','updated_at', 'is_on_sale', 'get_sale_price', 'get_default_photo_url')
    search_fields = ('name','description','sku')
    list_display = ('name', 'get_default_photo_url','sku', 'price', 'is_on_sale', 'get_sale_price', 'inventory_stock','active')

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
    fields = ('product', ('sale_price', 'get_retail_price'), ('start_date', 'end_date'), ('created_by','created_at'), ('updated_by','updated_at'))
    list_filter = ('start_date', 'end_date')

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
    list_display = ('product','number_of_stars', 'user', 'created_at')
    fields = ('product','number_of_stars', ('user', 'created_at'),('updated_by','updated_at'))
    list_filter = ('number_of_stars', 'created_at')
    ordering = ('product__name',)

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
    fields = (('user__first_name','user__last_name'),'user__email', 'bio', 'location', 'profile_pic')
    search_fields = ('bio','location','user__first_name','user__last_name','user__email')
    list_display = ('user', 'profile_pic', 'location')
    read_only_fields = ('user__first_name','user__last_name', 'user__email')

# admin.site.register(Answer)
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    fields = ('question','content', 'get_product', ('answerer','date_answered'),('updated_by','updated_at'))
    readonly_fields = ('answerer','date_answered','updated_by','updated_at', 'get_product')
    search_fields = ('question__content','content','answerer__first_name', 'answerer__last_name', 'question__product__name')
    date_hierarchy = 'date_answered'
    autocomplete_fields = ('question',)
    list_display = ('get_product', 'content', 'answerer','date_answered')
    list_filter = ('date_answered',)
    ordering = ('question__product__name',)
    link_fields = ('content', 'date_answered')

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

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2

# admin.site.register(Question)
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fields = ('content','asker','product','date_asked')
    readonly_fields = ('date_asked',)
    search_fields = ('content','asker__first_name','asker__last_name','product__name')
    date_hierarchy = 'date_asked'
    inlines = [AnswerInline]
    list_display = ('product', 'content','asker','date_asked')
    ordering = ('product__name', 'date_asked')
    list_filter = ('date_asked',)

# admin.site.register(Category)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ('name', 'parent_category','description', 'profile_pic', ('created_by','created_at'), ('updated_by','updated_at'))
    search_fields = ('name','description','parent_category__name')
    readonly_fields = ('created_by','updated_by','created_at','updated_at')
    autocomplete_fields = ('parent_category',)
    list_display = ('name', 'profile_pic','parent_category')
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

# admin.site.register(ProductPhoto)
@admin.register(ProductPhoto)
class ProductPhotoAdmin(admin.ModelAdmin):
    fields = ('product',('picture','is_default'))
    search_fields = ('product__name',)
    list_display = ('product','picture','is_default')

class CollectionProductInline(admin.StackedInline):
    model = Product
    extra = 1

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    fields = ('name', 'description', 'profile_pic', ('created_by','created_at'), ('updated_by','updated_at'))
    search_fields = ('name','description')
    readonly_fields = ('created_by','updated_by','created_at','updated_at', 'get_number_of_products')
    list_display = ('name', 'profile_pic', 'get_number_of_products')
    ordering = ('name',)
    # inlines = [CollectionProductInline]

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

admin.site.register(Sale)