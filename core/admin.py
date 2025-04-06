from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
import os
from .models import (
    User, Category, SubscriptionPlan, UserSubscription, Team, Rental,
    ServicePackage, Availability, BookingQueue, Media, Comment, Contract,
    ContractTemplate, Payment, Message, MessageGroup, MessageTemplate,
    Review, FeedbackTrend, FeedbackDispute, FAQ, SavedSearch,
    Notification, Dispute, Report, Task, ActionLog
)

# --- Inlines ---
class MediaInline(admin.TabularInline):
    model = Rental.media.through
    extra = 1
    verbose_name = _("Associated Media")
    verbose_name_plural = _("Associated Media")

class AvailabilityInline(admin.TabularInline):
    model = Availability
    extra = 1
    fields = ('start_date', 'end_date', 'is_available')

class ReviewInline(admin.TabularInline):
    model = Review
    fk_name = 'rental'
    extra = 0
    fields = ('reviewer', 'rating', 'comment_preview', 'created_at', 'is_anonymous')
    readonly_fields = ('reviewer', 'rating', 'comment_preview', 'created_at', 'is_anonymous')
    can_delete = False
    def comment_preview(self, obj): return obj.comment[:50] + ('...' if len(obj.comment) > 50 else '')
    comment_preview.short_description = 'Comment'
    def has_add_permission(self, request, obj=None): return False

class TaskInline(admin.TabularInline):
    model = Task
    fk_name = 'rental'
    extra = 1
    fields = ('description', 'assignee', 'status', 'due_date')

class MessageInline(admin.TabularInline):
    model = Message
    fk_name = 'group'
    extra = 0
    fields = ('sender', 'content_preview', 'timestamp', 'is_read')
    readonly_fields = ('sender', 'content_preview', 'timestamp', 'is_read')
    can_delete = False
    def content_preview(self, obj): return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    content_preview.short_description = 'Content'
    def has_add_permission(self, request, obj=None): return False

# --- Custom ModelAdmins ---

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_verified', 'trust_badge', 'is_premium', 'is_custom_admin', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'is_verified', 'trust_badge', 'is_premium', 'is_custom_admin', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'perfect_activity_since')
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Chagua Profile'), {'fields': ('user_type', 'phone_number', 'profile_picture', 'bio', 'city', 'country', 'theme_preference')}),
        (_('Verification & Status'), {'fields': ('is_verified', 'verification_document', 'trust_badge')}),
        (_('Premium & Admin'), {'fields': ('is_premium', 'badge_color', 'is_custom_admin', 'admin_permissions')}),
        (_('Activity Tracking'), {'fields': ('perfect_activity_since',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
         (_('Chagua Profile Info'), {'fields': ('user_type', 'email', 'phone_number')}),
    )
    actions = ['make_verified', 'make_premium', 'grant_trust_badge']
    @admin.action(description=_('Mark selected users as verified'))
    def make_verified(self, request, queryset): queryset.update(is_verified=True); self.message_user(request, _(f"{queryset.count()} users marked as verified."), messages.SUCCESS)
    @admin.action(description=_('Mark selected users as premium'))
    def make_premium(self, request, queryset): queryset.update(is_premium=True); self.message_user(request, _(f"{queryset.count()} users marked as premium."), messages.SUCCESS)
    @admin.action(description=_('Grant Trust Badge to selected users'))
    def grant_trust_badge(self, request, queryset): queryset.update(trust_badge=True); self.message_user(request, _(f"{queryset.count()} users granted trust badge."), messages.SUCCESS)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'feature_summary')
    search_fields = ('name',)
    def feature_summary(self, obj): return ", ".join(f"{k}: {v}" for k, v in obj.features.items()); feature_summary.short_description = 'Features'

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active')
    list_filter = ('plan', 'end_date')
    search_fields = ('user__username',)
    readonly_fields = ('start_date',)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'member_count')
    search_fields = ('name', 'owner__username', 'members__username')
    filter_horizontal = ('members',)
    def member_count(self, obj): return obj.members.count(); member_count.short_description = 'Members'

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'price', 'is_verified', 'is_featured', 'boosted', 'created_at', 'view_count_display')
    list_filter = ('category', 'is_verified', 'is_featured', 'boosted', 'city', 'country', 'created_at')
    search_fields = ('title', 'description', 'owner__username', 'city', 'country')
    list_editable = ('is_verified', 'is_featured', 'boosted')
    readonly_fields = ('created_at', 'views') # Removed updated_at
    inlines = [AvailabilityInline, TaskInline, ReviewInline]
    fieldsets = (
        (None, {'fields': ('owner', 'team', 'title', 'description', 'category')}),
        (_('Pricing & Location'), {'fields': ('price', 'city', 'country', 'latitude', 'longitude')}),
        (_('Status & Visibility'), {'fields': ('is_verified', 'is_featured', 'boosted', 'views')}),
        (_('Dates'), {'fields': ('created_at',)}),
        (_('Media'), {'fields': ('media',)})
    )
    filter_horizontal = ('media',)
    actions = ['verify_rentals', 'feature_rentals']
    def view_count_display(self, obj): return obj.views; view_count_display.short_description = 'Views'
    @admin.action(description=_('Mark selected rentals as verified'))
    def verify_rentals(self, request, queryset): queryset.update(is_verified=True); self.message_user(request, _(f"{queryset.count()} rentals verified."), messages.SUCCESS)
    @admin.action(description=_('Mark selected rentals as featured'))
    def feature_rentals(self, request, queryset): queryset.update(is_featured=True); self.message_user(request, _(f"{queryset.count()} rentals featured."), messages.SUCCESS)

