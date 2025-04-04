from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
import os

class User(AbstractUser):
    ROLE_CHOICES = (
        ('individual', 'Individual'),
        ('business', 'Business'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='individual')
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    trust_badge = models.BooleanField(default=False)
    premium_subscription = models.BooleanField(default=False)
    verification_documents = models.FileField(upload_to='verification_docs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    bio = models.TextField(blank=True, max_length=500)
    flagged = models.BooleanField(default=False)
    last_activity = models.DateTimeField(default=timezone.now)
    boosted_posts = models.PositiveIntegerField(default=0)

    def clean(self):
        if self.profile_picture and self.profile_picture.size > 5 * 1024 * 1024:
            raise ValidationError("Profile picture must not exceed 5MB.")
        if self.verification_documents:
            ext = os.path.splitext(self.verification_documents.name)[1].lower()
            if ext not in ['.pdf', '.jpg', '.png']:
                raise ValidationError("Only PDF, JPG, or PNG allowed for verification.")
            if self.verification_documents.size > 10 * 1024 * 1024:
                raise ValidationError("Verification file must not exceed 10MB.")

    def award_trust_badge(self):
        now = timezone.now()
        if (now.year - self.created_at.year >= 1 and 
            not self.reviews_received.filter(is_negative=True).exists() and 
            self.transactions.filter(status='completed').count() >= 5 and 
            not self.flagged):
            self.trust_badge = True
            self.save()
            return True
        return False

    def award_boosted_posts(self):
        if self.premium_subscription and self.boosted_posts < 10:
            self.boosted_posts = min(self.boosted_posts + 5, 10)  # Cap at 10
            self.save()

    def get_activity_stats(self):
        return {
            'rentals': self.rentals.count(),
            'reviews': self.reviews_received.count(),
            'messages': self.messages_sent.count(),
        }

class BusinessProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_profile')
    business_name = models.CharField(max_length=255)
    site_visit_verified = models.BooleanField(default=False)
    badge_color = models.CharField(max_length=20, default='blue', choices=[
        ('blue', 'Blue'), ('green', 'Green'), ('gold', 'Gold')
    ])
    verification_notes = models.TextField(blank=True)

    def verify_site(self):
        self.site_visit_verified = True
        self.verification_notes = f"Verified on {timezone.now()}"
        self.save()