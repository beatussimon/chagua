from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings  # Import settings to access AUTH_USER_MODEL

class Media(models.Model):
    file = models.FileField(upload_to='rentals_media/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.file.size > 20 * 1024 * 1024:  # 20MB limit
            raise ValidationError("Media file must not exceed 20MB.")

class Rental(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rentals')
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_verified = models.BooleanField(default=False)
    media = models.ManyToManyField(Media, blank=True)
    verification_fee_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.price < 0:
            raise ValidationError("Price cannot be negative.")

    def verify_on_site(self, fee=50.00):
        if not self.verification_fee_paid:
            raise ValidationError(f"Verification fee of ${fee} must be paid.")
        self.is_verified = True
        self.save()

class ServicePackage(models.Model):
    rentals = models.ManyToManyField(Rental, related_name='packages')
    name = models.CharField(max_length=255)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def clean(self):
        if self.discount < 0 or self.discount > 100:
            raise ValidationError("Discount must be between 0 and 100%.")