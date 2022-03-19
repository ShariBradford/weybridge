from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone 
from django.utils.translation import ngettext

from .models import *

class ProductIsOnSaleListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Sale Status'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_on_sale'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('true', 'On Sale'),
            ('false', 'Not On Sale'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'true':
            return queryset.filter(promotions__sale__start_date__lte=date.today(),
                promotions__sale__end_date__gte=date.today()
            )
        elif self.value() == 'false':
            filter_conditions = (Q(promotions__isnull=True)) | (Q(promotions__sale__start_date__gt=date.today())) | (Q(promotions__sale__end_date__lt=date.today()))
            return queryset.filter(filter_conditions).distinct()

class ProductIsNewListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'New Status'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_new'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('true', 'New'),
            ('false', 'Not New'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'true':
            return queryset.filter(created_at__gte=timezone.now() + timedelta(days=-30))
        elif self.value() == 'false':
            return queryset.filter(created_at__lt=timezone.now() + timedelta(days=-30))

# admin.site.register(Product)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    fields = ('name', 'description', ('sku', 'inventory_stock'), 'categories', ('price', 'is_on_sale', 'get_sale_price'), 'collection','size_chart','active', 'get_default_photo_url')
    date_hierarchy = 'created_at'
    filter_horizontal = ('categories',)
    readonly_fields = ('created_by','created_at','updated_by','updated_at', 'is_on_sale', 'get_sale_price', 'get_default_photo_url')
    search_fields = ('name','description','sku')
    list_display = ('name', 'get_average_rating', 'sku', 'price', 'is_on_sale', 'get_sale_price', 'inventory_stock','active', 'get_default_photo_url', 'size_chart')
    list_filter = ('active', ProductIsOnSaleListFilter,ProductIsNewListFilter)
    actions = ['mark_inactive']

    def mark_inactive(self, request, queryset):
        updated = queryset.update(active = False)
        self.message_user(
            request, 
            ngettext(
                f"{updated} item successfully marked as inactive.", 
                f"{updated} items successfully marked as inactive.", 
                updated
            ),
            level=messages.SUCCESS, 
            extra_tags='', 
            fail_silently=True
        )
        for obj in queryset:
            admin.ModelAdmin.log_change(self,request, obj, f"Marked inactive: '{str(obj)}'")
    mark_inactive.short_description='Mark selected items inactive'

    def save_model(self, request, obj, form, change):
        print(f"Saving {obj.name}. Change = {change}")
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.created_by = request.user
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)

        # add the default photo
        if not hasattr(object,"product_photos"):
            i = ProductPhoto(product=obj)
            i.save()

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    fields = ('name', 'promo_code', 'description', 'terms', ('start_date', 'end_date'), 'profile_pic', ('created_by','created_at'), ('updated_by','updated_at'))
    date_hierarchy = 'start_date'
    readonly_fields = ('created_by','created_at','updated_by','updated_at')
    search_fields = ('name','promo_code', 'description')
    list_display = ('name', 'profile_pic','promo_code', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')

    def save_model(self, request, obj, form, change):
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.created_by = request.user
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_date'
    readonly_fields = ('get_retail_price','created_by','created_at','updated_by','updated_at')
    search_fields = ('product',)
    list_display = ('product', 'sale', 'sale_price', 'get_retail_price', 'start_date', 'end_date')
    autocomplete_fields = ('product',)
    # fields = ('product', ('sale_price', 'get_retail_price'), ('start_date', 'end_date'), ('created_by','created_at'), ('updated_by','updated_at'))
    list_filter = ('sale__start_date', 'sale__end_date', ('sale', RelatedOnlyFieldListFilter)) # Note from docs: The FieldListFilter API is considered internal and might be changed

    fieldsets = (
        (None, {'fields': ('product',) }),
        ('Sale Info', {
            'fields': ('sale', ('sale_price', 'get_retail_price')),
        }),
        ('History', {
            'fields': (('created_by','created_at'), ('updated_by','updated_at')),
        }),
    )


    def save_model(self, request, obj, form, change):
        if change:
            # user is updating item 
            obj.updated_by = request.user
        else:
            # user is creating item
            obj.created_by = request.user
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)

# admin.site.register(Rating)
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    radio_fields = {"number_of_stars": admin.HORIZONTAL}
    search_fields = ('review','product__name','user__username')
    readonly_fields = ('user','created_at','updated_by','updated_at')
    autocomplete_fields = ('product',)
    list_display = ('product','number_of_stars', 'user', 'created_at')
    fields = ('product','number_of_stars', ('user', 'created_at'),('updated_by','updated_at'))
    list_filter = ('number_of_stars', 'created_at')
    ordering = ('product__name',)
    date_hierarchy = 'created_at'

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
    date_hierarchy = 'created_at'
    search_fields = ('bio','location','user__first_name','user__last_name','user__email')
    list_display = ('user', 'get_user_fullname', 'profile_pic', 'location', 'time_zone', 'one_click_purchasing',)
    readonly_fields = ('created_at','updated_at', 'get_user_fullname', 'get_user_email', 'id', 'user_id', )
    list_filter = ('one_click_purchasing',)

    fieldsets = (
        ('Associated User', {'fields': (('get_user_fullname', 'user_id'),'get_user_email',) }),
        ('Profile Details', {
            'fields': ('bio', 'location', 'profile_pic', 'id',),
        }),
        ('Favorites', {
            'fields': ('favorites', ),
        }),
        ('History', {
            'fields': ('created_at','updated_at'),
        }),
    )


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
    fields = ('content','asker','product','date_asked','followers')
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

# admin.site.register(Sale)

# admin.site.register(Contact)
@admin.register(Contact)
class CategoryAdmin(admin.ModelAdmin):
    fields = ('from_email', 'subject','message', ('created_at', 'updated_at'))
    search_fields = ('from_email','message','subject')
    readonly_fields = ('created_at','updated_at')
    list_display = ('from_email', 'subject','message', 'created_at')
    ordering = ('created_at',)
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

    # def save_model(self, request, obj, form, change):
    #     # print(f"Saving {obj.name}. Change = {change}")
    #     if change:
    #         # user is updating item 
    #         obj.updated_by = request.user
    #     else:
    #         # user is creating item
    #         obj.created_by = request.user
    #         obj.updated_by = request.user

    #     super().save_model(request, obj, form, change)

