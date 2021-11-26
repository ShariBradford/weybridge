from datetime import datetime,timezone,timedelta


from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core import serializers
from django.db.models import (
    OuterRef, Subquery, Avg, F, Q, Count, Min, FilteredRelation, Value, IntegerField, 
    CharField, BooleanField, Case, When)
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, reverse, get_object_or_404,HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView,DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from ipware import get_client_ip

from .models import *

category_qs = Category.objects.all()
throw_away_var = len(category_qs)   #force evaluation of queryset
recently_viewed_max = 4 # number of recently viewed products to store in session

class StaffMemberRequiredMixin(UserPassesTestMixin):
    # raise_exception = False

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        """ Do whatever you want here if the user doesn't pass the test """
        if self.request.user.is_authenticated:
            return render(self.request, 'shop/403.html')
        return super(StaffMemberRequiredMixin,self).handle_no_permission()

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
        all_ratings = object.ratings.annotate(upvotes=upvotes).annotate(downvotes=downvotes).order_by('-created_at')       
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

class RecentlyViewedMixin(object):
    # maximum number of products to show in recently viewed list
    max = recently_viewed_max
    
    def get_recently_viewed_products(self, **kwargs):
        #  GET RECENTLY VIEWED PRODUCTS

        current_item_id = kwargs.get('current_item_id', None)
        remove_current_item = kwargs.get('remove_current_item', False)
        list_order = 'id'

        try:
            recently_viewed = self.request.session['recently_viewed']
            # print(f"Recent: {Product.objects.filter(id__in = recently_viewed)}")
            
            # specify the order of the queryset according to the recently_viewed array
            list_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(recently_viewed)])
            # reference 'django models conditional expressions' for info on Case and When
            # print(f"List Order: {list_order}")

            if current_item_id and remove_current_item and current_item_id in recently_viewed:
                # print(f'This object ({obj.id}) already in recently viewed items ({recently_viewed})')
                recently_viewed.remove(current_item_id)
                # print(f"Recent (after removing current item): {Product.objects.filter(id__in = recently_viewed)}")

            if len(recently_viewed) > self.max:
                # print(f'Too many items in recently viewed items ({len(recently_viewed)})')
                # check if recently_viewed has equal to or more than the maximum number of items
                # if so, delete the last one 
                del recently_viewed[-1]
                # print(f"Recent (after resizing list): {Product.objects.filter(id__in = recently_viewed)}")            

        except KeyError:
            recently_viewed = []

        # Add recently viewed items to the session variable
        self.request.session['recently_viewed'] = recently_viewed
        products = Product.objects.filter(id__in = recently_viewed).order_by(list_order)

        # insert this item at the front of the recently_viewed list
        if current_item_id:
            recently_viewed.insert(0,current_item_id)
            # print(f"Recently viewed items (after adding current item): {recently_viewed}") # {Product.objects.filter(id__in = recently_viewed)}")

        return products

class RecentProductsView(StaffMemberRequiredMixin, RecentlyViewedMixin,TemplateView):
    template_name = 'shop/recent_products.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recently_viewed_items'] = self.get_recently_viewed_products()
        return context

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
            # print(f"Sort by {query_sort}")

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

        best_promotion = (
            Promotion.objects.filter(
                product=OuterRef('pk'),
                sale__start_date__lte=date.today(),
                sale__end_date__gte=date.today(),
            )
            .order_by('sale_price')
        )
        queryset = Product.objects.filter(filter_conditions).distinct().annotate(
            avg_rating=Avg('ratings__number_of_stars'), 
            num_ratings=Count('ratings'),
            best_promotion_price=Subquery(best_promotion.values('sale_price')[:1]),
            best_promotion_name=Coalesce(Subquery(best_promotion.values('sale__name')[:1]),Value('')),
        ).prefetch_related('ratings','promotions','product_photos')

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)

            queryset = queryset.order_by(*ordering)

        return queryset

