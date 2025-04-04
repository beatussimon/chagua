from django.db import models
from django.core.files.base import ContentFile
from django.utils import timezone
from django.core.exceptions import ValidationError

class Contract(models.Model):
    rental = models.ForeignKey('rentals.Rental', on_delete=models.CASCADE)
    renter = models.ForeignKey('users.User', on_delete=models.CASCADE)
    terms = models.TextField()
    emergency_clause = models.TextField(default="In case of emergency, 10% of the total cost will be charged.")
    agreed_at = models.DateTimeField(null=True, blank=True)
    contract_file = models.FileField(upload_to='contracts/', null=True, blank=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'), ('agreed', 'Agreed'), ('completed', 'Completed'), ('disputed', 'Disputed')
    ])

    def clean(self):
        if len(self.terms) < 50:
            raise ValidationError("Terms must be at least 50 characters.")

    def generate_contract_file(self):
        content = f"Contract for {self.rental.title}\nRenter: {self.renter.username}\nOwner: {self.rental.owner.username}\nTerms: {self.terms}\nEmergency Clause: {self.emergency_clause}\nAgreed At: {self.agreed_at or 'Pending'}"
        self.contract_file.save(f"contract_{self.id}_{timezone.now().strftime('%Y%m%d')}.txt", ContentFile(content))