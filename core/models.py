from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, FileExtensionValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, unique=True)
    currency = models.CharField(max_length=3, default='USD')
    tier = models.CharField(max_length=10, choices=[('free', 'Free'), ('green', 'Green'), ('blue', 'Blue'), ('gold', 'Gold')], default='free')
    verified = models.BooleanField(default=False)
    trusted = models.BooleanField(default=False)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class RentalItem(models.Model):
    TYPE_CHOICES = [('item', _('Item')), ('service', _('Service'))]
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    details = models.JSONField(default=dict)
    base_currency = models.CharField(max_length=3, default='KES')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    pricing_rules = models.JSONField(default=dict)  # e.g., {'weekend': 1.2, 'peak': 1.5}
    verified = models.BooleanField(default=False)
    image = models.ImageField(upload_to='items/%Y/%m/%d/', null=True, blank=True, validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    availability = models.JSONField(default=dict)
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    review_count = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Reservation(models.Model):
    STATUS_CHOICES = [('pending', _('Pending')), ('confirmed', _('Confirmed')), ('completed', _('Completed')), ('canceled', _('Canceled'))]
    renter = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(RentalItem, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    payment_proof = models.ImageField(upload_to='proofs/%Y/%m/%d/', null=True, blank=True, validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])])
    contract_agreed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.renter.username} - {self.item.title}"

class SocialPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(RentalItem, on_delete=models.CASCADE, null=True, blank=True)
    media = models.FileField(upload_to='posts/%Y/%m/%d/', null=True, blank=True, validators=[FileExtensionValidator(['mp4', 'jpg', 'jpeg', 'png'])])
    caption = models.CharField(max_length=280)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    comments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.caption[:50]

class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(RentalItem, on_delete=models.CASCADE, null=True, blank=True)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('reviewer', 'item'), ('reviewer', 'profile'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.item:
            reviews = Review.objects.filter(item=self.item)
            self.item.rating = sum(r.rating for r in reviews) / reviews.count()
            self.item.review_count = reviews.count()
            self.item.save()

class UserAction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.action}"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}"

class Badge(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)
    points_required = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')