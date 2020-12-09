from django.db import models
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.conf import settings
from datetime import datetime, date, timedelta
from django.db.models import Avg, UniqueConstraint
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils import timezone 
from django.shortcuts import reverse
# from django.utils import unique_slug_generator
import math
import string 
import random 

def random_string_generator(size = 10, chars = string.ascii_lowercase + string.digits): 
    return ''.join(random.choice(chars) for _ in range(size)) 
  
def unique_slug_generator(instance, new_slug = None): 
    if new_slug is not None: 
        slug = new_slug 
    else: 
        slug = slugify(instance.first_name) 
    Klass = instance.__class__ 
    qs_exists = Klass.objects.filter(slug = slug).exists() 
      
    if qs_exists: 
        new_slug = "{slug}-{randstr}".format( 
            slug = slug, randstr = random_string_generator(size = 4)) 
              
        return unique_slug_generator(instance, new_slug = new_slug) 
    return slug 

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
    updated_by = models.ForeignKey(User,related_name="categories_updated", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User,related_name="categories_created", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "categories"
        ordering: "name"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:category_details',kwargs={'pk': self.id})

class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'profile_pic','parent_category','description']
        widgets = {
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control-file',}),
            'name' : forms.TextInput(attrs={'class':'form-control'}),
            'parent_category' : forms.Select(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
       }        

def product_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/dish_<id>/<filename>
    return 'product_{0}/size_chart_'.format(instance.id, filename)

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="Description coming soon!", help_text="Describe the product, its history and why you were inspired to make it.")
    sku = models.CharField(max_length=50)
    categories = models.ManyToManyField(Category, related_name='products', help_text="Select all categories that apply.")
    price = models.FloatField()
    inventory_stock = models.IntegerField(default=0)
    user_likes = models.ManyToManyField(User, blank=True, null=True, related_name='liked_products')
    # slug = models.SlugField(max_length = 250, null = True, blank = True)
    size_chart = models.FileField(
        upload_to=product_directory_path, 
        blank=True,
        null=True,
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User,related_name="products_updated", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User,related_name="products_created", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    # def save(self, *args, **kwargs):
    #     self.slug = self.slug or unique_slug_generator(self) #slugify(self.title)
    #     super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:product_details',kwargs={'pk': self.id})

    def get_average_rating(self):
        average = self.ratings.aggregate(Avg('number_of_stars'))['number_of_stars__avg'] or 0
        # return math.ceil(average)
        return average

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

    def is_new(self):
        return self.created_at >= timezone.now() + timedelta(days=-30) 
    is_new.boolean = True

    def is_on_sale(self):
        return self.promotions.filter(
            start_date__lte=date.today(),
            end_date__gte=date.today()
        ).count() > 0
    is_on_sale.boolean = True
    
    def get_sale_price(self):
        if self.is_on_sale():
            return self.promotions.filter(
                start_date__lte=date.today(),
                end_date__gte=date.today()
            ).order_by('-sale_price').first().sale_price
        else:
            return self.price

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'sku', 'price', 'categories','inventory_stock']
        widgets = {
            'name' : forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'sku' : forms.TextInput(attrs={'class':'form-control'}),
            'price' : forms.TextInput(attrs={'class':'form-control'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'inventory_stock' : forms.TextInput(attrs={'class':'form-control'}),
       }

class ProductFormWithImages(ProductForm):
    images = forms.ImageField(
        required=False, 
        help_text="Upload up to 10 images.",
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'form-control-file',
                'multiple':True
            }
        )
    )

    class Meta(ProductForm.Meta):
        fields = ['images','name', 'description', 'sku', 'price', 'categories','inventory_stock']
    
class Promotion(models.Model):
    product = models.ForeignKey(Product, related_name='promotions', on_delete=models.CASCADE)
    sale_price = models.FloatField()
    start_date = models.DateField(null=True,blank=True, default=date.today)
    end_date = models.DateField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User,related_name="promotions_updated", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User,related_name="promotions_created", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.name} on sale for {self.sale_price}"

    def get_retail_price(self):
        return self.product.price

    def get_absolute_url(self):
        return reverse('shop:promotion_details',kwargs={'pk': self.id})

class PromotionForm(ModelForm):
    class Meta:
        model = Promotion
        fields = ['product', 'sale_price', 'start_date', 'end_date']
        widgets = {
            'product' : forms.Select(attrs={'class':'form-control'}),
            'sale_price' : forms.TextInput(attrs={'class':'form-control'}),
            'start_date' : forms.TextInput(attrs={'class':'form-control'}),
            'end_date' : forms.TextInput(attrs={'class':'form-control'}),
       }

class Rating(models.Model):
    RATING_CHOICES = (
        (1, 'It was awful!'),
        (2, 'Not so great.'),
        (3, 'Just Ok.'),
        (4, 'I liked it!'),
        (5, 'Pretty freakin awesome!')
    )
    product = models.ForeignKey(Product,related_name="ratings", on_delete=models.CASCADE)
    user = models.ForeignKey(User,related_name="ratings", on_delete=models.CASCADE)
    number_of_stars = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    updated_by = models.ForeignKey(User,related_name="ratings_updated", on_delete=models.CASCADE)

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
    user = models.ForeignKey(User,related_name="votes", on_delete=models.CASCADE, blank=True, null=True)
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
    asker = models.ForeignKey(User,related_name="questions_asked", on_delete=models.CASCADE)
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
    answerer = models.ForeignKey(User,related_name="product_answers", null=True, blank=True, on_delete=models.CASCADE)
    date_answered = models.DateField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    updated_by = models.ForeignKey(User,related_name="answers_updated", on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.content}'

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
    # file will be uploaded to MEDIA_ROOT/product_<id>/<filename>
    return 'products/product_{0}/{1}'.format(instance.product_id, filename)

class ProductPhoto(models.Model):
    product = models.ForeignKey(Product, related_name='product_photos', on_delete=models.CASCADE)
    picture = models.ImageField(
        upload_to=product_photos_directory_path, 
        default= 'products/blank-product.jpg',
        blank=True,
        null=True,
        )
    is_default = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} (ID={self.id})"

class ProductPhotoForm(ModelForm):
    class Meta:
        model = ProductPhoto
        fields = ['picture','is_default']
        widgets = {
            'picture': forms.ClearableFileInput(attrs={'class': 'form-control-file',}),
            'is_default' : forms.CheckboxInput(attrs={'class':'form-control'}),
       }        

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'users/user_{0}/{1}'.format(instance.id, filename)

class UserProfile(models.Model):
    profile_pic = models.ImageField(
        upload_to= user_directory_path, 
        default= 'users/blank-user.jpg',
        blank=True,
        null=True,
        )
    bio = models.TextField(blank=True, null=True, help_text="Tell us about yourself!")
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    location = models.CharField(blank=True, null=True,max_length=50)
    birthday = models.DateField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        # pylint: disable=E1101
        return f'{self.user.get_full_name()} Profile'

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'birthday', 'profile_pic']
        widgets = {
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control-file',}),
            'bio': forms.Textarea(attrs={'class': 'form-control'}),
            'location' : forms.TextInput(attrs={'class':'form-control'}),
            'birth_date': forms.DateTimeInput(attrs={'class': 'form-control'}),
       }