@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'price')
    list_filter = ('category',)
    search_fields = ('title', 'description', 'owner__username')
    filter_horizontal = ('rentals',)

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'uploaded_by', 'uploaded_at')
    search_fields = ('file', 'uploaded_by__username')
    readonly_fields = ('uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    def file_name(self, obj): return os.path.basename(obj.file.name); file_name.short_description = 'Filename'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'rental', 'content_preview', 'created_at', 'parent_comment')
    search_fields = ('content', 'user__username', 'rental__title')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    def content_preview(self, obj): return obj.content[:50] + ('...' if len(obj.content) > 50 else ''); content_preview.short_description = 'Content'
    def parent_comment(self, obj): return obj.parent.id if obj.parent else '-'; parent_comment.short_description = 'Parent ID'

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'rental', 'tenant', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('rental__title', 'tenant__username', 'terms')
    list_editable = ('status',)
    readonly_fields = ('signature_image_display',)
    fields = ('rental', 'tenant', 'terms', 'custom_terms', 'emergency_clause', 'start_date', 'end_date', 'status', 'signature_image', 'signature_image_display')
    def signature_image_display(self, obj):
        if obj.signature_image: return format_html('<img src="{}" width="150" />', obj.signature_image.url)
        return "N/A"
    signature_image_display.short_description = 'Signature Preview'

@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'terms')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'payer', 'target_object', 'amount', 'payment_date', 'status')
    list_filter = ('status', 'payment_date')
    search_fields = ('transaction_id', 'payer__username', 'rental__title', 'package__title', 'subscription__plan__name')
    list_editable = ('status',)
    readonly_fields = ('payment_date', 'transaction_id')
    actions = ['approve_payments', 'reject_payments']
    def target_object(self, obj): return obj.rental or obj.package or obj.subscription; target_object.short_description = 'For'
    @admin.action(description=_('Approve selected payments'))
    def approve_payments(self, request, queryset): queryset.update(status='approved'); self.message_user(request, _(f"{queryset.count()} payments approved."), messages.SUCCESS)
    @admin.action(description=_('Reject selected payments'))
    def reject_payments(self, request, queryset): queryset.update(status='rejected'); self.message_user(request, _(f"{queryset.count()} payments rejected."), messages.SUCCESS)

