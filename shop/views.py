from django.views.generic import ListView,DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.shortcuts import render, redirect, reverse, get_object_or_404,HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Avg, F, Q, Count, FilteredRelation, Value, IntegerField, CharField
from ipware import get_client_ip
from datetime import datetime
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseNotAllowed
from .models import *
from django.core import serializers

category_qs = Category.objects.all()
throw_away_var = len(category_qs)   #force evaluation of queryset

def test(request):
    return render(request, 'shop/test.html', {'test': 'Testing 123'})

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
    categories = []
    
    for current_category in category_qs.filter(parent_category = parent_category_id).annotate(
        indent_level=Value(level, IntegerField()),
        indent_px=Value(f"{level*20}px", CharField()),
    ).order_by('name'):
        categories.append(current_category) 
        for child_category in get_categories(current_category.id, level+1):
            categories.append(child_category)

    return categories    

def get_product_rating_for_user(user, object):
    # returns information about whether the user has rated a particular product
 
    if hasattr(object,'ratings'):

        if user.is_authenticated == False:
            # user is anonymous, so user has not yet rated item yet
            user_has_rated_item = False
            user_rating_this_item = None
            form = RatingForm()

        # determine if this user has rated this item before
        elif object.ratings.filter(user=user).count() > 0:
            #user hsa rated item; don't permit another rating (just don't return a form object)
            # print(f"Ratings for {object}: {object.ratings.filter(user=user).count()}")
            user_has_rated_item = True
            user_rating_this_item = object.ratings.filter(user=user).first()
            form = None

        else:
            # user has not yet rated this item
            user_has_rated_item = False
            user_rating_this_item = None
            form = RatingForm()

        #get the oversall ratings for this item
        # average_rating = Rating.objects.filter(dish=dish).aggregate(Avg('number_of_stars'))['number_of_stars__avg'] or 0
        average_rating = object.ratings.aggregate(Avg('number_of_stars'))['number_of_stars__avg'] or 0
        
        upvotes = Count('votes__score_type', filter=Q(votes__score_type=1))
        downvotes = Count('votes__score_type', filter=Q(votes__score_type=-1))
        all_ratings = object.ratings.annotate(upvotes=upvotes).annotate(downvotes=downvotes)       
        # all_ratings = object.ratings.all()

    else:
        # item has no ratings yet
        print(f"No ratings yet for {object}.")
        form = RatingForm()
        average_rating = 0
        all_ratings = None

    rating_info = {
        'user': user,
        'object': object,
        'average_rating': average_rating,
        'all_ratings': all_ratings,
        'user_has_rated_item': user_has_rated_item,
        'user_rating_this_item': user_rating_this_item,
        'form': form,
    }
    return rating_info

def get_breadcrumbs(page_type,item_id, breadcrumb_name=None):
    home = {
        'type':'home',
        'id': 0,
        'name': 'home'
    }
    categories = [home]

    if page_type == 'product': #product details page
        #get product category
        product_object = Product.objects.get(id=item_id)
        category_object = product_object.categories.first()
        category_list = get_category_parent(category_object.id)
        for category in category_list:
            categories.append ({
                "type": 'category',
                "id": category,
                "name": Category.objects.get(id=category).name,
            })
        categories.append ({
            "type": "product",
            "id": -1,
            "name": product_object.name,
        })
    elif page_type == 'category':   #category products list
        # category_object = Category.objects.get(id=item_id)
        category_list = get_category_parent(item_id)
        for category in category_list:
            categories.append ({
                "type": 'category',
                "id": category,
                "name": Category.objects.get(id=category).name,
            })
    else:
        categories.append ({
            "type": 'other',
            "id": None,
            "name": breadcrumb_name,
        })

    return categories

@login_required
def rate_product(request, product_id):
    # This view can be called via Ajax and returns only the ratings form

    user = request.user
    product = Product.objects.get(id=product_id)

    # print(f'Processing rating of product '{product.name}' by {user.full_name()}')
    if request.method == 'POST':

        rating = Rating(user=user, product=product,updated_by=user)
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            rating = form.save()
    
    else: #this is a GET request so return to the details page where the blank rating form is displayed
        return redirect(reverse('product_details'))
    
    if hasattr(product,'ratings'):
        # if user has rated item, don't let user rate it again
        # get user's rating for this item
        if product.ratings.filter(user=user).count() > 0:
            user_has_rated_item = True
            user_rating_this_item = product.ratings.filter(user=user).first()
            form = None #don't return a form

        else:
            user_has_rated_item = False
            user_rating_this_item = None

        #recalculate average ratings
        average_rating = Rating.objects.filter(product=product).aggregate(Avg('number_of_stars'))['number_of_stars__avg'] or 0
        all_ratings = product.ratings.all()

    else:
        average_rating = 0
        all_ratings = None

    context = {
        'user': user,
        'product': product,
        'average_rating': average_rating,
        'all_ratings': all_ratings,
        'user_has_rated_item': user_has_rated_item,
        'user_rating_this_item': user_rating_this_item,
        'ratings_form': form,
    }
   
    return render(request, 'shop/ratings-info.html', context)

