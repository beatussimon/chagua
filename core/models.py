from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg

class User(AbstractUser):
    USER_TYPE_CHOICES = (('individual', 'Individual'), ('business', 'Business'))
    BADGE_CHOICES = (('blue', 'Blue'), ('green', 'Green'), ('gold', 'Gold'))
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='individual')
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_document = models.FileField(upload_to='verification_docs/', blank=True, null=True)
    trust_badge = models.BooleanField(default=False)
    badge_color = models.CharField(max_length=10, choices=BADGE_CHOICES, blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    is_custom_admin = models.BooleanField(default=False)
    admin_permissions = models.JSONField(default=dict)
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)
    theme_preference = models.CharField(max_length=10, choices=(('light', 'Light'), ('dark', 'Dark')), default='light')
    perfect_activity_since = models.DateTimeField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    def check_trust_badge(self):
        if not self.perfect_activity_since:
            self.perfect_activity_since = timezone.now()
        if (timezone.now() - self.perfect_activity_since).days >= 365 and not self.trust_badge:
            self.trust_badge = True
            self.save()

    def __str__(self):
        return self.username

class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=dict)  # e.g., {"boosted_posts": 5, "analytics": true}

    def __str__(self):
        return self.name

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()

    def is_active(self):
        return timezone.now() < self.end_date

class Team(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_teams')
    members = models.ManyToManyField(User, related_name='teams')

    def __str__(self):
        return self.name

class Rental(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='rentals')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    media = models.ManyToManyField('Media', blank=True)
    likes = models.ManyToManyField(User, related_name='liked_rentals', blank=True)
    views = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    boosted = models.BooleanField(default=False)

    def get_recommendation_score(self, user):
        score = self.views / 100
        if user in self.likes.all():
            score += 10
        if self.owner in user.following.all():
            score += 5
        if self.boosted or self.is_featured:
            score += 20
        return score

    def __str__(self):
        return self.title

class ServicePackage(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_packages')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rentals = models.ManyToManyField(Rental, related_name='packages')

    def __str__(self):
        return self.title

class Availability(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='availabilities')
    start_date = models.DateField()
    end_date = models.DateField()
    is_available = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=100, blank=True)  # e.g., "Every Saturday"

    def __str__(self):
        return f"{self.rental} - {self.start_date} to {self.end_date}"

class BookingQueue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} queued for {self.rental}"

class Media(models.Model):
    file = models.FileField(upload_to='rental_media/', max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media by {self.uploaded_by}"

class Comment(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.rental}"

class Contract(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('signed', 'Signed'), ('expired', 'Expired'))
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    tenant = models.ForeignKey(User, on_delete=models.CASCADE)
    terms = models.TextField()
    custom_terms = models.JSONField(default=dict)  # e.g., {"cancellation": "50% refund"}
    signature_image = models.ImageField(upload_to='signatures/', blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    emergency_clause = models.TextField(default="In case of emergency, tenant agrees to pay 10% of rental price.")

    def __str__(self):
        return f"Contract for {self.rental}"

class ContractTemplate(models.Model):
    name = models.CharField(max_length=100)
    terms = models.TextField()

    def __str__(self):
        return self.name

class Payment(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'))
    payer = models.ForeignKey(User, on_delete=models.CASCADE)
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, null=True, blank=True)
    package = models.ForeignKey(ServicePackage, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    instructions = models.TextField(default="Please transfer the amount to Chagua Bank Account: 123456789 via bank transfer or cash.")

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.transaction_id}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    group = models.ForeignKey('MessageGroup', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField(blank=False)
    attachment = models.FileField(upload_to='message_attachments/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender}"

class MessageGroup(models.Model):
    name = models.CharField(max_length=255)
    participants = models.ManyToManyField(User, related_name='message_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class MessageTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return f"Template by {self.user}"

class ScheduledMessage(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    send_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=(('pending', 'Pending'), ('sent', 'Sent')), default='pending')

class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, null=True, blank=True)
    package = models.ForeignKey(ServicePackage, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    media = models.ManyToManyField(Media, blank=True)
    is_anonymous = models.BooleanField(default=False)
    likes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Review by {self.reviewer}"

class FeedbackTrend(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    date = models.DateField()
    avg_rating = models.FloatField()

    class Meta:
        unique_together = ('rental', 'date')

class FeedbackDispute(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=(('open', 'Open'), ('resolved', 'Resolved')), default='open')

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.question

class SavedSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filters = models.JSONField()  # e.g., {"category": "cars", "price_max": 100}
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    content = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user}"

class Dispute(models.Model):
    STATUS_CHOICES = (('open', 'Open'), ('resolved', 'Resolved'), ('closed', 'Closed'))
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dispute by {self.raised_by}"

class Report(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    target_rental = models.ForeignKey(Rental, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report by {self.reporter}"

class Task(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    assignee = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=(('open', 'Open'), ('in_progress', 'In Progress'), ('done', 'Done')), default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Task for {self.rental}"

class ActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    target = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user}"