from django.shortcuts import render, redirect, get_object_or_404
from .models import Book, Comment, Category, Rating
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator
from . import forms
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg # Used for efficient database aggregation

# Create your views here.
# Book list 
# category, search 

def book_list(request):
    categoryQ = request.GET.get('category')
    searchQ = request.GET.get('q')

    books = Book.objects.all().annotate(
        avg_score=Avg('rating__score')
    )
    
    if categoryQ:
        books = books.filter(category__name = categoryQ)
    if searchQ:
        books = books.filter(
            Q(title__icontains = searchQ) |
            Q(description__icontains = searchQ) | 
            Q(category__name__icontains = searchQ) 
        ).distinct()
    
    # books = books.order_by('-avg_score') 

    paginator = Paginator(books, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj' : page_obj,
        'categories' : Category.objects.all().order_by('name'),
        'search_query' : searchQ,
        'categoryQ' : categoryQ,
    }
    return render(request, 'book/book_list.html', context)

# @login_required
# def book_create(request):
#     if request.method == 'POST':
#         # The book creation form needs to handle potential image upload (for cover_image)
#         form = forms.BookForm(request.POST, request.FILES) 
#         if form.is_valid():
#             book = form.save(commit=False)            
#             book.save()
#             return redirect('book_list')
#     else:
#         form = forms.BookForm()
    
#     return render(request, 'book/book_create.html', {'form' : form})

# @login_required
# def book_update(request, id):
#     book = get_object_or_404(Book, id=id)
    
#     # 💡 IMPROVEMENT: Check if the user is the author before allowing update
#     # If the 'author' field is a CharField storing the username:
#     if book.author != request.user.username:
#         return redirect('book_details', id=book.id) # Or raise Http404/PermissionDenied

#     if request.method == 'POST':
#         # Handle file upload for cover_image
#         form = forms.BookForm(request.POST, request.FILES, instance=book) 
#         if form.is_valid():
#             form.save()
#             return redirect('book_details', id=book.id) # Redirect to details after update
#     else: # GET
#         # 🐛 CRITICAL FIX: Corrected form class name from PostForm to BookForm
#         form = forms.BookForm(instance=book) 
    
#     return render(request, 'book/book_create.html', {'form' : form})

# @login_required
# def book_delete(request, id):
#     book = get_object_or_404(Book, id=id)
    
#     if book.author != request.user.username:
#         return redirect('book_details', id=book.id) # Or raise Http404/PermissionDenied

#     book.delete()
#     return redirect('book_list')

def book_details(request, id):
    # 🌟 IMPROVEMENT: Annotate the single book with its average rating 
    book = get_object_or_404(
        Book.objects.annotate(avg_score=Avg('rating__score')), 
        id=id
    )
    
    # comment and rating form handle
    if request.method == 'POST':
        # 🔒 SECURITY: Check if user is logged in for POST requests
        if not request.user.is_authenticated:
            # If an anonymous user tries to submit, redirect them to login
            return redirect('login') 
            
        form = forms.CommentForm(request.POST)
        score = request.POST.get('score')
        
        # Check if score is provided (it's required for the update_or_create logic)
        if score:
            try:
                score = int(score)
                # 1. RATING LOGIC: Update or create the rating
                Rating.objects.update_or_create(
                    user=request.user, # request.user is safe here because of the 'if not request.user.is_authenticated' check above
                    book=book,
                    defaults={'score': score}
                )
            except ValueError:
                pass 
        
        # 2. COMMENT LOGIC: Save the comment if content is provided
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.book = book
            comment.save()
            
        # Redirect to prevent resubmission and show updated data
        return redirect('book_details', id=book.id)

    else:
        # GET request: initialize empty comment form
        form = forms.CommentForm()
    
    # 💡 FIX/IMPROVEMENT: Safely get the user's existing rating for the template
    user_rating = None
    if request.user.is_authenticated:
        # This only runs if request.user is a real User object, avoiding TypeError
        user_rating = Rating.objects.filter(user=request.user, book=book).first()

    # Prefetch the user for comments (visible to everyone)
    comments = book.comment_set.all().select_related('user').order_by('-created_at')
    
    context = {
        'book' : book,
        'categories' : Category.objects.all(),
        'comments' : comments,
        'comment_form' : form,
        'user_rating' : user_rating.score if user_rating else None, # Pass existing score
    }
    
    return render(request, 'book/book_details.html', context)

# ... (rest of the views remain the same) ...

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
        # 💡 Filter by the CharField 'author' which stores the username
        books = Book.objects.filter(author = request.user.username)
        
        # 🌟 IMPROVEMENT: Annotate books for profile list too
        books = books.annotate(avg_score=Avg('rating__score')) 
        
        context['books'] = books 
    
    elif section == 'update':
        if request.method == 'POST':
            # 🐛 CRITICAL FIX: The form instantiation needs to handle file uploads
            form = forms.UpdateProfileForm(request.POST, request.FILES, instance=request.user) 
            if form.is_valid():
                form.save()
                return redirect('book_list')
        else:
            form = forms.UpdateProfileForm(instance=request.user)
    
        context['form'] = form
    
    return render(request, 'user/profile.html', context)