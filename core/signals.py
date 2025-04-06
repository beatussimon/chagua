from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Rental, Review, Payment, Contract, ActionLog, FeedbackTrend, Notification
from django.db.models import Avg


@receiver(post_save, sender=Rental)
def log_rental_action(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    ActionLog.objects.create(user=instance.owner, action=f"Rental {action}", target=instance.title)

@receiver(post_save, sender=Review)
def update_feedback_trend(sender, instance, created, **kwargs):
    if created and instance.rental:
        date = instance.created_at.date()
        reviews = Review.objects.filter(rental=instance.rental, created_at__date=date)
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        FeedbackTrend.objects.update_or_create(rental=instance.rental, date=date, defaults={'avg_rating': avg_rating})

@receiver(post_save, sender=Payment)
def notify_payment(sender, instance, created, **kwargs):
    if created:
        target = instance.rental.owner if instance.rental else instance.package.owner
        Notification.objects.create(user=target, content=f"{instance.payer} made a payment: {instance.transaction_id}", link=f"/rental/{instance.rental.id}/" if instance.rental else f"/dashboard/")

@receiver(post_save, sender=Contract)
def notify_contract(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(user=instance.rental.owner, content=f"{instance.tenant} created a contract for {instance.rental}", link=f"/rental/{instance.rental.id}/")