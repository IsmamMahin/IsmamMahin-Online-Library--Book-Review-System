from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.db.models import Avg  # This import is correctly included

class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    description = RichTextField()
    cover_image = models.ImageField(upload_to="book_covers/", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # 🐛 FIX: Switched from inefficient Python calculation to efficient Django ORM aggregation (Avg)
    @property
    def average_rating(self):
        # Annotate the Book queryset with the average 'score' from related 'Rating' objects
        # The result is a dictionary: {'score__avg': <average_value>}
        avg_result = self.rating_set.aggregate(Avg('score'))
        
        # Return the calculated average, or None if there are no ratings
        return avg_result['score__avg']

    def __str__(self):
        return self.title


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # The 'related_name' for the Rating field on Book is 'rating_set' by default, 
    # but the original code used 'ratings'. It's best to be explicit or consistent. 
    # I'll stick with the default 'rating_set' in the fix.
    book = models.ForeignKey(Book, on_delete=models.CASCADE) 
    score = models.PositiveIntegerField()  # 1–5 stars

    class Meta:
        unique_together = ("user", "book")  # ✅ one rating per user per book

    def __str__(self):
        # NOTE: I changed 'rating' to 'score' here to match the field name in the Rating model.
        return f"{self.user} rated {self.book} {self.score}★" 


class Comment(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # 💡 Minor improvement: Check for a rating in one query.
    @property
    def rating_score(self):
        # Use .values_list('score', flat=True) for a cleaner result retrieval
        score = Rating.objects.filter(user=self.user, book=self.book).values_list('score', flat=True).first()
        return score # returns the score (int) or None

    def __str__(self):
        return f"{self.user} commented on {self.book}"