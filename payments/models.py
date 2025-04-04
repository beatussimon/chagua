from django.db import models
from django.core.exceptions import ValidationError

class Transaction(models.Model):
    contract = models.ForeignKey('contracts.Contract', on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_instructions = models.TextField(default="Please pay via bank transfer to account XYZ or in cash to the owner.")
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'), ('completed', 'Completed')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.amount < 0:
            raise ValidationError("Amount cannot be negative.")