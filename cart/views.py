from datetime import datetime

from django.conf import Settings, settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, F, Q, Count, Sum, Max
from django.http import Http404
from django.shortcuts import render, redirect, reverse, get_object_or_404,HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView,DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from ipware import get_client_ip

from weybridge.settings import CART_EMPTY_CART_ID

from .models import *
from shop.models import Product

@staff_member_required
def test_cart(request, new_cart_id=None):
    """
    Changes cart_id in session to new_cart_id for testing purposes.    
    Creates a copy of cart_id in old_cart_id in session.
    """
    
    try:
        cart_id = request.session['cart_id']
        request.session['old_cart_id'] = cart_id

    except KeyError: #no cart_id key in request.session
        messages.info(request,"CART TESTING: No cart_id in session.")
        cart_id = None

    if not new_cart_id:
        max_cart_id = Cart.objects.aggregate(Max('id'))['id__max'] or 0
        new_cart_id = max_cart_id + 1

    request.session['cart_id'] = new_cart_id
    messages.success(request,f"CART TESTING: Successfully updated cart_id from {cart_id} to {new_cart_id}.")

    return redirect(reverse_lazy('cart:cart_details'))

@staff_member_required
def get_cart_id(request):
    """
    Returns value of cart_id in session for testing purposes.    
    """
    
    try:
        cart_id = request.session['cart_id']
        messages.info(request,f"CART TESTING: cart_id = {cart_id}.")

    except KeyError: #no cart_id key in request.session
        messages.info(request,"CART TESTING: No cart_id in session.")

    return redirect(reverse_lazy('cart:cart_details'))

@staff_member_required
def revive_cart(request):
    """
    Revives cart_id in session by copying from old_cart_id for testing purposes.    
    """
    
    try:
        cart_id = request.session['old_cart_id']
        del request.session['old_cart_id']
        request.session['cart_id'] = cart_id
        messages.success(request,f"CART TESTING: Successfully revived cart_id to {cart_id}.")

    except KeyError: #no cart_id key in request.session
        messages.info(request,"CART TESTING: No old_cart_id in session.")

    return redirect(reverse_lazy('cart:cart_details'))

@staff_member_required
def clear_cart_id_from_session(request):
    """
    Deletes cart_id from session for testing purposes.
    """

    try:
        cart_id = request.session['cart_id']
        del request.session['cart_id']
        messages.success(request,f"CART TESTING: Successfully cleared cart_id {cart_id}.")

    except KeyError: #no cart_id key in request.session
        messages.warning(request,"CART TESTING: No cart_id in session.")

    return redirect(reverse_lazy('cart:cart_details'))

def get_or_create_cart(request):
    try:
        cart_id = request.session['cart_id']

        # if cart_id == settings.CART_EMPTY_CART_ID:
        #     # anonymous user cart_id, so create a cart object but do not store in database
        #     cart_json = request.session.get['cart',{}]
        #     cart = Cart(cart_json)

        # else:
        # cart = Cart.objects.get(id=cart_id)
        cart, created = Cart.objects.get_or_create(
            id=cart_id,
            defaults = {
                'user': request.user,
                'created_by': request.user,
                'updated_by': request.user,
            }
        )

        if created:
            # cart_id from request.session was not in database, so update session
            request.session['cart_id'] = cart.id

    except KeyError: #no cart_id key in request.session, so create one
        # try:
        cart = Cart(user=request.user,created_by=request.user,updated_by=request.user)
        cart.save()
        request.session['cart_id'] = cart.id

        # except:
        #     # user is not authenticated, so the attempt to create the cart above will fail
        #     # just create new empty cart
        #     cart = Cart()
        #     request.session['cart_id'] = settings.CART_EMPTY_CART_ID

    return cart

def get_cart(request):
    """
        Get a cart, if it exists, 
        but don't create the cart if it does not exist .
    """
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
    except:
        # let whatever error occurs (e.g., KeyError if cart_id not in session,
        # or DoesNotExist if found cart_id is not in the database).

        raise 

    return cart

def view_cart(request):
    empty_message = "What's this? Your cart is empty. Please keep shopping!"
    context = {
        'cart': None,
        'empty': True,
        'empty_message': empty_message,
    }
    template =  'cart/cart_detail.html'
    
    # if not request.user.is_authenticated:
        # try:
            # cart_json = request.session['cart']
            # cart = Cart(cart_json)
            # context.update({
            #     'cart': cart,
            #     'empty': cart.item_count == 0, # boolean
            # })
            # refresh cart items (e.g., if an item has gone on sale since adding 
            # to cart, the line total will need to be updated)
            # cart.refresh_cart(request.user)

    #     except KeyError: # no cart object in database
    #         context.update({
    #             'empty': True,
    #         })

    # else:
    # don't create the cart if it does not exist 
    try:
        # cart_id = request.session['cart_id']
        # cart = Cart.objects.get(id=cart_id)
        cart = get_cart(request)

        # refresh cart items (e.g., if an item has gone on sale since adding 
        # to cart, the line total will need to be updated)
        cart.refresh_cart(request.user)
    
        context.update({
            'cart': cart,
            'empty': cart.item_count == 0, # boolean
        })

    except KeyError: #no cart_id key in request.session
        # cart_id = None
        context.update({
            'empty': True,
        })

    except Cart.DoesNotExist: #cart_id is not in database
        context.update({
            'empty': True,
        })

    return render(request, template, context)

