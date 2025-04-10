from django.contrib import admin
from .models import UserProfile, RentalItem, Reservation, SocialPost, Review, UserAction, Message, Badge, UserBadge

admin.site.register(UserProfile)
admin.site.register(RentalItem)
admin.site.register(Reservation)
admin.site.register(SocialPost)
admin.site.register(Review)
admin.site.register(UserAction)
admin.site.register(Message)
admin.site.register(Badge)
admin.site.register(UserBadge)