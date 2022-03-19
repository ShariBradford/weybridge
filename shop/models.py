from datetime import datetime, date, timedelta

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg, UniqueConstraint, Q, Count
from django.forms import ModelForm, ValidationError
from django.shortcuts import reverse
from django.utils import timezone 
from django.utils.text import slugify
# from django.utils import unique_slug_generator

import math
import random 
import string 

# def random_string_generator(size = 10, chars = string.ascii_lowercase + string.digits): 
#     return ''.join(random.choice(chars) for _ in range(size)) 
  
# def unique_slug_generator(instance, new_slug = None): 
#     """
#         Generates a unique slug for an item in a class.
#     """

#     if new_slug is not None: 
#         slug = new_slug 
#     else: 
#         slug = slugify(instance.first_name) 
#     Klass = instance.__class__ 
#     qs_exists = Klass.objects.filter(slug = slug).exists() 
      
#     if qs_exists: 
#         new_slug = "{slug}-{randstr}".format( 
#             slug = slug, randstr = random_string_generator(size = 4)) 
              
#         return unique_slug_generator(instance, new_slug = new_slug) 
#     return slug 

class AbstractHistoryModel(models.Model):
    """
    Abstract model that provides history information (created_at, updated_at, created_by, updated_by).
    This ensures that any model based on this abstract model can automate saving of history information 
    because the fields required for this will always be present and named consistently.
    """
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="%(class)ss_updated", on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="%(class)ss_created", on_delete=models.CASCADE)

    class Meta:
        abstract = True

class Category(models.Model):   
    name = models.CharField(max_length=20)
    parent_category = models.ForeignKey("self",related_name="child_categories", blank=True, null=True, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField( 
        upload_to='categories/', 
        default= 'categories/blank-category.jpg',
        blank=True,
        null=True,
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="categories_updated", on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="categories_created", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "categories"
        ordering= ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:category_details',kwargs={'pk': self.id})

class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'profile_pic','parent_category','description']
        widgets = {
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control-file','data-single-image': 'true'}),
            'name' : forms.TextInput(attrs={'class':'form-control'}),
            'parent_category' : forms.Select(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
       }        

class Collection(AbstractHistoryModel):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True, default="Description coming soon!")
    profile_pic = models.ImageField( 
        upload_to='collections/', 
        default= 'collections/blank-collection.jpg',
        blank=True,
        null=True,
        )
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)
    # updated_by = models.ForeignKey(User,related_name="collections_updated", on_delete=models.CASCADE)
    # created_by = models.ForeignKey(User,related_name="collections_created", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "collections"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:collection_details',kwargs={'pk': self.id})

    def get_number_of_products(self):
        return self.products.count()
    get_number_of_products.short_description = "# Products"

class CollectionForm(ModelForm):
    class Meta:
        model = Collection
        fields = ['profile_pic', 'name', 'description']
        widgets = {
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control-file','data-single-image': 'true',}),
            'name' : forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
       }        

def product_directory_path(instance, filename):
    """
        Given product instance, returns path where size chart file should be uploaded 
        (MEDIA_ROOT/product_<id>/size_chart_<filename>).
    """

    return f'product_{instance.id}/size_chart_{filename}'