def rating_vote(request, rating_id, score):
    kwargs = {
        'rating_id': rating_id,
        'user': request.user
    }
    client_ip, is_routable = get_client_ip(request)
    if request.user.is_authenticated == False:
        if client_ip is None:
            return redirect(request.META.get('HTTP_REFERER'))
        else:
            # We got the client's IP address
            if not is_routable:
                return redirect(request.META.get('HTTP_REFERER'))
    else:
        # user is authenticated; make sure this user did not author the rating.
        # user cannot vote on her/his own rating.
        rating = Rating.objects.get(id=rating_id)
        if request.user == rating.user:
            return redirect(request.META.get('HTTP_REFERER'))
    
    kwargs['ip_address'] = client_ip
    
    try:
        #if the following result does not raise an error, it means that 
        # user has already votedon this rating. Do nothing
        RatingVote.objects.get(**kwargs)

    except RatingVote.DoesNotExist:
        kwargs['score_type'] = score
        vote = RatingVote.objects.create(**kwargs)
        vote.save()

    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def favorite(request, product_id):
    user = request.user
    next = request.GET.get('next', request.META.get('HTTP_REFERER'))
    if hasattr(user,"profile"): 
        # adding a second time is OK, it will not duplicate the relation
        user.profile.favorites.add(product_id)
        # messages.success(request,"Item favorited!")

    # user could be on any numbmer of pages when they push the favorite button
    # return the user to the same page they were on when they favorited the item
    return redirect(next)

@login_required
def unfavorite(request, product_id):
    user = request.user
    next = request.GET.get('next', request.META.get('HTTP_REFERER'))

    if hasattr(user,"profile"):
        user.profile.favorites.remove(product_id)
        # messages.success(request,"Item unfavorited!")
 
    # user could be on any numbmer of pages when they push the favorite button
    # return the user to the same page they were on when they favorited the item
    return redirect(next)
 
@login_required
def ajax_favorite(request, product_id):
    # print(f"Starting favorite action on product id #{product_id}")

    if request.method == 'POST':
        user = request.user
        product = Product.objects.get(id=product_id)

        if hasattr(user,"profile"): 
            # adding a second time is OK, it will not duplicate the relation
            user.profile.favorites.add(product_id)
            # messages.success(request,"Item favorited!")

        else:   # user has no profile
            profile = UserProfile(user=user)
            profile.favorites.add(product_id)
            profile.save()

        context = {
            'product': product,
            'favorite_products': user.profile.favorites.all(),
        }

        # print (f"Product: {context['product']}")
        # print(f"Favorites: {context['favorite_products']}")
        return render(request, 'shop/action-favorite.html', context)

    # user could be on any numbmer of pages when they push the favorite button
    # return the user to the same page they were on when they favorited the item
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def ajax_unfavorite(request, product_id):
    if request.method == 'POST':
        user = request.user
        product = Product.objects.get(id=product_id)

        if hasattr(user,"profile"): 
            user.profile.favorites.remove(product_id)
            # messages.success(request,"Item favorited!")

        context = {
            'product': product,
            'favorite_products': user.profile.favorites.all(),
        }
        return render(request, 'shop/action-favorite.html', context)

    # user could be on any numbmer of pages when they push the favorite button
    # return the user to the same page they were on when they favorited the item
    return redirect(request.META.get('HTTP_REFERER'))

