from django.views.generic import ListView,DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.shortcuts import render, redirect, reverse, get_object_or_404,HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Avg, F, Q, Count, Sum
from ipware import get_client_ip
from datetime import datetime
from django.contrib.auth.models import User
from .models import *
from shop.models import Product
from django.http import Http404

def get_or_create_cart(request):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        
    except KeyError: #no cart_id key in request.session, so create one
        cart = Cart(user=request.user,created_by=request.user,updated_by=request.user)
        cart.save()
        request.session['cart_id'] = cart.id

    return cart

def view_cart(request):
    empty_message = "Your cart is empty. Please keep shopping!"
    
    # don't create the cart if it does not exist 
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(id=cart_id)
        cart.refresh_cart(request.user)

        # # refresh cart items (e.g., if an item has gone on sale since adding to cart., the line total will need to be updated)
        # for item in cart.items.all():
        #     item.line_total = item.product.get_sale_price() * item.quantity
        #     item.save()
            
        # cart.total = cart.items.aggregate(Sum('line_total'))['line_total__sum']
        # cart.updated_by = request.user
        # cart.save()    
        
        context = {
            'cart': cart,
            'empty': cart.item_count == 0,
            'empty_message': empty_message,
        }

    except KeyError: #no cart_id key in request.session
        cart_id = None
        context = {
            'empty': True,
            'empty_message': empty_message,
        }

    template = 'cart/cart_detail.html'
    return render(request, template, context)

def add_to_cart(request,product_id):
    if request.method == "POST":
        quantity = request.POST.get('qty',1)

        try:
            quantity = int(quantity)
        except:
            raise Http404("Invalid quantity.")

        cart = get_or_create_cart(request)
        product = get_object_or_404(Product,pk=product_id)

        item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
        if not created: # the item was already
            item.quantity += quantity

        # item.line_total = item.product.price * float(item.quantity)
        item.line_total = item.product.get_sale_price() * item.quantity
        item.save()
        
        cart.item_count += quantity
        cart.total = cart.items.aggregate(Sum('line_total'))['line_total__sum']
        cart.updated_by = request.user
        cart.save()
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
            cart_id = request.session['cart_id']
            cart = Cart.objects.get(id=cart_id)
            
        except KeyError: #no cart_id key in request.session
            raise Http404("No cart exists. Cannot complete remove operation.")

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

        cart.item_count -= quantity
        cart.total = cart.items.aggregate(Sum('line_total'))['line_total__sum']
        cart.updated_by = request.user
        cart.save()
        request.session['cart_item_count'] = cart.item_count

        return HttpResponseRedirect(reverse('cart:cart_details'))
    else:
        return redirect('/')

def update_cart(request,product_id):
    # similar to add_to_cart(). however, this just updates quantity 
    # to whatever is in request.GET['qty']
    if request.method == "POST":
        quantity = request.POST.get('qty',1)

        try:
            quantity = int(quantity)
        except:
            raise Http404("Invalid quantity.")

        # if the cart does not exist, you can't remove anything from it
        try:
            cart_id = request.session['cart_id']
            cart = Cart.objects.get(id=cart_id)        
        except KeyError: #no cart_id key in request.session
            raise Http404("No cart exists. Cannot complete update operation.")

        product = get_object_or_404(Product,pk=product_id)

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
            item.line_total = item.product.get_sale_price() * item.quantity
            item.save()
        else:
            item.delete()

        items = cart.items.aggregate(Sum('line_total'), Sum('quantity'))
        cart.item_count = items['quantity__sum'] or 0
        cart.total = items['line_total__sum'] or 0
        cart.updated_by = request.user
        cart.save()
        request.session['cart_item_count'] = cart.item_count

        return HttpResponseRedirect(reverse('cart:cart_details'))
    else:
        return redirect("/")