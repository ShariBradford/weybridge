from datetime import datetime,timezone,timedelta

from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db.models import Value, IntegerField, CharField
from django.shortcuts import reverse
from django.utils.text import slugify

import random, requests, string

from .models import Category,Product,Rating,RatingForm

category_qs = Category.objects.all()
throw_away_var = len(category_qs)   #force evaluation of queryset

class RecentlyViewedItems(object):
    """
        Class that manages recently viewed products session variable
    """

    # maximum number of products to show in recently viewed list
    max = settings.SHOP_RECENTLY_VIEWED_MAX_ITEMS
    session_key = settings.SHOP_RECENTLY_VIEWED_SESSION_KEY

    @classmethod
    def get(cls, request):
        """
        Get a list of recently viewed product ids
        """
        
        # print(f"starting class method get. Looking for session key '{cls.session_key}'")
        try:
            recently_viewed = request.session[cls.session_key]
            # print(f"GET returned: {recently_viewed}")
            
            # make sure recently viewed is a proper list; if not, return empty list
            if not isinstance(recently_viewed, list):
                # print(f"Recently viewed is not a list. Returning empty list.")
                recently_viewed = []

        except KeyError:
            # session key is not in session; return empty list
            # print(f"Session key is not valid. Returning empty list.")
            recently_viewed = []

        return recently_viewed

    @classmethod
    def add(cls, recently_viewed_list, current_item_id,remove_current_item=True):
        """
        Add new item to recently viewed items
        """

        # print(f"starting class method add.")
        if current_item_id:
            if remove_current_item and current_item_id in recently_viewed_list:
                # print(f'This object ({current_item_id}) already in recently viewed items ({recently_viewed_list})')
                recently_viewed_list.remove(current_item_id)
                # print(f"Recent (after removing current item): {Product.objects.filter(id__in = recently_viewed_list)}")

            # insert this item at the front of the recently_viewed list
            recently_viewed_list.insert(0,current_item_id)
            # print(f"Recently viewed items (after adding current item): {recently_viewed_list}") # {Product.objects.filter(id__in = recently_viewed)}")

        if len(recently_viewed_list) > cls.max:
            # print(f'Too many items in recently viewed items ({len(recently_viewed_list)})')

            # check if recently_viewed has equal to or more than the maximum number of items
            # if so, delete the last one 
            del recently_viewed_list[-1]
            # print(f"Recent (after resizing list): {recently_viewed_list}")            

        return recently_viewed_list

    @classmethod
    def update(cls, request, current_item_id):
        """
        Add current_item_id to recently_viewed_list and save to session
        """
        # print(f"starting class method update. calling class method get.")
        recently_viewed_list = cls.get(request)
        # print(f"Class method get returned: {recently_viewed_list}")

        # print('Calling class method update.')
        updated_list = cls.add(recently_viewed_list,current_item_id) 
        # print(f"Class method update returned: {updated_list}")

        # print('Adding updated list to session')
        # Add updated recently viewed items list to the session variable
        request.session[cls.session_key] = updated_list
        # print(f'Session is now:{request.session[cls.session_key]}')

        return updated_list

    @classmethod
    def clear(cls,request):
        """
            Clear all items from recently_viewed_list in session
        """
        request.session[cls.session_key] = []
        # print(f"Recently viewed items: {request.session[cls.session_key]}")

def get_product_rating_for_user(user, object):   
    """
        Returns information about user's ratings for a particular product.
    """
 
    if hasattr(object,'ratings'):
        all_ratings = object.ratings.all()

        if user.is_authenticated == False:
            # user is anonymous, so user has not yet rated item yet
            user_has_rated_item = False
            user_rating_this_item = None
            form = RatingForm()

        # determine if this user has rated this item before
        elif all_ratings.filter(user=user).count() > 0:
            #user hsa rated item; don't permit another rating (just don't return a form object)
            # print(f"Ratings for {object}: {all_ratings.filter(user=user).count()}")
            user_has_rated_item = True
            user_rating_this_item = all_ratings.filter(user=user).first()
            form = None

        else:
            # user has not yet rated this item
            user_has_rated_item = False
            user_rating_this_item = None
            form = RatingForm()

    else:
        # object has no ratings yet or object is not a product 
        print(f"No ratings yet for {object}.")
        user_has_rated_item = False
        user_rating_this_item = None
        form = RatingForm()

    rating_info = {
        'user': user,
        'object': object,
        'user_has_rated_item': user_has_rated_item,
        'user_rating_this_item': user_rating_this_item,
        'form': form,
    }
    return rating_info

