from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, FormView, CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime, timedelta
from .models import RentalItem, SocialPost, Reservation, UserProfile, Review, UserAction, Message, Badge, UserBadge
from .forms import SignUpForm, ReservationForm, RentalItemForm, SocialPostForm, ReviewForm
from django.contrib.auth.models import User

def award_points(user, points, action):
    profile = user.profile
    profile.points += points
    profile.save()
    badges = Badge.objects.filter(points_required__lte=profile.points).exclude(userbadge__user=user)
    for badge in badges:
        UserBadge.objects.create(user=user, badge=badge)
        messages.success(user.request, _(f"Badge earned: {badge.name}!"))

class HomeView(ListView):
    model = SocialPost
    template_name = 'home.html'
    context_object_name = 'posts'
    ordering = ['-created_at']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = RentalItem.objects.filter(type='item', verified=True).order_by('-rating')[:6]
        context['services'] = RentalItem.objects.filter(type='service', verified=True).order_by('-rating')[:6]
        user_currency = self.request.user.profile.currency if self.request.user.is_authenticated else settings.DEFAULT_CURRENCY
        context['user_currency'] = user_currency
        if self.request.user.is_authenticated:
            actions = UserAction.objects.filter(user=self.request.user).values('details').annotate(count=Count('id'))
            prefs = {a['details'].get('type', 'item'): a['count'] for a in actions if 'type' in a['details']}
            top_type = max(prefs, key=prefs.get, default='item') if prefs else 'item'
            context['recommended'] = RentalItem.objects.filter(type=top_type, verified=True).exclude(owner=self.request.user).order_by('-rating')[:4]
        return context

class SearchView(ListView):
    model = RentalItem
    template_name = 'search.html'
    context_object_name = 'results'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        type_filter = self.request.GET.get('type', '')
        min_price = float(self.request.GET.get('min_price', 0))
        max_price = float(self.request.GET.get('max_price', 10000))
        UserAction.objects.create(user=self.request.user if self.request.user.is_authenticated else None,
                                 action='search', details={'query': query, 'type': type_filter})
        queryset = RentalItem.objects.filter(verified=True)
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
        if type_filter in ['item', 'service']:
            queryset = queryset.filter(type=type_filter)
        queryset = queryset.filter(base_price__gte=min_price, base_price__lte=max_price)
        return queryset.order_by('-rating')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['type_filter'] = self.request.GET.get('type', '')
        context['min_price'] = self.request.GET.get('min_price', '')
        context['max_price'] = self.request.GET.get('max_price', '')
        context['user_currency'] = self.request.user.profile.currency if self.request.user.is_authenticated else settings.DEFAULT_CURRENCY
        return context

class ListingView(DetailView):
    model = RentalItem
    template_name = 'listing.html'
    context_object_name = 'item'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.views += 1
        self.object.save()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_currency = self.request.user.profile.currency if self.request.user.is_authenticated else settings.DEFAULT_CURRENCY
        context['converted_price'] = float(self.object.base_price) * settings.EXCHANGE_RATES[self.object.base_currency][user_currency]
        context['user_currency'] = user_currency
        context['related'] = RentalItem.objects.filter(type=self.object.type, verified=True).exclude(id=self.object.id).order_by('-rating')[:4]
        context['reviews'] = Review.objects.filter(item=self.object).order_by('-created_at')[:5]
        if self.request.user.is_authenticated:
            context['can_review'] = not Review.objects.filter(reviewer=self.request.user, item=self.object).exists()
            context['review_form'] = ReviewForm()
            context['chat_available'] = self.object.owner != self.request.user
        return context

class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['listings'] = self.request.user.rentalitem_set.all().order_by('-created_at')
        context['reservations'] = self.request.user.reservation_set.all().order_by('-created_at')
        context['posts'] = self.request.user.socialpost_set.all().order_by('-created_at')[:5]
        context['reviews'] = Review.objects.filter(profile=self.request.user.profile).order_by('-created_at')[:5]
        context['badges'] = UserBadge.objects.filter(user=self.request.user).select_related('badge')
        return context

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserAction.objects.create(user=user, action='signup')
            award_points(user, 10, 'signup')
            messages.success(request, _("Account created successfully! Please log in."))
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

class BookingView(LoginRequiredMixin, FormView):
    template_name = 'booking.html'
    form_class = ReservationForm
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(RentalItem, id=self.kwargs['item_id'], verified=True)
        context['item'] = item
        user_currency = self.request.user.profile.currency
        base_price = float(item.base_price)
        if item.pricing_rules:
            today = datetime.now().date()
            start_date_str = self.request.POST.get('start_date', today.isoformat() + 'T00:00')
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M').date()
            if start_date.weekday() >= 5 and 'weekend' in item.pricing_rules:
                base_price *= item.pricing_rules['weekend']
        context['converted_price'] = base_price * settings.EXCHANGE_RATES[item.base_currency][user_currency]
        context['user_currency'] = user_currency
        return context

    def form_valid(self, form):
        item = get_object_or_404(RentalItem, id=self.kwargs['item_id'], verified=True)
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        for date in item.availability:
            d = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=start_date.tzinfo)
            if start_date <= d <= end_date and item.availability[date] == 'booked':
                messages.error(self.request, _("This item is not available for the selected dates."))
                return self.form_invalid(form)
        reservation = form.save(commit=False)
        reservation.renter = self.request.user
        reservation.item = item
        duration = (end_date - start_date).total_seconds() / 86400
        base_price = float(item.base_price)
        if item.pricing_rules and start_date.weekday() >= 5 and 'weekend' in item.pricing_rules:
            base_price *= item.pricing_rules['weekend']
        reservation.total_cost = base_price * max(1, duration)
        reservation.save()
        current = start_date
        while current <= end_date:
            item.availability[current.strftime('%Y-%m-%d')] = 'booked'
            current += timedelta(days=1)
        item.save()
        UserAction.objects.create(user=self.request.user, action='booking', details={'item': item.title})
        award_points(self.request.user, 20, 'booking')
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{item.owner.id}',
            {'type': 'send_notification', 'message': f'{self.request.user.username} booked {item.title}'}
        )
        messages.success(self.request, _("Booking successful! Please upload payment proof."))
        return redirect('payment', reservation_id=reservation.id)

