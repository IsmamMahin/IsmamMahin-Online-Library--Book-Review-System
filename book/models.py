from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name
    
class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    description = RichTextField()
    
    # Tags needed to connect
    tag = models.ManyToManyField(Tag, related_name='book')

    ratings = models.ManyToManyField(User, through='Rating', related_name='rated_books')

    def __str__(self):
        return self.title
    
    @property
    def average_rating(self):
        return self.rating_set.aggregate(models.Avg('score'))['score__avg'] or 0.00


class Rating(models.Model):
    # A foreign key to the User who submitted the rating
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # A foreign key to the Book that was rated
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    
    # The actual rating score (e.g., 1 to 5)
    # Use PositiveSmallIntegerField for small integers like ratings
    score = models.PositiveSmallIntegerField(
        default=5,
        choices=[(i, i) for i in range(1, 6)] # Define choices for a 1-5 rating
    )

    class Meta:
        # Ensures a user can only submit one rating per book
        unique_together = ('user', 'book')
        
    def __str__(self):
        return f'{self.book.title} rated {self.score} by {self.user.username}'

class Comment(models.Model):
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username