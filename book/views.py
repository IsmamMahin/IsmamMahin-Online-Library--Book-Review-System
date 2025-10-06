from django.shortcuts import render, redirect, get_object_or_404
from .models import Book, Comment, Category, Tag, Rating
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator
from . import forms
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
# Create your views here.
# Book list 
# category, tag, search 

def book_list(request):
    categoryQ = request.GET.get('category') # python
    tagQ = request.GET.get('tag')
    searchQ = request.GET.get('q')
    
    books = Book.objects.all() # all book ke anlam
    
    if categoryQ:
        books = books.filter(category__name = categoryQ)
    if tagQ:
        books = books.filter(tag__name = tagQ)
    if searchQ:
        books = books.filter(
            Q(title__icontains = searchQ) |
            Q(description__icontains = searchQ) | 
            Q(category__name__icontains = searchQ) | 
            Q(tag__name__icontains = searchQ) 
        ).distinct()
    
    paginator = Paginator(books, 2) # per page a 2 ta kore book dekhabe
    # 100 ta book ache, per page e 10 ta book hole, total 10 ta page lagbe
    page_number = request.GET.get('page') # ?page=8
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj' : page_obj,
        'categories' : Category.objects.all(),
        'tags' : Tag.objects.all(),
        'search_query' : searchQ,
        'category_query' : categoryQ,
        'tag_query' : tagQ,
    }
    return render(request, 'blog/book_list.html', context)

@login_required
def book_create(request):
    if request.method == 'POST':
        form = forms.BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.author = request.user
            book.save()
            return redirect('book_list')
    else:
        form = forms.BookForm()
    
    return render(request, 'blog/book_create.html', {'form' : form})

@login_required
def book_update(request, id):
    book = get_object_or_404(Book, id=id)
    if request.method == 'POST':
        form = forms.BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else: # get
        form = forms.PostForm(instance=book)
    
    return render(request, 'blog/book_create.html', {'form' : form})

@login_required
def book_delete(request, id):
    book = get_object_or_404(Book, id=id)
    book.delete()
    return redirect('book_list')

@login_required
def book_details(request, id):
    book = get_object_or_404(book, id=id)
    
    # comment form handle
    if request.method == 'POST':
        form = forms.CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.book = book
            comment.save()
            return redirect('book_details', id=book.id)
    else:
        form = forms.CommentForm()
    
    # show comments
    comments = book.comment_set.all()
    is_liked = book.liked_users.filter(id=request.user.id).exists()
    like_count = book.liked_users.count()
    # liked part
    # like count
    
    context = {
        'book' : book,
        'categories' : Category.objects.all(),
        'tag' : Tag.objects.all(),
        'comments' : comments,
        'is_liked' : is_liked,
        'like_count' : like_count,
        'comment_form' : forms.CommentForm
    }
    
    book.save()
    return render(request, 'blog/book_details.html', context)

@login_required
@require_POST  # Only allow POST requests for safety and clarity
def rate_book(request, id):
    # 1. Get the Book instance
    book = get_object_or_404(Book, id=id)

    # 2. Get the rating score from the POST data
    #    You'll need to name your form/input field 'score' 
    #    Use .get() and provide a default to prevent KeyErrors
    score = request.POST.get('score') 
    
    # Basic validation for the score
    # if not score or not score.isdigit() or not (1 <= int(score) <= 5):
    #     messages.error(request, "Invalid rating score. Please choose a score between 1 and 5.")
    #     return redirect('book_details', id=book.id)

    score = int(score)

    # 3. Try to find an existing Rating for the current user and book
    rating, created = Rating.objects.update_or_create(
        user=request.user,
        book=book,
        defaults={'score': score}
    )

    # if created:
    #     messages.success(request, f"Successfully rated '{book.title}' with a score of {score}.")
    # else:
    #     messages.info(request, f"Updated your rating for '{book.title}' to {score}.")
    
    return redirect('book_details', id=book.id)     

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # login
            login(request, user)
            return redirect('book_list')
    else:
        form = UserCreationForm()
    
    return render(request, 'user/signup.html', {'form' : form})


# Profile page
@login_required
def profile_view(request):
    section = request.GET.get('section', 'profile')
    context = {'section' : section}
    
    if section == 'books':
        books = Book.objects.filter(author = request.user)
        context['books'] = books 
    
    elif section == 'update':
        if request.method == 'POST':
            form = forms.UpdateProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                return redirect('/profile?section=update')
        else:
            form = forms.UpdateProfileForm(instance=request.user)
    
        context['form'] = form
    
    return render(request, 'user/profile.html', context)