class Product(AbstractHistoryModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="Description coming soon!", help_text="Describe the product, its history and why you were inspired to make it.")
    sku = models.CharField(max_length=50)
    categories = models.ManyToManyField(Category, related_name='products', help_text="Select all categories that apply.")
    price = models.DecimalField(max_digits=10,decimal_places=2)
    inventory_stock = models.IntegerField(default=0)
    collection = models.ForeignKey(Collection,related_name="products", blank=True, null=True, on_delete=models.SET_NULL)
    size_chart = models.FileField(
        upload_to=product_directory_path, 
        blank=True,
        null=True,
    )
    active = models.BooleanField(default=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)
    # updated_by = models.ForeignKey(User,related_name="products_updated", on_delete=models.CASCADE)
    # created_by = models.ForeignKey(User,related_name="products_created", on_delete=models.CASCADE)
    # slug = models.SlugField(max_length = 250, null = True, blank = True)

    def __str__(self):
        return self.name

    # def save(self, *args, **kwargs):
    #     from .services import unique_slug_generator
    
    #     self.slug = self.slug or unique_slug_generator(self) #slugify(self.title)
    #     super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:product_details',kwargs={'pk': self.id})

    def get_average_rating(self):
        average = self.ratings.aggregate(Avg('number_of_stars'))['number_of_stars__avg'] or 0
        # return math.ceil(average)
        return average
    get_average_rating.short_description = "Average Rating"

    def get_ratings_with_votes(self):
        upvotes = Count('votes__score_type', filter=Q(votes__score_type=1))
        downvotes = Count('votes__score_type', filter=Q(votes__score_type=-1))
        return self.ratings.annotate(upvotes=upvotes).annotate(downvotes=downvotes).order_by('-created_at')       
    get_ratings_with_votes.short_description = "Ratings"

    def get_default_photo_url(self):
        default_photo = self.product_photos.filter(is_default=True).first()
        first_photo = self.product_photos.first()
        # model_default = self.product_photos.__class__.__name__._meta.get_field('profile_pic').get_default()
        model_default = ProductPhoto._meta.get_field('picture').get_default()

        if default_photo:
            # print(f"Photo for {self.name}: (primary) {default_photo.picture.url}")
            return default_photo.picture.url
        elif first_photo:
            # print(f"Photo for {self.name}: (first) {first_photo.picture.url}")
            return first_photo.picture.url
        else:
            # print(f"Photo for {self.name}: (model default) {model_default}")
            return f"{settings.MEDIA_URL}{model_default}"
        # return default_photo or first_photo or model_default or None
    get_default_photo_url.short_description = "Default Photo"

    def is_new(self):
        return self.created_at >= timezone.now() + timedelta(days=-30) 
    is_new.boolean = True
    is_new.short_description = 'New?'

    def is_on_sale(self):
        """
            Checks if product is on sale based on the sale start and end dates 
            for any of the product's promotions.
        """

        return self.promotions.filter(
            sale__start_date__lte=date.today(),
            sale__end_date__gte=date.today()
        ).count() > 0
    is_on_sale.boolean = True
    is_on_sale.short_description = 'On Sale?'

    def get_sale_price(self):
        """
            Returned the sale price of the product by filtering active promotions.
            Promotions are ordered by sale_price ascending, and the first (lowest) price 
            is returned.
        """

        if self.is_on_sale():
            return self.promotions.filter(
                sale__start_date__lte=date.today(),
                sale__end_date__gte=date.today()
            ).order_by('sale_price').first().sale_price
        else:
            return self.price
    get_sale_price.short_description = 'Sale Price'
    get_sale_price.admin_order_field = 'price'

    def get_promotion(self):
        """
            Returns the lowest price promotion by filtering product's active promotions.
            Promotions are ordered by sale_price ascending, and the first (lowest) price 
            promotion is returned.
        """        
        
        if self.is_on_sale():
            return self.promotions.filter(
                sale__start_date__lte=date.today(),
                sale__end_date__gte=date.today()
            ).order_by('sale_price').first()
        else:
            return None
    get_promotion.short_description = 'Promotion'
    get_promotion.admin_order_field = 'price'

    def get_sale(self, include_description=False, include_promo_code=False):
        """
            Returns the sale associated with the lowest price active promotion.
            Promotions are ordered by sale_price ascending, and the first (lowest) price 
            promotion is returned. Returns name of sale and (optionally) description and promo code.
        """        

        return_val = None

        if self.is_on_sale():
            # sale = self.promotions.filter(
            #     sale__start_date__lte=date.today(),
            #     sale__end_date__gte=date.today()
            # ).order_by('sale_price').first().sale
            promotion = self.get_promotion()
            if promotion:
                sale = promotion.sale
                return_val = sale

                if include_description and sale.description:
                    return_val = f"{sale.name}: {sale.description}"

                if include_promo_code and sale.promo_code:
                    return_val = f"{return_val} (with promo code {sale.promo_code.upper()})" 

        return return_val
    get_sale.short_description = 'Sale'
    get_sale.admin_order_field = 'name'

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'sku', 'price', 'categories', 'collection','inventory_stock','size_chart','active']
        widgets = {
            'name' : forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'sku' : forms.TextInput(attrs={'class':'form-control'}),
            'price' : forms.TextInput(attrs={'class':'form-control'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'collection' : forms.Select(attrs={'class':'form-control'}),
            'inventory_stock' : forms.TextInput(attrs={'class':'form-control'}),
            'size_chart': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'active' : forms.CheckboxInput(attrs={'class':'form-check-input'}),
       }

class ProductFormWithImages(ProductForm):
    images = forms.ImageField(
        required=False, 
        help_text="Upload up to 10 images.",
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'form-control-file',
                'multiple':True,
                'data-multiple-image':"true",
            }
        )
    )

    class Meta(ProductForm.Meta):
        fields = ['images','name', 'collection', 'description', 'sku', 'price', 'categories','inventory_stock','size_chart','active']
    