class ProductList(ListView):
    model = Product
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['sidebar'] = get_category_list(None)
        context['sort_by'] = self.request.GET.get('sort_by', 'mostPopular')
        return context

    def get_ordering(self):
        query_sort = self.request.GET.get('sort_by', 'mostPopular')
        # print(f"Sort by: {query_sort}")
        if query_sort:
            print(f"Sort by {query_sort}")

            if query_sort == "priceLowToHigh":
                return 'price'
            elif query_sort == "priceHighToLow":
                return '-price'
            elif query_sort == "aToZ":
                return 'name'
            elif query_sort == "zToA":
                return '-name'
            elif query_sort == "new":
                return '-created_at'
            else:
                # Most popular
                return ['-avg_rating','-num_ratings'] # assumes self.queryset is annotated with these two fields
        return ['-avg_rating','-num_ratings'] # assumes self.queryset is annotated with these two fields

    def get_queryset(self):
        query_search = self.request.GET.get('q', None)
        # print(f"query_search: {query_search}")
        
        if query_search:
            filter_conditions = (Q(name__icontains = query_search)) | (Q(description__icontains=query_search)) | (Q(sku__icontains=query_search))
            # return Product.objects.filter(name__icontains=query)
            # qs = Product.objects.filter(filter_conditions).distinct()
        else:
            # qs = Product.objects.all()
            filter_conditions = Q(name__isnull = False)

        queryset = Product.objects.filter(filter_conditions).distinct().annotate(
            avg_rating=Avg('ratings__number_of_stars'), 
            num_ratings=Count('ratings')
        ).prefetch_related('ratings','promotions','product_photos')

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)

            queryset = queryset.order_by(*ordering)

        return queryset

class ProductDetail(DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        rating_info = get_product_rating_for_user(self.request.user,self.object)
        # print(f"Rating information for {self.object}:")
        # print(f"{rating_info}")
        # #get the oversall ratings
        # average_rating = Rating.objects.filter(product_id=self.object.id).aggregate(Avg('number_of_stars'))['number_of_stars__avg'] or 0
        # all_ratings = self.object.ratings.all() # product.ratings.all()

        context['average_rating'] = rating_info['average_rating']
        context['all_ratings'] = rating_info['all_ratings']
        context['user_has_rated_item'] = rating_info['user_has_rated_item']
        context['user_rating_this_item'] = rating_info['user_rating_this_item']
        context['form'] = rating_info['form']
        context['question_form'] = QuestionForm()
        context['answer_form'] = AnswerForm()
        context['categories'] = " | ".join(list(category.name for category in self.object.categories.all()))
        # print(f'User Rating: {context["user_rating_this_item"].number_of_stars or None}')   

        context['breadcrumbs'] = get_breadcrumbs('product',self.object.id)

        return context

class ProductCreate(CreateView):
    model = Product
    form_class = ProductFormWithImages
    
    def form_valid(self, form):
        kwargs = self.get_form_kwargs()
        files = kwargs['files']
        images = files.getlist('images')

        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)

        if images:
            for image in images:
                i = ProductPhoto(product=self.object,picture=image)
                i.save()
        else:
            # no files uploaded so add default product photo
            i = ProductPhoto(product=self.object)
            i.save()
            
        # return super().form_valid(form)
        return response

class ProductUpdate(UpdateView):
    model = Product
    # form_class = ProductForm
    form_class = ProductFormWithImages

    def get_initial(self):
        initial = super().get_initial()
        initial['images'] = self.object.product_photos.all().values('picture')
        return initial
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # context['images'] = self.object.product_photos.all().values('picture')
        context['images'] = self.object.product_photos.all()
        # context['form'] = rating_info['form']
        # context['question_form'] = QuestionForm()
        # context['categories'] = " | ".join(list(category.name for category in self.object.categories.all()))
        # # print(f'User Rating: {context["user_rating_this_item"].number_of_stars or None}')   

        return context
        
    # def form_valid(self, form):
    #     form.instance.updated_by = self.request.user
    #     return super().form_valid(form)
    def form_valid(self, form):
        kwargs = self.get_form_kwargs()
        files = kwargs['files']
        images = files.getlist('images')

        form.instance.updated_by = self.request.user
        response = super().form_valid(form)

        if images:
            for image in images:
                i = ProductPhoto(product=self.object,picture=image)
                i.save()
        else:
            if self.object.product_photos.count() < 1:
                # no existing or added images uploaded, so add default product photo
                i = ProductPhoto(product=self.object)
                i.save()
            
        # return super().form_valid(form)
        return response

class ProductDelete(DeleteView):
    model = Product
    success_url = reverse_lazy('shop:index')
    template_name = 'shop/object_confirm_delete.html'

def product_photo_delete(request, product_photo_id):
    product_photo = ProductPhoto.objects.get(id=product_photo_id)
    product = product_photo.product 

    if request.method == 'POST':        
        product_photo.delete()
        # return a list of the remaining product photos so that te images can be redisplayed in the container

    context = {
        'images': product.product_photos.all(),
    }
    return render(request,'shop/existing-images.html', context)

