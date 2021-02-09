from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from django.shortcuts import redirect
from django.urls import reverse
from rango.forms import PageForm

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

    # Return a rendered response ot send to the client
    # We make use of the hortcut function to make our lives easier
    # Note that the first parameter is the template we wish to use
    return render(request, 'rango/index.html', context=context_dict)

def about(request):
    return render(request, 'rango/about.html')

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