def sale_directory_path(instance, filename):
    """
        Given sale instance, returns path where file should be uploaded 
        (MEDIA_ROOT/sales/sale_<id>/<sale_name>).
    """

    return f'sales/sale_{instance.id}/{instance.name}'

class Sale(AbstractHistoryModel):
    name = models.CharField(max_length=255, default='Sale')
    start_date = models.DateField(null=True,blank=True, default=date.today)
    end_date = models.DateField(null=True,blank=True)
    description = models.CharField(max_length=255, blank=True, null=True, default='Description coming soon!')
    promo_code = models.CharField(max_length=20, null=True, blank=True, help_text="Try to keep the code short (under 10 characters).")
    terms = models.TextField(blank=True, null=True, default='Terms coming soon.')
    profile_pic = models.ImageField( 
        upload_to=sale_directory_path, 
        default= 'sales/blank-sale.jpg',
        blank=True,
        null=True,
        )
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)
    # updated_by = models.ForeignKey(User,related_name="sales_updated", on_delete=models.CASCADE)
    # created_by = models.ForeignKey(User,related_name="sales_created", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "sales"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse('shop:sale_details',kwargs={'pk': self.id})

    def has_ended(self):
        return self.end_date < date.today()
    has_ended.boolean = True
    has_ended.short_description = 'Ended?'

    def get_info(self, include_description=False, include_promo_code=False):
        return_val = self.name

        if include_description and self.description:
            return_val = f"{self.name}: {self.description}"

        if include_promo_code and self.promo_code:
            return_val = f"{return_val} (with promo code {self.promo_code.upper()})" 

        return return_val
    get_info.short_description = 'Sale Info'
    get_info.admin_order_field = 'name'
    
class SaleForm(ModelForm):
    class Meta:
        model = Sale
        fields = ['profile_pic', 'name', 'promo_code', 'description', 'terms', 'start_date', 'end_date']
        widgets = {
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control-file','data-single-image':'true'}),
            'name' : forms.TextInput(attrs={'class':'form-control'}),
            'promo_code' : forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'terms': forms.Textarea(attrs={'class': 'form-control'}),
            'start_date' : forms.TextInput(attrs={'class':'form-control'}),
            'end_date' : forms.TextInput(attrs={'class':'form-control'}),
       }

class Promotion(AbstractHistoryModel):
    name = models.CharField(max_length=255, default='Sale')
    sale = models.ForeignKey(Sale, related_name='promotions', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='promotions', on_delete=models.CASCADE)
    sale_price = models.DecimalField(max_digits=10,decimal_places=2)
    start_date = models.DateField(null=True,blank=True, default=date.today)
    end_date = models.DateField(null=True,blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)
    # updated_by = models.ForeignKey(User,related_name="promotions_updated", on_delete=models.CASCADE)
    # created_by = models.ForeignKey(User,related_name="promotions_created", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.name} on sale for {self.sale_price}"

    def get_absolute_url(self):
        return reverse('shop:promotion_details',kwargs={'pk': self.id})

    def get_retail_price(self):
        return self.product.price
    get_retail_price.short_description = "Retail Price"

