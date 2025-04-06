from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

admin.site.register(User, UserAdmin)
admin.site.register([Category, SubscriptionPlan, UserSubscription, Team, Rental, ServicePackage, Availability, BookingQueue, Media, Comment, Contract, ContractTemplate, Payment, Message, MessageGroup, MessageTemplate, ScheduledMessage, Review, FeedbackTrend, FeedbackDispute, FAQ, SavedSearch, Notification, Dispute, Report, Task, ActionLog])