@admin.register(MessageGroup)
class MessageGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'participant_list')
    search_fields = ('name', 'participants__username')
    filter_horizontal = ('participants',)
    inlines = [MessageInline]
    def participant_list(self, obj): return ", ".join([p.username for p in obj.participants.all()]); participant_list.short_description = 'Participants'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'group', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read')
    search_fields = ('content', 'sender__username', 'recipient__username', 'group__name')
    readonly_fields = ('timestamp',)
    list_display_links = ('content_preview',)
    def content_preview(self, obj): return obj.content[:50] + ('...' if len(obj.content) > 50 else ''); content_preview.short_description = 'Content'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'target_object', 'rating', 'is_anonymous', 'created_at', 'likes')
    list_filter = ('rating', 'is_anonymous', 'created_at')
    search_fields = ('comment', 'reviewer__username', 'rental__title', 'package__title')
    readonly_fields = ('created_at', 'likes')
    actions = ['mark_anonymous']
    filter_horizontal = ('media',)
    def target_object(self, obj): return obj.rental or obj.package; target_object.short_description = 'Reviewed Item'
    @admin.action(description=_('Mark selected reviews as anonymous'))
    def mark_anonymous(self, request, queryset): queryset.update(is_anonymous=True); self.message_user(request, _(f"{queryset.count()} reviews marked anonymous."), messages.SUCCESS)

# --- FIX FOR FeedbackDisputeAdmin ---
@admin.register(FeedbackDispute)
class FeedbackDisputeAdmin(admin.ModelAdmin):
    # REMOVED 'created_at' from list_display
    list_display = ('review_link', 'user', 'reason_preview', 'status')
    # REMOVED 'created_at' from list_filter
    list_filter = ('status',)
    list_editable = ('status',)
    search_fields = ('reason', 'user__username', 'review__comment')
    # REMOVED 'created_at' from readonly_fields
    readonly_fields = () # Let Django handle auto_now_add implicitly

    # Display created_at in the detail view explicitly if needed (it should appear anyway)
    fields = ('review', 'user', 'reason', 'status', 'created_at')

    def reason_preview(self, obj): return obj.reason[:50] + ('...' if len(obj.reason) > 50 else ''); reason_preview.short_description = 'Reason'
    def review_link(self, obj): link = reverse("admin:core_review_change", args=[obj.review.id]); return format_html('<a href="{}">Review #{}</a>', link, obj.review.id); review_link.short_description = 'Review'

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    # REMOVED 'category' from list_display
    list_display = ('question', 'created_by', 'created_at', 'likes')
    # REMOVED category filter
    list_filter = ('created_at',)
    search_fields = ('question', 'answer') # Removed category search for safety
    # REMOVED 'updated_at' from readonly_fields
    readonly_fields = ('created_at', 'likes')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'link', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'content')
    list_editable = ('is_read',)
    readonly_fields = ('created_at',)

@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ('contract_link', 'raised_by', 'status', 'created_at')
    list_filter = ('status','created_at')
    list_editable = ('status',)
    search_fields = ('description', 'raised_by__username', 'contract__rental__title')
    readonly_fields = ('created_at',)
    fields = ('contract', 'raised_by', 'description', 'status', 'resolution_notes')
    def contract_link(self, obj): link = reverse("admin:core_contract_change", args=[obj.contract.id]); return format_html('<a href="{}">Contract #{}</a>', link, obj.contract.id); contract_link.short_description = 'Contract'

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'target_summary', 'description_preview', 'resolved', 'created_at')
    list_filter = ('resolved', 'created_at')
    list_editable = ('resolved',)
    search_fields = ('description', 'reporter__username', 'target_user__username', 'target_rental__title')
    readonly_fields = ('created_at',) # Keep created_at readonly
    def target_summary(self, obj):
        if obj.target_user: return f"User: {obj.target_user}"
        if obj.target_rental: return f"Rental: {obj.target_rental}"
        if obj.target_comment: return f"Comment: {obj.target_comment.id}"
        return "N/A"
    target_summary.short_description = 'Target'
    def description_preview(self, obj): return obj.description[:50] + ('...' if len(obj.description) > 50 else ''); description_preview.short_description = 'Description'

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # REMOVED 'due_date' from list_display
    list_display = ('rental', 'assignee', 'description_preview', 'status', 'created_at') # Added created_at instead
    list_filter = ('status',) # REMOVED due_date filter
    list_editable = ('status',) # REMOVED due_date editable
    search_fields = ('description', 'assignee__username', 'rental__title')
    readonly_fields = ('created_at',)
    fields = ('rental', 'assignee', 'description', 'status', 'due_date', 'created_at') # Keep due_date in detail view

    def description_preview(self, obj): return obj.description[:50] + ('...' if len(obj.description) > 50 else ''); description_preview.short_description = 'Description'

# Register remaining models with default admin
admin.site.register([Availability, BookingQueue, MessageTemplate, FeedbackTrend, SavedSearch, ActionLog])