class PromotionForm(ModelForm):
    class Meta:
        model = Promotion
        fields = ['product', 'sale', 'sale_price']
        widgets = {
            'sale' : forms.Select(attrs={'class':'form-control'}),
            'product' : forms.Select(attrs={'class':'form-control'}),
            'sale_price' : forms.TextInput(attrs={'class':'form-control'}),
        }

    def clean(self):
        super(PromotionForm,self).clean()
        # errors_dict = {}
        if 'product' in self.cleaned_data:
            product = self.cleaned_data['product']
        else: 
            product = None

        if 'sale' in self.cleaned_data:
            sale = self.cleaned_data['sale']
        else: 
            sale = None

        if product and self.cleaned_data['sale_price'] > product.price:
            # errors_dict['sale_price'] = ValidationError("Sale price should be less than retail price.")
            self.add_error('sale_price', "Sale price should be less than retail price.")

        # if this is a new item or if user is updating sale selected, make sure it's not a duplicate of another promotion
        if sale and product:
            if self.instance.pk == None or (product != self.instance.product) or (sale != self.instance.sale):            
                if sale.promotions.filter(product_id=product).exists():
                    # errors_dict['NON_FIELD_ERRORS'] = ValidationError(f"A promotion with this product is already part of the sale '{sale.name}'. Select another sale or another product.")
                    self.add_error(None, f"A promotion with this product is already part of the sale '{sale.name}'. Select another sale or another product.")

class Rating(models.Model):
    RATING_CHOICES = (
        (1, 'It was awful!'),
        (2, 'Not so great.'),
        (3, 'Just Ok.'),
        (4, 'I liked it!'),
        (5, 'Pretty freakin awesome!')
    )
    product = models.ForeignKey(Product,related_name="ratings", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="ratings", on_delete=models.CASCADE)
    number_of_stars = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name = 'Rating',
    )
    review = models.CharField(max_length=255, null=True, blank=True, help_text="Let other shoppers know what you liked, or didn't, about this purchase.")
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="ratings_updated", on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.number_of_stars} star rating for {self.product}'

    # def user_has_voted(self):
    #     return False
        
    # user_has_vote.boolean = True 

class RatingForm(ModelForm):
    class Meta:
        model = Rating
        fields = ['number_of_stars', 'review', ]
        labels = {
            'number_of_stars': 'Rating',
        }
        widgets = {
            'number_of_stars': forms.RadioSelect(attrs={'class': 'form-check-inline d-flex flex-wrap'}),
            'review': forms.Textarea(attrs={'class': 'form-control'}),
       }

class RatingVote(models.Model):
    SCORE_CHOICES = (
        (-1, 'down_vote'),
        (1, 'up_vote'),
    )
    rating = models.ForeignKey(Rating,related_name="votes", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="votes", on_delete=models.CASCADE, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    score_type = models.SmallIntegerField(choices=SCORE_CHOICES)
    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        UniqueConstraint (
            fields=['user','ip_address','rating'],
            name='unique_vote',
        ) 

class Question(models.Model):
    #id INT
    content = models.CharField(max_length=255)
    asker = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="questions_asked", on_delete=models.CASCADE)
    followers = models.ManyToManyField(User, blank=True, null=True, related_name='questions_followed')
    # answers = models.ForeignKey(Answer, related_name='question', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product,related_name="questions", on_delete=models.CASCADE)
    date_asked = models.DateField(auto_now_add=True,null=True,blank=True)

    def __str__(self):
        return f'{self.content}'

class QuestionForm(ModelForm):
    class Meta:
        model = Question
        fields = ['content']
        labels = {
            'content': 'Question',
        }
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control'}),
       }

class Answer(models.Model):
    #id INT
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE, null=True, blank=True)
    content = models.CharField(max_length=255)
    answerer = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="product_answers", null=True, blank=True, on_delete=models.CASCADE)
    date_answered = models.DateField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,related_name="answers_updated", on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.content}'

    def get_product(self):
        return self.question.product
    get_product.short_description = 'Product'
    # get_product.admin_order_field = 'question__product'

