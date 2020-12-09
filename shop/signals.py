from django.db.models.signals import post_save
from django.contrib.auth.models import User
from .models import UserProfile,Product,ProductPhoto
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, **kwargs):
    user = kwargs["instance"]
    print(f'USER BEING SAVED: {user.first_name}')
    if kwargs["created"]:
        profile = UserProfile(user=user)
        profile.save()

# @receiver(post_save, sender=Product)
# def create_default_product_photo(sender, **kwargs):
#     product = kwargs["instance"]
#     print(f'Product: {product.name}')
#     if product.product_photos.count() < 1 and kwargs["created"]:
#         photo = ProductPhoto(product=product)
#         photo.save()