class ProductDetail(RecentlyViewedMixin, DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        rating_info = get_product_rating_for_user(self.request.user,self.object)
        # print(f"Rating information for {self.object}:")
        # print(f"{rating_info}")
        # print(f'User Rating: {context["user_rating_this_item"].number_of_stars or None}')   

        # context['average_rating'] = rating_info['average_rating']
        # context['all_ratings'] = rating_info['all_ratings']
        # context['user_has_rated_item'] = rating_info['user_has_rated_item']
        # context['user_rating_this_item'] = rating_info['user_rating_this_item']
        # context['form'] = rating_info['form']
        # context['question_form'] = QuestionForm()
        # context['answer_form'] = AnswerForm()
        # context['categories'] = " | ".join(list(category.name for category in self.object.categories.all()))

        context.update({
            'average_rating': rating_info['average_rating'],
            'all_ratings': rating_info['all_ratings'],
            'user_has_rated_item': rating_info['user_has_rated_item'],
            'user_rating_this_item': rating_info['user_rating_this_item'],
            'form': rating_info['form'],
            'question_form': QuestionForm(),
            'answer_form': AnswerForm(),
            'categories': " | ".join(list(category.name for category in self.object.categories.all())),
            'breadcrumbs': get_breadcrumbs('product',self.object.id),
        })
        
        #  GET RECENTLY VIEWED PRODUCTS

        # Don't show the current item in recently viewed.
        # Put the recently_viewed items in the context before adding the current item to recently_viewed.
        obj = self.object
        # try:
        #     recently_viewed = self.request.session['recently_viewed']
        #     # print(f"Recent: {Product.objects.filter(id__in = recently_viewed)}")
            
        #     # specify the order of the queryset according to the recently_viewed array
        #     list_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(recently_viewed)])
        #     # reference 'django models conditional expressions' for info on Case and When

        #     # print(f"List Order: {list_order}")

        #     # if the item is already in the list, remove it.
        #     if obj.id in recently_viewed:
        #         # print(f'This object ({obj.id}) already in recently viewed items ({recently_viewed})')
        #         recently_viewed.remove(obj.id)
        #         # print(f"Recent (after removing current item): {Product.objects.filter(id__in = recently_viewed)}")
        #         context['recently_viewed_items'] = Product.objects.filter(id__in = recently_viewed).order_by(list_order)[0:4]

        #     elif len(recently_viewed) > recently_viewed_max:
        #         # print(f'Too many items in recently viewed items ({len(recently_viewed)})')
        #         # check if recently_viewed has equal to or more than the maximum number of items
        #         # if so, delete the last one 
        #         context['recently_viewed_items'] = Product.objects.filter(id__in = recently_viewed).order_by(list_order)[0:4]
        #         del recently_viewed[-1]
        #         # print(f"Recent (after resizing list): {Product.objects.filter(id__in = recently_viewed)}")            

        #     else:
        #         context['recently_viewed_items'] = Product.objects.filter(id__in = recently_viewed).order_by(list_order)[0:4]

        #     # insert this item at the front of the recently_viewed list
        #     recently_viewed.insert(0,obj.id)
        #     # print(f"Recently viewed items (after adding current item): {recently_viewed}") # {Product.objects.filter(id__in = recently_viewed)}")

        # except KeyError:
        #     recently_viewed = [obj.id]
            
        # # Add recently viewed items to the session variable
        # self.request.session['recently_viewed'] = recently_viewed
        context['recently_viewed_items'] = self.get_recently_viewed_products(current_item_id=obj.id,remove_current_item=True)[0:4]

        return context

class ProductCreate(StaffMemberRequiredMixin, CreateView):
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

class ProductUpdate(StaffMemberRequiredMixin, UpdateView):
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

class ProductDelete(StaffMemberRequiredMixin, DeleteView):
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

class SaleList(StaffMemberRequiredMixin, ListView):
    model = Sale

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = get_breadcrumbs('page',None,'Sales')
        return context

class SaleDetail(StaffMemberRequiredMixin, DetailView):
    model = Sale

class SaleCreate(StaffMemberRequiredMixin, CreateView):
    model = Sale
    form_class = SaleForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class SaleUpdate(StaffMemberRequiredMixin, UpdateView):
    model = Sale
    form_class = SaleForm

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class SaleDelete(StaffMemberRequiredMixin, DeleteView):
    model = Sale
    success_url = reverse_lazy('shop:sales')
    template_name = 'shop/object_confirm_delete.html'

class PromotionList(StaffMemberRequiredMixin, ListView):
    model = Promotion
    ordering = ['-sale__start_date', 'product__name']

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = get_breadcrumbs('page',None,'Promotions')
        return context

class PromotionDetail(StaffMemberRequiredMixin, DetailView):
    model = Promotion

class PromotionCreate(StaffMemberRequiredMixin, CreateView):
    model = Promotion
    form_class = PromotionForm
    success_url = reverse_lazy('shop:promotions')

    def get_initial(self):
        product_pk = self.kwargs.get('pk',None)
        # try:
        #     product = Product.objects.get(id=product_pk)
        # except Product.DoesNotExist:
        #     product = None

        sale_id = self.request.GET.get('sale_id',None)
        print(f'Sale ID: {sale_id}')

        return {'product':product_pk, 'sale': sale_id}

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     if kwargs['pk']:
    #         context['product'] = Product.objects.get(id=kwargs['pk'])
    #     return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class PromotionUpdate(StaffMemberRequiredMixin, UpdateView):
    model = Promotion
    form_class = PromotionForm
    success_url = reverse_lazy('shop:promotions')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class PromotionDelete(StaffMemberRequiredMixin, DeleteView):
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

class CategoryDetail(StaffMemberRequiredMixin, DetailView):
    model = Category

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        self.subcategories = get_category_children(self.object.id) 
        context.update({
            'subcategories': " | ".join(list(category.name for category in Category.objects.filter(id__in = self.subcategories).all())),
            'breadcrumbs': get_breadcrumbs('category',self.object.id),
            'product_count': Product.objects.filter(categories__id__in = self.subcategories).distinct().count(),
        })      
        # context['subcategories'] = " | ".join(list(category.name for category in Category.objects.filter(id__in = self.subcategories).all()))
        # context['breadcrumbs'] = get_breadcrumbs('category',self.object.id)
        # context['product_count'] = Product.objects.filter(categories__id__in = self.subcategories).distinct().count()

        # print(f"Subcategories ARRAY for {self.object.name}: {self.subcategories}")
        # print(f"Subcategories for {self.object.name}: {context['subcategories']}")
        # print(f"Breadcrumbs for {self.object.name}: {context['breadcrumbs']}")
        # print(f"Product Count for {self.object.name}: {context['product_count']}")
        return context

class CategoryCreate(StaffMemberRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy('shop:categories')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class CategoryUpdate(StaffMemberRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm

    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        # if the user deleted the previous photo, add the default photo
        if form.cleaned_data['profile_pic'] == None or form.cleaned_data['profile_pic'] == False:
            form.instance.profile_pic = Category._meta.get_field('profile_pic').get_default()

        return super().form_valid(form)

class CategoryDelete(StaffMemberRequiredMixin, DeleteView):
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
        # Add in the category and breadcrumbs
        context.update({
            'category': self.category,
            'breadcrumbs': get_breadcrumbs('category',self.category.id),
        })
        # context['category'] = self.category
        # context['breadcrumbs'] = get_breadcrumbs('category',self.category.id)
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

        context.update({
            'breadcrumbs': get_breadcrumbs('other',self.object.id,self.object.name),
            'product_count': Product.objects.filter(collection = self.object).count(),
        })
        # context['breadcrumbs'] = get_breadcrumbs('other',self.object.id,self.object.name)       
        # context['product_count'] = Product.objects.filter(collection = self.object).count()

        # print(f"Breadcrumbs for {self.object.name}: {context['breadcrumbs']}")
        # print(f"Product Count for {self.object.name}: {context['product_count']}")
        return context

class CollectionCreate(StaffMemberRequiredMixin, CreateView):
    model = Collection
    form_class = CollectionForm
    success_url = reverse_lazy('shop:collections')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class CollectionUpdate(StaffMemberRequiredMixin, UpdateView):
    model = Collection
    form_class = CollectionForm

    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        # if the user deleted the previous photo, add the default photo
        if form.cleaned_data['profile_pic'] == None or form.cleaned_data['profile_pic'] == False:
            form.instance.profile_pic = Collection._meta.get_field('profile_pic').get_default()

        return super().form_valid(form)

class CollectionDelete(StaffMemberRequiredMixin, DeleteView):
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
        context.update({
            'collection': self.collection,
            'breadcrumbs': get_breadcrumbs('page',None,self.collection.name),
        })
        # context['collection'] = self.collection
        # context['breadcrumbs'] = get_breadcrumbs('page',None,self.collection.name)
        return context

class FavoriteProductList(ProductList):
    template_name = 'shop/favorite_products.html'
    paginate_by = 8

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

def get_sale_info(request, sale_id):
    if request.method == 'POST':
        sale = Sale.objects.get(id=sale_id)
        data = {
            'description': sale.description,
            'id': sale.id,
            'start_date': sale.start_date,
            'end_date': sale.end_date,
            'has_ended': sale.has_ended(),
        }
        return JsonResponse(data)
    return HttpResponseNotAllowed(['POST'])

@staff_member_required
def clear_recent(request):
    request.session['recently_viewed'] = []
    print(f"Recently viewed items: {request.session['recently_viewed']}")
    return redirect('/')