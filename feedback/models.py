from django.db import models

class Review(models.Model):
    reviewer = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reviews_given')
    reviewed = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    media = models.ManyToManyField('rentals.Media', blank=True)
    is_negative = models.BooleanField(default=False)
    likes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.is_negative = self.rating <= 2
        super().save(*args, **kwargs)

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    helpful_votes = models.IntegerField(default=0)
    user_contribution = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)