@login_required
def payment(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, renter=request.user)
    if reservation.status != 'pending':
        messages.error(request, _("This reservation cannot be modified."))
        return redirect('profile')
    if request.method == 'POST' and 'payment_proof' in request.FILES:
        try:
            reservation.payment_proof = request.FILES['payment_proof']
            reservation.status = 'confirmed'
            reservation.save()
            UserAction.objects.create(user=request.user, action='payment', details={'reservation': reservation.id})
            award_points(request.user, 15, 'payment')
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{reservation.item.owner.id}',
                {'type': 'send_notification', 'message': f'Payment confirmed for {reservation.item.title}'}
            )
            messages.success(request, _("Payment proof uploaded successfully!"))
            return redirect('profile')
        except Exception as e:
            messages.error(request, f"Error uploading payment proof: {str(e)}")
    user_currency = request.user.profile.currency
    converted_cost = float(reservation.total_cost) * settings.EXCHANGE_RATES[reservation.item.base_currency][user_currency]
    return render(request, 'booking.html', {
        'reservation': reservation,
        'converted_cost': converted_cost,
        'user_currency': user_currency
    })

@login_required
def notifications(request):
    return render(request, 'notifications.html')

@login_required
def like_post(request, post_id):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")
    post = get_object_or_404(SocialPost, id=post_id)
    liked = request.user in post.likes.all()
    if liked:
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
        award_points(request.user, 5, 'like')
    return JsonResponse({'likes': post.likes.count(), 'liked': not liked})

@login_required
def add_comment(request, post_id):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")
    post = get_object_or_404(SocialPost, id=post_id)
    comment_text = request.POST.get('comment', '').strip()
    if not comment_text:
        return JsonResponse({'error': 'Comment cannot be empty'}, status=400)
    comment = {'user': request.user.username, 'text': comment_text, 'date': datetime.now().isoformat()}
    post.comments.append(comment)
    post.save()
    award_points(request.user, 10, 'comment')
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{post.user.id}',
        {'type': 'send_notification', 'message': f'{request.user.username} commented on your post'}
    )
    return JsonResponse({'comment': comment})

class AddListingView(LoginRequiredMixin, CreateView):
    model = RentalItem
    form_class = RentalItemForm
    template_name = 'add_listing.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        UserAction.objects.create(user=self.request.user, action='add_listing', details={'title': form.instance.title})
        award_points(self.request.user, 25, 'add_listing')
        messages.success(self.request, _("Listing added successfully! It will be visible once verified."))
        return response

class AddPostView(LoginRequiredMixin, CreateView):
    model = SocialPost
    form_class = SocialPostForm
    template_name = 'add_post.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        UserAction.objects.create(user=self.request.user, action='add_post', details={'caption': form.instance.caption[:50]})
        award_points(self.request.user, 15, 'add_post')
        messages.success(self.request, _("Post shared successfully!"))
        return response

@login_required
def add_review(request, item_id):
    item = get_object_or_404(RentalItem, id=item_id, verified=True)
    if Review.objects.filter(reviewer=request.user, item=item).exists():
        messages.error(request, _("You have already reviewed this item."))
        return redirect('listing', pk=item_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.item = item
            review.save()
            UserAction.objects.create(user=request.user, action='review', details={'item': item.title, 'rating': review.rating})
            award_points(request.user, 20, 'review')
            messages.success(request, _("Review submitted successfully!"))
            return redirect('listing', pk=item_id)
    return redirect('listing', pk=item_id)

@login_required
def chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    messages_list = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(sender=request.user, receiver=other_user, content=content)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{other_user.id}',
                {'type': 'chat_message', 'message': {'sender': request.user.username, 'content': content, 'timestamp': datetime.now().isoformat()}}
            )
            return redirect('chat', user_id=user_id)
    Message.objects.filter(receiver=request.user, sender=other_user, read=False).update(read=True)
    return render(request, 'chat.html', {'other_user': other_user, 'messages': messages_list})

class DashboardView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'dashboard.html'
    context_object_name = 'user'

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        listings = self.request.user.rentalitem_set.all()
        context['total_views'] = sum(l.views for l in listings)
        context['total_bookings'] = Reservation.objects.filter(item__owner=self.request.user).count()
        context['average_rating'] = sum(l.rating for l in listings if l.review_count) / max(1, listings.filter(review_count__gt=0).count())
        context['recent_actions'] = UserAction.objects.filter(user=self.request.user).order_by('-timestamp')[:10]
        return context