import pytz
import os
import json
import random

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView

from shop.services import getPhotoFromURL

from .forms import SignUpForm
from shop.models import *

user_data = None

def set_timezone(request,profiled_user_id):
    if request.method == 'POST':
        print(f'Setting timezone for user {profiled_user_id}')
        request.session['django_timezone'] = request.POST['timezone']
        user_profile = UserProfile.objects.get(user_id = profiled_user_id)
        user_profile.time_zone = request.session['django_timezone']
        user_profile.save()
        # return redirect('/')
        return redirect(user_profile.get_absolute_url())
    else:
        return render(request, 'accounts/template.html', {'timezones': pytz.common_timezones})

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('/')
    
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})

def user_profile(request,profiled_user_id):
    profiled_user = (
        User.objects
        .select_related('profile')
        .prefetch_related(
            'ratings__product__product_photos',
            'questions_asked__product__product_photos',
            'questions_followed__product__product_photos',
            'product_answers__question__product__product_photos',
        )
        .get(id=profiled_user_id)
    )

    location = profiled_user.profile.location or None

    # average_rating_old = (
    #     Rating.objects.filter(user=profiled_user)
    #     .aggregate(
    #         Avg('number_of_stars')
    #     )['number_of_stars__avg'] or 0
    # )

    all_ratings = profiled_user.ratings.all()

    average_rating = (
        all_ratings
        .aggregate(
            Avg('number_of_stars')
        )['number_of_stars__avg'] or 0
    )

    all_questions_followed = profiled_user.questions_followed.all().order_by('product')
    all_questions_asked = profiled_user.questions_asked.all().order_by('product')
    all_answers = profiled_user.product_answers.all().order_by('question__product')

    context = {
        'user': request.user,
        'profiled_user': profiled_user,
        'location': location,
        'user_average_rating' : average_rating,
        'all_ratings' : all_ratings,
        'all_questions_followed': all_questions_followed,
        'all_questions_asked': all_questions_asked,
        'all_answers': all_answers,
    }
    return render(request, 'registration/user-profile.html', context)

def update_user_profile(request, profiled_user_id):
    profiled_user = User.objects.get(id=profiled_user_id)
    profile = profiled_user.profile

    if request.method == 'POST':

        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():

            profile = form.save(commit=False)

            # if the user deleted the previous photo, add the default photo
            if form.cleaned_data['profile_pic'] == None or form.cleaned_data['profile_pic'] == False:
                profile.profile_pic = UserProfile._meta.get_field('profile_pic').get_default()

            request.session['django_timezone'] = form.cleaned_data['time_zone']

            #save the profile and then save the many-to-many data from the form
            profile.save()

            # If your model has a many-to-many relation and you specify commit=False when you save a form, 
            # Django cannot immediately save the form data for the many-to-many relation.
            # Manually save many-to-many data
            form.save_m2m() 

            # save the new timezone to session variable

            return redirect(f'/registration/{profiled_user_id}')
    
    else: #this is a GET request so create a blank form
        form = UserProfileForm(instance=profile)
    
    context = {
        'user': request.user,
        'profiled_user': profiled_user,
        'form': form,
        'action': 'Update',
    }
    return render(request,'registration/user-profile-form.html', context)

@staff_member_required
def getTestData(request):
    global user_data

    path = os.path.join(settings.BASE_DIR, 'accounts\\static\\accounts\\test_users.json') 
    # print(f'Path: {path}')
    with open(path, 'r') as data:
        user_data = json.load(data)

    # print('Users: ')
    for user in user_data["results"]:
        # print(f'{user["name"]["first"]} {user["name"]["last"]}',end=' ')
        user['created'] = False
        user['user_id'] = None
    
    # print()
    # print(user_data)

@staff_member_required
def testdata(request):
    global user_data

    if user_data == None:
        print('User data is empty. Calling getTestData().')
        getTestData(request)
    else:
        print('Test data is loaded already')

    if user_data == None:
        print('User data is STILL empty.')
    else:
        print('Test data has been loaded.')

    for user in user_data['results']:
        # for test data, don't allow users with same full name
        users_with_same_name = User.objects.filter(first_name=user["name"]["first"], last_name=user["name"]["last"])
        if users_with_same_name.exists():
            # get first item from queryset and save to the current user in userdata'
            user.update({
                'created': True,
                'user_id': users_with_same_name[0].id,
            })

    context = {
        'user_data': user_data,
        'test_data': True,
    }
    return render(request, 'registration/test-data.html',context)

