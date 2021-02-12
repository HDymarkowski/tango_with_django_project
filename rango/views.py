from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from django.shortcuts import redirect
from django.urls import reverse
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime

def index(request):
    """
     Query the database for a list of ALL categories currently stored.
     Order the categories by the number of likes in descending order
     Retrieve the top 5 only -- or all if less than 5
     Place the list in our context_dict dictionary (with our boldmessage)
     that will be passed on to the template
    """
    category_list = Category.objects.order_by('-likes')[:5]
    top_5_pages = Page.objects.order_by('-views')[:5]

    # Construct a dictionary to pass to the template engine as its context
    # Note the key boldmessage matches to {{ boldmessage }} in the template
    context_dict = {}
    context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
    context_dict['categories'] = category_list
    context_dict['pages'] = top_5_pages

    visitor_cookie_handler(request)

    response =  render(request, 'rango/index.html', context=context_dict)
    return response

def about(request):
    context_dict = {}

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    return render(request, 'rango/about.html', context = context_dict)

def show_category(request, category_name_slug):
    context_dict = {}

    try:
        category = Category.objects.get(slug = category_name_slug)
        # Sees if the category page exists

        pages = Page.objects.filter(category = category)
        # Retreive all associated pages

        context_dict['pages'] = pages
        context_dict['category'] = category
        # Adds results to the context_dict

    except Category.DoesNotExist:
        # Gets here if the specified category does not exist
        #The templaye will displaye a "no category" message

        context_dict['category'] = None
        context_dict['pages'] = None

    return render(request, 'rango/category.html', context = context_dict)

@login_required
def add_category(request):
    form = CategoryForm()

    # Check if its a HTTP post i.e. did the user submit the data via the form
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Check if form is valid
        if form.is_valid():
            # Save new category to database
            form.save(commit=True)
            # Place confirmation of category being saved here
            return redirect('/rango/')
        else:
            # If the form is invalid
            print(form.errors)
    return render(request, 'rango/add_category.html', {'form': form})

@login_required
def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except:
        category = None
    
    # You cannot add a page to a Category that does not exist
    if category is None:
        return redirect('/rango/')

    form = PageForm()

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()

                return redirect(reverse('rango:show_category', kwargs={'category_name_slug': category_name_slug}))
        else:
            print(form.errors)  # This could be better done; for the purposes of TwD, this is fine
    
    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context=context_dict)

def register(request):
    # Boolean value telling the template if regestration was successful
    # Set to False initially, changed to True after successful registration
    registered = False

    # If if's a HTTP POST we're interested in processing form data
    if request.method == 'POST':
        # Grab info from the raw form info
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's data to the database
            user = user_form.save()

            # Next, we hash the password (with user.set_password) and update the user object
            user.set_password(user.password)
            user.save()

            # We need to set the user attribute ourselves so we do commit = False, delaying saving the model
            profile = profile_form.save(commit=False)
            profile.user = user

            # If the user provideed a profile picture get it from the form and put it in the model
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Finally, we actually save the UserProfile model instance
            profile.save()
            registered = True
        else:
            # Invalid form or forms
            print(user_form.errors, profile_form.errors)
    else:
        # Not an HTTP POST so we render our form using two ModelForm instances, blank and ready for user input
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context
    return render(request, 'rango/register.html', context = {'user_form': user_form,
     'profile_form': profile_form, 'registered': registered})

def user_login(request):
    # If the request is a HTTP POST, try to pull out the relevant information
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Use django's machinery to attempt to see if the username/passwork combo is valid
        # A user object is returned if it is
        user = authenticate(username=username, password=password)

        # if user checks if the details are correct and thus an object was returned
        if user:
            if user.is_active:
                login(request, user)
                return redirect(reverse('rango:index'))
            else:
                # An inactive account - no logging in
                return HttpResponse("Your Rango account is disabled")
        else:
            # Bad login details so we can't log the user in
            print(f"Invalid login details: {username}, {password}")
            return HttpResponse("Invalid login details supplied")
    else:
        # Request is not a HTTP POST, probably a HTTP GET
        return render(request, 'rango/login.html')

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html')
    # return HttpResponse("Since you're logged in, you can see this text!")

@login_required
def user_logout(request):
    logout(request)
    return redirect(reverse('rango:index'))


# Helper functions for cookies, not actually a view

def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    # Note: all cookies are strings

    # GET the number of visits tothe site
    # If cookie exists, we obtain the visits, otherwised default value = 1
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    # If it's been more than a day since the last visit...
    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        # Update the last visit cookie now that we have updated the count
        request.session['last_visit'] = str(datetime.now())
    else:
        # Set the last visit cookie
        request.session['last_visit'] = last_visit_cookie
    
    # Update/set the visits cookie
    request.session['visits'] = visits