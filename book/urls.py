from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.book_list, name = 'book_list'),
    path('books/create', views.book_create, name = 'book_create'),
    path('books/update/<int:id>/', views.book_update, name = 'book_update'),
    path('books/delete/<int:id>/', views.book_delete, name = 'book_delete'),
    # path('books/rate/<int:id>/', views.rate_book, name = 'rate_book'),
    path('books/details/<int:id>/', views.book_details, name = 'book_details'),
    path('signup/', views.signup_view, name = 'signup_view'),
    path('login/', LoginView.as_view(template_name='user/login.html'), name = 'login'),
    path('logout/', LogoutView.as_view(), name = 'logout'),
    path('profile/', views.profile_view, name = 'profile'),
]