@staff_member_required
def create_users(request):
    global user_data

    if user_data == None:
        getTestData(request)

    i = 0
    for user in user_data["results"]:

        # Don't create the same user (user['created'] resets every runserver)
        if user['created']:
            print(f'{user["name"]["first"]} {user["name"]["last"]} was already in the database. Skipping.')
            continue

        # don't allow users under 13
        if user["dob"]["age"] <= 13:            
            print(f'{user["name"]["first"]} {user["name"]["last"]} is under age. Skipping.')
            continue

        # for test data, don't allow users with same full name
        users_with_same_name = User.objects.filter(first_name=user["name"]["first"], last_name=user["name"]["last"])
        if users_with_same_name.exists():
            print(f'Someone with the name \'{user["name"]["first"]} {user["name"]["last"]}\' already registered. Skipping.')
            messages.info(request,f'{user["name"]["first"]} {user["name"]["last"]} is already registered. Skipping.') 

            'get first item from queryset and save to the current user in userdata'
            user.update({
                'created': True,
                'user_id': users_with_same_name[0].id,
            })

            continue

        try:
            new_user = User.objects.create_user(user["email"],user["email"],settings.DEFAULT_TEST_PASSWORD)
            print(f'{user["name"]["first"]} {user["name"]["last"]} created.')

        except:
            error = f'Error registering {user["name"]["first"]} {user["name"]["last"]}'
            print(error)
            messages.add_message(request,messages.ERROR,error)
            continue
        
        new_user.first_name = user["name"]["first"]
        new_user.last_name = user["name"]["last"]
        new_user.save()

        new_user.profile.location = user["location"]["city"]
        new_user.profile.bio = "**TEST USER** Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec ac fringilla ex. Integer in dictum justo, id ornare sapien. Phasellus id tempus odio. Vestibulum vitae ultrices tellus. Quisque id nisi nec tortor hendrerit suscipit. Pellentesque et viverra sapien, interdum iaculis ex. Quisque viverra lacus malesuada, maximus felis eu, mollis nisl. Nunc vel rutrum lorem. Morbi quis lobortis mauris, in lacinia justo. Mauris semper, magna eget mollis gravida, nisi felis mattis tortor, ut volutpat mi dui nec libero."
        new_user.profile.birthday = parse_date(user["dob"]["date"]) #user["dob"]["date"][0:10]
        new_user.profile.save()
        print(f'Profile created for {user["name"]["first"]} {user["name"]["last"]}.')

        filename = user['picture']['medium'].split('/')[-1]
        image = getPhotoFromURL(user['picture']['medium'],filename) 
        if image != '':
            print(f'About to save image \'{filename}\' for user {user["name"]["first"]} {user["name"]["last"]}.')
            
            try:
                new_user.profile.profile_pic = image #.save(filename, image, save=True)
                new_user.profile.save()
                print(f'Image saved.')
            except:
                print(f'Image \'{filename}\' for user {user["name"]["first"]} {user["name"]["last"]} could not be saved.')
                pass

        user.update({
            'created': True,
            'user_id': new_user.id,
        })
        print(f'User data json updated for user {user["name"]["first"]} {user["name"]["last"]}.')

        num_favorites = random.randint(1,8) #get a random number of favorites
        num_products = Product.objects.count()
        print(f'Attempting to create {num_favorites} favorites from {num_products} products.')

        for j in range(num_favorites):
            # get a random number and try to identify it with a product_id.
            # because of deletions, not every product id will exist
            product_id = random.randint(1,num_products)
            try:
                product = Product.objects.get(id=product_id)
                new_user.profile.favorites.add(product)
                new_user.profile.save()
                print(f'Saved product {product.name} to {user["name"]["first"]}\'s favorites.')

            except Product.DoesNotExist:
                print(f'Could not identify a product for product_id #{product_id}.')

            if product.questions.count():
                product.questions.first().followers.add(new_user)
                product.questions.first().save()

        print(f'{user["name"]["first"]} {user["name"]["last"]}\'s favorites: {new_user.profile.favorites.values("name")}.')

        message = f"SUCCESS! Registered {new_user.get_full_name()}."
        messages.success(request,message)
        print(f'Finished with {user["name"]["first"]} {user["name"]["last"]}.')
        
        i += 1
        if i > 2:
            break 

    return redirect('accounts:test_data')   #('/testing')

@staff_member_required
def reset_users(request):

    for one_user in User.objects.all():
        print(f"Updating profile picture for {one_user.get_full_name()} to {UserProfile._meta.get_field('profile_pic').get_default()}.")
        
        if len(one_user.profile.bio) >= 13 and one_user.profile.bio[:13] != "**TEST USER**":
            one_user.profile.profile_pic = UserProfile._meta.get_field('profile_pic').get_default()
            one_user.profile.save()

    return redirect('accounts:test_data')   #('/testing')