def product_photo_make_primary(request, product_photo_id):
    product_photo = ProductPhoto.objects.get(id=product_photo_id)
    product = product_photo.product 

    if request.method == 'POST':   
        # Note about using .update() from djangodocs: realize that update() does an update at the SQL level and, thus, 
        # does not call any save() methods on your models, nor does it emit the pre_save or post_save signals 
        # (which are a consequence of calling Model.save()). 
        # If you want to update a bunch of records for a model that has a custom save() method, 
        # loop over them and call save()
        product.product_photos.filter(is_default=True).update(is_default=False)
        product_photo.is_default = True
        product_photo.save()

    # return a list of the remaining product photos so that te images can be redisplayed in the container
    context = {
        'images': product.product_photos.all(),
    }
    return render(request,'shop/existing-images.html', context)

class SaleList(ListView):
    model = Sale

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = get_breadcrumbs('page',None,'Sales')
        return context

class SaleDetail(DetailView):
    model = Sale

class SaleCreate(CreateView):
    model = Sale
    form_class = SaleForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class SaleUpdate(UpdateView):
    model = Sale
    form_class = SaleForm

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class SaleDelete(DeleteView):
    model = Sale
    success_url = reverse_lazy('shop:sales')
    template_name = 'shop/object_confirm_delete.html'

class PromotionList(ListView):
    model = Promotion

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = get_breadcrumbs('page',None,'Promotions')
        return context

class PromotionDetail(DetailView):
    model = Promotion

class PromotionCreate(CreateView):
    model = Promotion
    form_class = PromotionForm

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     # context['products'] = Product.objects.values('name','price','product_photos')
    #     return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class PromotionUpdate(UpdateView):
    model = Promotion
    form_class = PromotionForm

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class PromotionDelete(DeleteView):
    model = Promotion
    success_url = reverse_lazy('shop:index')
    template_name = 'shop/object_confirm_delete.html'

class CategoryList(ListView):
    model = Category

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = get_breadcrumbs('page',None,'Categories')
        return context

class CategoryDetail(DetailView):
    model = Category

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        self.subcategories = get_category_children(self.object.id)       
        context['subcategories'] = " | ".join(list(category.name for category in Category.objects.filter(id__in = self.subcategories).all()))

        context['breadcrumbs'] = get_breadcrumbs('category',self.object.id)
        
        context['product_count'] = Product.objects.filter(categories__id__in = self.subcategories).distinct().count()

        # print(f"Subcategories ARRAY for {self.object.name}: {self.subcategories}")
        # print(f"Subcategories for {self.object.name}: {context['subcategories']}")
        # print(f"Breadcrumbs for {self.object.name}: {context['breadcrumbs']}")
        # print(f"Product Count for {self.object.name}: {context['product_count']}")
        return context