@login_required
def add_to_cart(request,product_id):
    if request.method == "POST":
        quantity = request.POST.get('qty',1)

        try:
            quantity = int(quantity)
        except:
            raise Http404("Invalid quantity.")

        cart = get_or_create_cart(request)
        product = get_object_or_404(Product,pk=product_id)

        # if cart.id == setting.CART_EMPTY_CART_ID:
        #     #Cart stored in session only so manually add item json to cart object
        #     pass

        # if the CartItem does not exist already, create it with quantity
        item, created = CartItem.objects.get_or_create(
            cart=cart, 
            product=product, 
            defaults={'quantity': quantity}
        )

        if not created: # the item was already in cart, so just update quantity
            item.quantity += quantity

        # item.line_total = item.product.price * float(item.quantity)
        item.line_total = item.product.get_sale_price() * item.quantity
        item.save()
        
        # cart.item_count += quantity
        # cart.total = cart.items.aggregate(Sum('line_total'))['line_total__sum']
        # cart.updated_by = request.user
        # cart.save()
        cart.refresh_cart(request.user)
        request.session['cart_item_count'] = cart.item_count

        return HttpResponseRedirect(reverse('cart:cart_details'))

    else:   #Ignore GET requests
        return redirect('/')

def remove_from_cart(request,product_id):
    # cart = get_or_create_cart(request)
    if request.method == "POST":
        quantity = request.POST.get('qty',1)

        try:
            quantity = int(quantity)
        except:
            raise Http404("Invalid quantity.")

        # if the cart does not exist, you can't remove anything from it
        try:
            # cart_id = request.session['cart_id']
            # cart = Cart.objects.get(id=cart_id)
            cart = get_cart(request)

        except KeyError: #no cart_id key in request.session
            raise Http404("No cart exists. Cannot complete remove operation.")
        except Cart.DoesNotExist: # cart_id from session is not in database
            raise  Http404("Cart is not in the database. Cannot complete remove operation.")
        
        product = get_object_or_404(Product,pk=product_id)

        try:
            item = CartItem.objects.get(cart=cart,product=product)
        except CartItem.DoesNotExist:
            raise Http404("No cart item matches the given query. Cannot complete remove operation.")
        
        item.quantity -= quantity
        if item.quantity > 0:
            # item.line_total = item.product.price * float(item.quantity)
            item.line_total = item.product.get_sale_price() * item.quantity
            item.save()
        else:
            item.delete()

        # cart.item_count -= quantity
        # cart.total = cart.items.aggregate(Sum('line_total'))['line_total__sum']
        # cart.updated_by = request.user
        # cart.save()

        cart.refresh_cart(request.user)
        request.session['cart_item_count'] = cart.item_count

        return HttpResponseRedirect(reverse('cart:cart_details'))
    else:
        return redirect('/')

def update_cart(request,product_id):
    """
        Similar to add_to_cart(). However, this just updates quantity of 
        product_id to whatever is in request.GET['qty']
    """

    if request.method == "POST":
        quantity = request.POST.get('qty',1)

        # 'qty' from querystring will be a string, not an integer, so convert it
        try:
            quantity = int(quantity)
        except:
            raise Http404("Invalid quantity.")

        # if the cart does not exist, you can't remove anything from it
        try:
            # cart_id = request.session['cart_id']
            # cart = Cart.objects.get(id=cart_id)        
            cart = get_cart(request)

        except KeyError: #no cart_id key in request.session
            raise Http404("No cart_id. Cannot complete update operation.")
        except Cart.DoesNotExist: #no cart with that id in the database
            raise Http404("No cart exists in database. Cannot complete update operation.")

        product = get_object_or_404(Product,pk=product_id)

        # if the product is not in the cart it cannot be updated
        try:
            item = CartItem.objects.get(cart=cart,product=product)
        except CartItem.DoesNotExist:
            raise Http404("No cart item matches the given query. Cannot complete update operation.")
        
        # item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
        # if not created: # the item was already
        #     item.quantity = quantity

        # item.line_total = item.product.price * float(item.quantity)
        # item.save()

        if quantity > 0:
            item.quantity = quantity
            # item.line_total = item.product.price * float(item.quantity)
            # item.line_total = item.product.get_sale_price() * item.quantity
            item.line_total = item.get_line_total() # * item.quantity
            item.save()
        else:
            item.delete()

        # items = cart.items.aggregate(Sum('line_total'), Sum('quantity'))
        # cart.item_count = items['quantity__sum'] or 0
        # cart.total = items['line_total__sum'] or 0
        # cart.updated_by = request.user
        # cart.save()
        cart.refresh_cart(request.user)
        request.session['cart_item_count'] = cart.item_count

        return HttpResponseRedirect(reverse('cart:cart_details'))
    else:
        return redirect("/")