def get_category_parent(category_id):
    '''
        Returns an ordered list of category ids for all category 'ancestors'.
        Ancestors are the parent_category for the category_id param, plus the parent's parent, etc.
        The returned list includes the category_id param as its first item.
    '''
    category = Category.objects.get(id=category_id)
    parent = category.parent_category_id or None
    list = []
    if parent:
        list.extend(get_category_parent(parent))
    list.append(category_id)
    return list
    
def get_category_children(category_id):
    '''
        Returns an ordered list of category ids for all categories that are children of the category_id param.
        The returned list include the category_id param as its first item.
        Different from category.child_categories in that the list is ordered and it includes the category_id param as its first item.
    '''
    children = Category.objects.filter(parent_category = category_id)
    list = []
    if children:
        for child in children:
            list.extend(get_category_children(child.id))
    list.append(category_id)
    return list

def get_category_list(parent_category_id):
    """
        Returns an html-formatted list of categories for parent_category_id param,
        plus all child categories.
    """

    strHTML = ''
    # children = Category.objects.filter(parent_category = parent_category_id).order_by('name')
    children = category_qs.filter(parent_category = parent_category_id).order_by('name')
    if children:
        for child in children:
            id_str = child.name.replace('\\','').replace(' ','_').replace('\'','').lower()
            category_products_url = reverse('shop:category_products', kwargs={'category_id': child.id})
            strHTML += f'<div class="category" id="category-{id_str}">'
            strHTML += f'<a href="{category_products_url}">'
            strHTML += child.name
            strHTML += '</a>'
            strHTML += get_category_list(child.id) 
            strHTML += '</div>'    

    return strHTML.replace('\\','')  

def get_categories(parent_category_id,level=0):
    """
        Returns a list of category objects  annotated with indent_level, 
        including parent_category_id param, plus all descendent categories. 
    """

    categories = []
    
    for current_category in category_qs.filter(parent_category = parent_category_id).annotate(
        indent_level=Value(level, IntegerField()),
        indent_px=Value(f"{level*20}px", CharField()),
    ).order_by('name'):
        categories.append(current_category) 
        for child_category in get_categories(current_category.id, level+1):
            categories.append(child_category)

    return categories    

def create_ref_code():
    """
        Creates a 20-character reference code containing lowercase letters and digits.
    """

    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def random_string_generator(size = 10, chars = string.ascii_lowercase + string.digits): 
    """
        Returns a random string of length specified in 'size' parameter.
        The characters that can be used are specified in the 'chars' string parameter 
        (defaults to all alphanumeric ascii characters).
    """

    return ''.join(random.choice(chars) for _ in range(size)) 
  
def unique_slug_generator(instance, field_to_slugify, new_slug = None): 
    """
       Generates a unique slug for the specified field in a class.
       Class must have a slug field called 'slug' and must provide the field_to_slugify.
       If the 'new_slug' parameter is provided, the slug will be based on 
       'new_slug" instead of 'field_to_slugify'.       
    """

    if new_slug is not None: 
        slug = new_slug 

    else: 
        slug = slugify(instance[field_to_slugify])  # slugify(instance.first_name) 

    Klass = instance.__class__ 
    slug_exists = Klass.objects.filter(slug = slug).exists() 
      
    if slug_exists: 
        new_slug = f"{slug}-{random_string_generator(size = 4)}"
              
        return unique_slug_generator(instance, new_slug = new_slug) 
    return slug 

def getPhotoFromURL(image_url,filename):
    """
        Downloads file from provided image_url and returns an in-memory file
        with provided filename.
    """

    headers = {"Accept":"image/*"}

    try:
        response = requests.get(image_url, headers=headers)
    except requests.exceptions.MissingSchema:
        # http://httpbin.org/image/jpeg
        print(f'Problem with image url \'{image_url}\'. Did you forget to provide the URL?')
        return ''

    if response.status_code == 200:
        
        if response.headers.get('content-type', 'Not Specified')[:6] == 'image/':
            print(f'Image has been downloaded from {image_url}')

            # see https://medium.com/@jainmickey/how-to-save-file-programmatically-to-django-37c67d9664b5
            # for more information 
            temp_image = NamedTemporaryFile() #delete=True is default
            temp_image.write(response.content)
            temp_image.flush()
            return File(temp_image,name=filename)
        
        else:
            print(f'Received non-image content type from {image_url}: {response.headers.get("content-type", "Not Specified")}.')
            return ''

    else:
        print(f'Image could not be downloaded from {image_url}.\nStatus Code: {response.status_code}.')
        return ''