class CategoryCreate(CreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy('shop:categories')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class CategoryUpdate(UpdateView):
    model = Category
    form_class = CategoryForm

    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        # if the user deleted the previous photo, add the default photo
        if form.cleaned_data['profile_pic'] == None or form.cleaned_data['profile_pic'] == False:
            form.instance.profile_pic = Category._meta.get_field('profile_pic').get_default()

        return super().form_valid(form)

class CategoryDelete(DeleteView):
    model = Category
    success_url = reverse_lazy('shop:categories')
    template_name = 'shop/object_confirm_delete.html'

class CategoryProductList(ProductList):
    template_name = 'shop/category_products.html'

    def get_queryset(self):
        qs = super().get_queryset()

        self.category = get_object_or_404(Category,id=self.kwargs['category_id'])

        # get all child categories so that you can display products from this category and its subcategories
        self.categories_list = get_category_children(self.category.id)
        # print(f"Category: {self.category.name}")
        # print(f"Category Hierarchy: {self.categories_list}")

        return qs.filter(categories__id__in = self.categories_list)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in the category
        context['category'] = self.category
        context['breadcrumbs'] = get_breadcrumbs('category',self.category.id)
        return context

class CollectionList(ListView):
    model = Collection

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = get_breadcrumbs('page',None,'Collections')
        return context

class CollectionDetail(DetailView):
    model = Collection

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        context['breadcrumbs'] = get_breadcrumbs('other',self.object.id,self.object.name)       
        context['product_count'] = Product.objects.filter(collection = self.object).count()

        # print(f"Breadcrumbs for {self.object.name}: {context['breadcrumbs']}")
        # print(f"Product Count for {self.object.name}: {context['product_count']}")
        return context

class CollectionCreate(CreateView):
    model = Collection
    form_class = CollectionForm
    success_url = reverse_lazy('shop:collections')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class CollectionUpdate(UpdateView):
    model = Collection
    form_class = CollectionForm

    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        # if the user deleted the previous photo, add the default photo
        if form.cleaned_data['profile_pic'] == None or form.cleaned_data['profile_pic'] == False:
            form.instance.profile_pic = Collection._meta.get_field('profile_pic').get_default()

        return super().form_valid(form)

class CollectionDelete(DeleteView):
    model = Collection
    success_url = reverse_lazy('shop:collections')
    template_name = 'shop/object_confirm_delete.html'

class CollectionProductList(ProductList):
    template_name = 'shop/collection_products.html'

    def get_queryset(self):
        qs = super().get_queryset()

        self.collection = get_object_or_404(Collection,id=self.kwargs['collection_id'])
        # print(f"Collection: {self.collection.name}")

        return qs.filter(collection = self.collection)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in the category
        context['collection'] = self.collection
        context['breadcrumbs'] = get_breadcrumbs('page',None,self.collection.name)
        return context

class FavoriteProductList(ProductList):
    template_name = 'shop/favorite_products.html'

    def get_queryset(self):
        qs = super().get_queryset()

        if hasattr(self.request.user, 'profile'):
            user_favorites = self.request.user.profile.favorites.all()
        else:
            user_favorites = None

        # return qs.filter(user_likes = self.request.user.id)
        return qs.filter(id__in = user_favorites)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in the breadcrumbs
        context['breadcrumbs'] = get_breadcrumbs('page',None,'Favorites')
        return context

class SaleProductList(ProductList):
    template_name = 'shop/sale_products.html'

    def get_queryset(self):
        qs = super().get_queryset()

        # return qs.annotate(
        #     on_sale = FilteredRelation(
        #         'promotions', condition = Q(
        #             promotions__start_date__lte=date.today(),
        #             promotions__end_date__gte=date.today()
        #         )
        #     )
        # ).filter(on_sale = True)

        # return qs.filter(
        #     promotions__start_date__lte=date.today(),
        #     promotions__end_date__gte=date.today()
        # )

        return qs.filter(
            promotions__sale__start_date__lte=date.today(),
            promotions__sale__end_date__gte=date.today()
        )

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in the breadcrumbs
        context['breadcrumbs'] = get_breadcrumbs('page',None,'Sale')
        return context

@login_required
def question_product(request, product_id):
    # This view can be called via Ajax and returns only the markup for the new comment

    user = request.user
    product = Product.objects.get(id=product_id)

    # print(f'Processing product question on '{product.name}' from {user.full_name()}')
    if request.method == 'POST':

        question = Question(asker=user, product=product)
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save()
            
    else: #this is a GET request so return to the details page where the blank rating form is displayed
        return redirect(reverse('product_details'))
    
    context = {
        'user': user,
        'product': product,
        'question': question,
        'question_form': form,
        'answer_form': AnswerForm(),
    }
   
    return render(request, 'shop/question.html', context)

@login_required
def answer_question(request, question_id):
    # This view can be called via Ajax and returns only the markup for the new answer

    user = request.user
    question = Question.objects.get(id=question_id)

    # print(f'Processing product answer on '{product.name}' from {user.full_name()}')
    if request.method == 'POST':

        answer = Answer(answerer=user, question=question, updated_by=user)
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            answer = form.save()
            print("answer form is valid")
            form = AnswerForm()  # return a blank form that can be reused for the next answer

    else: #this is a GET request so return to the details page where the blank rating form is displayed
        return redirect(reverse('product_details'))
    
    context = {
        'user': user,
        'answer': answer,
        'question': question,
        'answer_form': form,
    }
   
    return render(request, 'shop/question.html', context)

def get_product_info(request, product_id):
    if request.method == 'POST':
        # data = serializers.serialize('json', Product.objects.filter(id=product_id).prefetch_related('product_photos'))
        product = Product.objects.get(id=product_id)
        product_photo_url = product.get_default_photo_url()
        data = {
            'name': product.name,
            'id': product.id,
            'sku': product.sku,
            'retail_price': product.price,
            'inventory_stock': product.inventory_stock,
            'product_photo_url': product_photo_url,
        }
        return JsonResponse(data)
    return HttpResponseNotAllowed(['POST'])