class AnswerForm(ModelForm):
    class Meta:
        model = Answer
        fields = ['content']
        labels = {
            'content': 'Answer',
        }
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control'}),
       }

def product_photos_directory_path(instance, filename):
    """
        Given product_photo instance, returns path where image should be uploaded 
        (MEDIA_ROOT/products/product_<id>/<filename>).
    """

    return 'products/product_{0}/{1}'.format(instance.product_id, filename)

class ProductPhoto(models.Model):
    product = models.ForeignKey(Product, related_name='product_photos', on_delete=models.CASCADE)
    picture = models.ImageField(
        upload_to=product_photos_directory_path, 
        default= 'products/blank-product.jpg',
        blank=True,
        null=True,
        )
    is_default = models.BooleanField(default=False, verbose_name="Default?")
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} (ID={self.id})"

    def get_absolute_url(self):
        return self.picture.url

class ProductPhotoForm(ModelForm):
    class Meta:
        model = ProductPhoto
        fields = ['picture','is_default']
        widgets = {
            'picture': forms.ClearableFileInput(attrs={'class': 'form-control-file',}),
            'is_default' : forms.CheckboxInput(attrs={'class':'form-control'}),
       }        

def user_directory_path(instance, filename):
    """
        Given user_profile instance, returns path where profile photo should be uploaded 
        (MEDIA_ROOT/users/user_<id>/<filename>).
    """

    return 'users/user_{0}/{1}'.format(instance.id, filename)

class UserProfile(models.Model):
    profile_pic = models.ImageField(
        upload_to= user_directory_path, 
        default= 'users/blank-user.jpg',
        blank=True,
        null=True,
        )
    bio = models.TextField(blank=True, null=True, help_text="Tell us about yourself!")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', on_delete=models.CASCADE)
    location = models.CharField(blank=True, null=True,max_length=50)
    birthday = models.DateField(blank=True, null=True)
    favorites = models.ManyToManyField(Product, blank=True, null=True, related_name='favorited_by')
    time_zone = models.CharField(max_length=100, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)    
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        # pylint: disable=E1101
        return f'{self.user.get_full_name()} Profile'

    def get_absolute_url(self):
        print(f'Getting UserProfile URL for ID # {self.user_id}')
        print(reverse('accounts:user_profile',kwargs={'profiled_user_id': self.user_id}))

        return reverse('accounts:user_profile',kwargs={'profiled_user_id': self.user_id})
    
    def favorite(self, product):
        """Favorite `product`."""
        self.favorites.add(product)

    def unfavorite(self, product):
        """Unfavorite `product`."""
        self.favorites.remove(product)

    def has_favorited(self, product):
        """Returns True if we have favorited `product`; else False."""
        return self.favorites.filter(pk=product.pk).exists()

    def get_user_fullname(self):
        """Returns the full name of the User associated with the profile."""
        return self.user.get_full_name()
    get_user_fullname.short_description = 'Name'

    def get_user_email(self):
        """Returns the email address of the User associated with the profile."""
        return self.user.email
    get_user_email.short_description = 'Email'

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_pic', 'bio', 'location', 'birthday', 'time_zone','stripe_customer_id','one_click_purchasing',]
        widgets = {
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control-file','data-single-image': 'true',}),
            'bio': forms.Textarea(attrs={'class': 'form-control'}),
            'location' : forms.TextInput(attrs={'class':'form-control'}),
            'birth_date': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'time_zone': forms.TextInput(attrs={'class':'form-control'}),
            'stripe_customer_id': forms.TextInput(attrs={'class':'form-control'}),
            'one_click_purchasing': forms.CheckboxInput(attrs={'class':'form-check-input'}),
       }

class Contact(models.Model):
    from_email =  models.EmailField(max_length=150)
    message = models.TextField()
    subject = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Email from {self.from_email} on {self.created_at}'

class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = ['from_email','subject','message']
        widgets = {
            'from_email' : forms.TextInput(attrs={'class':'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control'}),
            'subject' : forms.TextInput(attrs={'class':'form-control'}),
        }
