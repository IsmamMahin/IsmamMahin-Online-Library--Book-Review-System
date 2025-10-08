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
    
    # 🌟 FIX/IMPROVEMENT: Use annotate to calculate average rating efficiently in the DB
    # The calculated average will be available on each Book object as 'avg_score'
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
    
    # You might want to order by the calculated average rating here
    # books = books.order_by('-avg_score') 

    paginator = Paginator(books, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj' : page_obj,
        'categories' : Category.objects.all(),
        'search_query' : searchQ,
        'category_query' : categoryQ,
    }
    return render(request, 'book/book_list.html', context)

@login_required
def book_create(request):
    if request.method == 'POST':
        # The book creation form needs to handle potential image upload (for cover_image)
        form = forms.BookForm(request.POST, request.FILES) 
        if form.is_valid():
            book = form.save(commit=False)
            # 🐛 CRITICAL FIX: The Book model's 'author' field is a CharField, 
            # NOT a ForeignKey to User based on the model structure provided.
            # If the migration error fix involved changing this back to CharField,
            # you need to get the user's name or a related profile field.
            # Assuming 'author' is INTENDED to store the user's username for now:
            book.author = request.user.username 
            # If you fixed the migration to make 'author' a ForeignKey to User, 
            # then 'book.author = request.user' is correct. I'll stick to CharField 
            # to match the model provided in the first prompt.
            book.save()
            return redirect('book_list')
    else:
        form = forms.BookForm()
    
    return render(request, 'book/book_create.html', {'form' : form})

@login_required
def book_update(request, id):
    book = get_object_or_404(Book, id=id)
    
    # 💡 IMPROVEMENT: Check if the user is the author before allowing update
    # If the 'author' field is a CharField storing the username:
    if book.author != request.user.username:
        return redirect('book_details', id=book.id) # Or raise Http404/PermissionDenied

    if request.method == 'POST':
        # Handle file upload for cover_image
        form = forms.BookForm(request.POST, request.FILES, instance=book) 
        if form.is_valid():
            form.save()
            return redirect('book_details', id=book.id) # Redirect to details after update
    else: # GET
        # 🐛 CRITICAL FIX: Corrected form class name from PostForm to BookForm
        form = forms.BookForm(instance=book) 
    
    return render(request, 'book/book_create.html', {'form' : form})

@login_required
def book_delete(request, id):
    book = get_object_or_404(Book, id=id)
    
    # 💡 IMPROVEMENT: Check if the user is the author before allowing delete
    # If the 'author' field is a CharField storing the username:
    if book.author != request.user.username:
        return redirect('book_details', id=book.id) # Or raise Http404/PermissionDenied

    book.delete()
    return redirect('book_list')

@login_required
def book_details(request, id):
    # 🌟 IMPROVEMENT: Annotate the single book with its average rating 
    # to avoid the overhead of calling the @property (though it's efficient now)
    book = get_object_or_404(
        Book.objects.annotate(avg_score=Avg('rating__score')), 
        id=id
    )
    
    # comment and rating form handle
    if request.method == 'POST':
        form = forms.CommentForm(request.POST)
        score = request.POST.get('score')
        
        # Check if score is provided (it's required for the update_or_create logic)
        if score:
            try:
                score = int(score)
                # 1. RATING LOGIC: Update or create the rating
                Rating.objects.update_or_create(
                    user=request.user,
                    book=book,
                    defaults={'score': score}
                )
            except ValueError:
                # Handle case where score is not a valid integer
                pass # You may want to add error messages/messages.error here
        
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
    
    # 💡 IMPROVEMENT: Use select_related/prefetch_related to optimize queries
    # Prefetch the user for comments and ratings for the rating_score property
    comments = book.comment_set.all().select_related('user').order_by('-created_at')
    
    # Get the user's existing rating, if any, for the template
    user_rating = Rating.objects.filter(user=request.user, book=book).first()
    
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
                return redirect('/profile?section=update')
        else:
            form = forms.UpdateProfileForm(instance=request.user)
    
        context['form'] = form
    
    return render(request, 'user/profile.html', context)