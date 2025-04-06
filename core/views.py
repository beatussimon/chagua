from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse, FileResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Avg
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from .models import *
from .forms import *
import os
from django.conf import settings
import json



def dashboard(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    city = request.GET.get('city', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    rentals = Rental.objects.all()
    packages = ServicePackage.objects.all()

    if query:
        rentals = rentals.filter(Q(title__icontains=query) | Q(description__icontains=query))
        packages = packages.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category:
        rentals = rentals.filter(category__slug=category)
        packages = packages.filter(category__slug=category)
    if price_min:
        rentals = rentals.filter(price__gte=price_min)
        packages = packages.filter(price__gte=price_min)
    if price_max:
        rentals = rentals.filter(price__lte=price_max)
        packages = packages.filter(price__lte=price_max)
    if city:
        rentals = rentals.filter(city__icontains=city)
    if start_date and end_date:
        rentals = rentals.filter(availabilities__start_date__lte=end_date, availabilities__end_date__gte=start_date, availabilities__is_available=True)

    if request.user.is_authenticated:
        rentals = sorted(rentals, key=lambda r: r.get_recommendation_score(request.user), reverse=True)
    else:
        rentals = rentals.order_by('-created_at')

    paginator = Paginator(rentals, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    notifications = Notification.objects.filter(user=request.user, is_read=False) if request.user.is_authenticated else []
    categories = Category.objects.all()
    saved_searches = SavedSearch.objects.filter(user=request.user) if request.user.is_authenticated else []

    if request.method == 'POST' and request.user.is_authenticated:
        form = SavedSearchForm(request.POST)
        if form.is_valid():
            filters = {'q': query, 'category': category, 'price_min': price_min, 'price_max': price_max, 'city': city, 'start_date': start_date, 'end_date': end_date}
            form.instance.filters = {k: v for k, v in filters.items() if v}
            form.instance.user = request.user
            form.save()
            messages.success(request, _("Search saved!"))

    return render(request, 'core/dashboard.html', {
        'page_obj': page_obj, 'packages': packages, 'notifications': notifications, 'categories': categories,
        'saved_searches': saved_searches, 'query': query, 'category': category, 'price_min': price_min,
        'price_max': price_max, 'city': city, 'start_date': start_date, 'end_date': end_date
    })

def rental_detail(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    rental.views += 1
    rental.save()
    comments = rental.comments.filter(parent__isnull=True)
    comment_form = CommentForm()
    review_form = ReviewForm()
    availability_form = AvailabilityForm()
    dispute_form = DisputeForm()
    task_form = TaskForm()
    contract_form = ContractForm(initial={'terms': rental.description, 'start_date': timezone.now().date(), 'end_date': timezone.now().date() + timezone.timedelta(days=7)})

    if request.method == 'POST' and request.user.is_authenticated:
        if 'contract' in request.POST:
            if request.user == rental.owner:
                messages.error(request, _("You cannot contract your own rental."))
            else:
                contract_form = ContractForm(request.POST)
                if contract_form.is_valid():
                    contract = contract_form.save(commit=False)
                    contract.rental = rental
                    contract.tenant = request.user
                    contract.save()
                    return redirect('download_contract', contract_id=contract.id)
        elif 'payment' in request.POST:
            payment = Payment.objects.create(payer=request.user, rental=rental, amount=rental.price)
            messages.success(request, _("Payment submitted! Follow offline instructions."))
        elif 'review' in request.POST:
            review_form = ReviewForm(request.POST, request.FILES)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.reviewer = request.user
                review.rental = rental
                review.save()
                for file in request.FILES.getlist('media_files'):
                    media = Media.objects.create(file=file, uploaded_by=request.user)
                    review.media.add(media)
                messages.success(request, _("Review posted!"))
        elif 'comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.rental = rental
                comment.user = request.user
                parent_id = request.POST.get('parent_id')
                if parent_id:
                    comment.parent = get_object_or_404(Comment, id=parent_id)
                comment.save()
                messages.success(request, _("Comment added!"))
        elif 'availability' in request.POST:
            availability_form = AvailabilityForm(request.POST)
            if availability_form.is_valid():
                availability = availability_form.save(commit=False)
                availability.rental = rental
                availability.save()
                messages.success(request, _("Availability added!"))
        elif 'dispute' in request.POST:
            dispute_form = DisputeForm(request.POST)
            if dispute_form.is_valid():
                contract = Contract.objects.filter(rental=rental, tenant=request.user).first()
                if contract:
                    dispute = dispute_form.save(commit=False)
                    dispute.contract = contract
                    dispute.raised_by = request.user
                    dispute.save()
                    messages.success(request, _("Dispute raised!"))
        elif 'task' in request.POST:
            task_form = TaskForm(request.POST)
            if task_form.is_valid():
                task = task_form.save(commit=False)
                task.rental = rental
                task.save()
                messages.success(request, _("Task assigned!"))
        elif 'queue' in request.POST:
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            BookingQueue.objects.create(user=request.user, rental=rental, start_date=start_date, end_date=end_date)
            messages.success(request, _("Added to booking queue!"))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'comments': [c.content for c in comments], 'availabilities': [{'start': a.start_date.isoformat(), 'end': a.end_date.isoformat()} for a in rental.availabilities.all()]})
    return render(request, 'core/rental_detail.html', {
        'rental': rental, 'comments': comments, 'comment_form': comment_form, 'review_form': review_form,
        'availability_form': availability_form, 'dispute_form': dispute_form, 'task_form': task_form,
        'contract_form': contract_form, 'templates': ContractTemplate.objects.all()
    })

@login_required
def download_contract(request, contract_id):
    contract = get_object_or_404(Contract, id=contract_id)
    if request.user not in [contract.tenant, contract.rental.owner]:
        return HttpResponseForbidden()
    file_path = os.path.join(settings.MEDIA_ROOT, f'contracts/contract_{contract.id}.txt')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(f"Contract for {contract.rental.title}\nTenant: {contract.tenant.username}\nOwner: {contract.rental.owner.username}\nTerms: {contract.terms}\nCustom Terms: {contract.custom_terms}\nEmergency Clause: {contract.emergency_clause}")
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=f"contract_{contract.id}.txt")

@login_required
def rental_edit(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    if request.user != rental.owner and rental.team not in request.user.teams.all():
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = RentalForm(request.POST, request.FILES, instance=rental)
        if form.is_valid():
            rental = form.save()
            for file in request.FILES.getlist('media_files'):
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, _("File too large."))
                    continue
                media = Media.objects.create(file=file, uploaded_by=request.user)
                rental.media.add(media)
            messages.success(request, _("Rental updated!"))
            return redirect('rental_detail', rental_id=rental.id)
    else:
        form = RentalForm(instance=rental)
    return render(request, 'core/rental_edit.html', {'form': form, 'rental': rental})

@login_required
def rental_delete(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    if request.user != rental.owner and rental.team not in request.user.teams.all():
        return HttpResponseForbidden()
    if request.method == 'POST':
        rental.delete()
        messages.success(request, _("Rental deleted!"))
        return redirect('dashboard')
    return render(request, 'core/rental_delete.html', {'rental': rental})

@login_required
def rental_create(request):
    if request.method == 'POST':
        form = RentalForm(request.POST, request.FILES)
        if form.is_valid():
            rental = form.save(commit=False)
            rental.owner = request.user
            rental.save()
            for file in request.FILES.getlist('media_files'):
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, _("File too large."))
                    continue
                media = Media.objects.create(file=file, uploaded_by=request.user)
                rental.media.add(media)
            messages.success(request, _("Rental created!"))
            return redirect('dashboard')
    else:
        form = RentalForm()
    return render(request, 'core/rental_create.html', {'form': form})

@login_required
def service_package_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')
        rental_ids = request.POST.getlist('rentals')
        category_id = request.POST.get('category')
        package = ServicePackage.objects.create(
            owner=request.user, title=title, description=description, price=price,
            category_id=category_id if category_id else None
        )
        package.rentals.set(Rental.objects.filter(id__in=rental_ids, owner=request.user))
        messages.success(request, _("Service package created!"))
        return redirect('dashboard')
    rentals = Rental.objects.filter(owner=request.user)
    categories = Category.objects.all()
    return render(request, 'core/service_package_create.html', {'rentals': rentals, 'categories': categories})

@login_required
def like_rental(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    if request.method == 'POST':
        if request.user in rental.likes.all():
            rental.likes.remove(request.user)
        else:
            rental.likes.add(request.user)
            Notification.objects.create(user=rental.owner, content=f"{request.user.username} liked {rental.title}", link=reverse('rental_detail', args=[rental.id]))
    return redirect('rental_detail', rental_id=rental_id)

@login_required
def add_comment(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.rental = rental
            comment.user = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = get_object_or_404(Comment, id=parent_id)
            comment.save()
            Notification.objects.create(user=rental.owner, content=f"{request.user.username} commented on {rental.title}", link=reverse('rental_detail', args=[rental.id]))
            messages.success(request, _("Comment added!"))
    return redirect('rental_detail', rental_id=rental_id)

@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
        else:
            comment.likes.add(request.user)
            Notification.objects.create(user=comment.user, content=f"{request.user.username} liked your comment", link=reverse('rental_detail', args=[comment.rental.id]))
    return redirect('rental_detail', rental_id=comment.rental.id)

@login_required
def messaging(request, group_id=None):
    messages_received = Message.objects.filter(recipient=request.user).order_by('-timestamp')
    messages_sent = Message.objects.filter(sender=request.user).order_by('-timestamp')
    group = get_object_or_404(MessageGroup, id=group_id) if group_id else None
    if group:
        messages_received = messages_received.filter(group=group)
        messages_sent = messages_sent.filter(group=group)
    users = User.objects.exclude(id=request.user.id)
    groups = request.user.message_groups.all()
    templates = MessageTemplate.objects.filter(user=request.user)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            recipient_id = request.POST.get('recipient_id')
            group_id = request.POST.get('group_id')
            schedule = request.POST.get('schedule')
            if recipient_id:
                recipient = get_object_or_404(User, id=recipient_id)
                message = form.save(commit=False)
                message.sender = request.user
                message.recipient = recipient
                message.save()
                if schedule:
                    ScheduledMessage.objects.create(message=message, send_at=schedule)
                else:
                    Notification.objects.create(user=recipient, content=f"New message from {request.user.username}", link=reverse('messaging'))
                messages.success(request, _("Message sent!"))
            elif group_id:
                group = get_object_or_404(MessageGroup, id=group_id)
                message = form.save(commit=False)
                message.sender = request.user
                message.group = group
                message.save()
                if schedule:
                    ScheduledMessage.objects.create(message=message, send_at=schedule)
                else:
                    for participant in group.participants.exclude(id=request.user.id):
                        Notification.objects.create(user=participant, content=f"New message in {group.name}", link=reverse('messaging_group', args=[group.id]))
                messages.success(request, _("Message sent to group!"))
            elif 'template' in request.POST:
                MessageTemplate.objects.create(user=request.user, content=form.cleaned_data['content'])
                messages.success(request, _("Template saved!"))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        messages_list = messages_received | messages_sent
        return JsonResponse({'messages': [{'content': m.content, 'sender': m.sender.username, 'timestamp': m.timestamp.isoformat()} for m in messages_list.order_by('timestamp')]})
    return render(request, 'core/messaging.html', {
        'sent': messages_sent, 'received': messages_received, 'users': users, 'form': MessageForm(),
        'groups': groups, 'current_group': group, 'templates': templates
    })

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        participant_ids = request.POST.getlist('participants')
        group = MessageGroup.objects.create(name=name)
        group.participants.add(request.user, *User.objects.filter(id__in=participant_ids))
        messages.success(request, _("Group created!"))
        return redirect('messaging_group', group_id=group.id)
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'core/create_group.html', {'users': users})

@login_required
def team_manage(request, team_id):
    team = get_object_or_404(Team, id=team_id, owner=request.user)
    if request.method == 'POST':
        if 'add_member' in request.POST:
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            team.members.add(user)
            messages.success(request, _("Member added!"))
        elif 'remove_member' in request.POST:
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            team.members.remove(user)
            messages.success(request, _("Member removed!"))
    users = User.objects.exclude(id=request.user.id).exclude(teams=team)
    return render(request, 'core/team_manage.html', {'team': team, 'users': users})

@login_required
def team_history(request, team_id):
    team = get_object_or_404(Team, id=team_id, owner=request.user)
    logs = ActionLog.objects.filter(user__in=team.members.all()) | ActionLog.objects.filter(user=team.owner)
    return render(request, 'core/team_history.html', {'team': team, 'logs': logs})

def feedback(request):
    reviews = Review.objects.all().order_by('-likes', '-created_at')
    faqs = FAQ.objects.all().order_by('-likes')
    faq_form = FAQForm()
    if request.method == 'POST' and request.user.is_authenticated:
        if 'faq' in request.POST:
            faq_form = FAQForm(request.POST)
            if faq_form.is_valid():
                faq = faq_form.save(commit=False)
                faq.created_by = request.user
                faq.save()
                messages.success(request, _("FAQ added!"))
        elif 'like_review' in request.POST:
            review = get_object_or_404(Review, id=request.POST.get('review_id'))
            review.likes += 1
            review.save()
        elif 'like_faq' in request.POST:
            faq = get_object_or_404(FAQ, id=request.POST.get('faq_id'))
            faq.likes += 1
            faq.save()
        elif 'dispute_review' in request.POST:
            review = get_object_or_404(Review, id=request.POST.get('review_id'))
            FeedbackDispute.objects.create(review=review, user=request.user, reason=request.POST.get('reason'))
            messages.success(request, _("Review disputed!"))
    return render(request, 'core/feedback.html', {'reviews': reviews, 'faqs': faqs, 'faq_form': faq_form})

def profile(request, username):
    user = get_object_or_404(User, username=username)
    rentals = user.rentals.all()
    packages = user.service_packages.all()
    teams = user.owned_teams.all()
    earnings = Payment.objects.filter(rental__owner=user, status='approved').aggregate(Sum('amount'))['amount__sum'] or 0
    analytics = {
        'views': rentals.aggregate(Sum('views'))['views__sum'] or 0,
        'avg_rating': Review.objects.filter(rental__owner=user).aggregate(Avg('rating'))['rating__avg'] or 0
    }

    if request.method == 'POST' and request.user == user:
        if 'verification_document' in request.FILES:
            user.verification_document = request.FILES['verification_document']
            user.save()
            messages.success(request, _("Verification document uploaded!"))
        elif 'follow' in request.POST:
            if request.user in user.followers.all():
                user.followers.remove(request.user)
            else:
                user.followers.add(request.user)
        elif 'theme' in request.POST:
            user.theme_preference = request.POST['theme']
            user.save()
        elif 'boost' in request.POST:
            rental = get_object_or_404(Rental, id=request.POST.get('rental_id'), owner=user)
            if user.is_premium:
                rental.boosted = True
                rental.save()
                messages.success(request, _("Rental boosted!"))
            else:
                messages.error(request, _("Premium subscription required to boost posts."))
        elif 'feature' in request.POST:
            rental = get_object_or_404(Rental, id=request.POST.get('rental_id'), owner=user)
            if user.is_premium:
                Payment.objects.create(payer=user, rental=rental, amount=10, instructions="Pay $10 to feature this rental.")
                rental.is_featured = True
                rental.save()
                messages.success(request, _("Rental featured! Follow payment instructions."))
            else:
                messages.error(request, _("Premium subscription required to feature posts."))
        elif 'create_team' in request.POST:
            Team.objects.create(name=request.POST.get('team_name'), owner=user)
            messages.success(request, _("Team created!"))

    user.check_trust_badge()
    subscription = UserSubscription.objects.filter(user=user, end_date__gt=timezone.now()).first()
    return render(request, 'core/profile.html', {
        'profile_user': user, 'rentals': rentals, 'packages': packages, 'earnings': earnings, 'analytics': analytics,
        'teams': teams, 'subscription': subscription
    })

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, _("Invalid credentials"))
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.user_type = request.POST.get('user_type', 'individual')
            user.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def subscribe(request):
    plans = SubscriptionPlan.objects.all()
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)
        end_date = timezone.now() + timezone.timedelta(days=30)
        UserSubscription.objects.create(user=request.user, plan=plan, end_date=end_date)
        Payment.objects.create(payer=request.user, amount=plan.price, instructions=f"Pay ${plan.price} for {plan.name}")
        messages.success(request, _("Subscription activated! Follow payment instructions."))
        return redirect('profile', username=request.user.username)
    return render(request, 'core/subscribe.html', {'plans': plans})

@login_required
def admin_dashboard(request):
    if not (request.user.is_superuser or request.user.is_custom_admin):
        return HttpResponseForbidden()
    perms = request.user.admin_permissions if request.user.is_custom_admin else {'all': True}
    context = {}
    if perms.get('all', False) or perms.get('users', False):
        context['users'] = User.objects.all()
    if perms.get('all', False) or perms.get('rentals', False):
        context['rentals'] = Rental.objects.all()
    if perms.get('all', False) or perms.get('payments', False):
        context['payments'] = Payment.objects.all()
    if perms.get('all', False) or perms.get('disputes', False):
        context['disputes'] = Dispute.objects.all()
    if perms.get('all', False) or perms.get('contracts', False):
        context['contracts'] = Contract.objects.all()
    if perms.get('all', False) or perms.get('reports', False):
        context['reports'] = Report.objects.all()
    if request.method == 'POST':
        if 'permissions' in request.POST and request.user.is_superuser:
            user_id = request.POST.get('user_id')
            permissions = json.loads(request.POST.get('permissions', '{}'))
            user = get_object_or_404(User, id=user_id)
            user.is_custom_admin = True
            user.admin_permissions = permissions
            user.save()
            messages.success(request, f"Updated admin permissions for {user.username}")
        elif 'verify_payment' in request.POST and (perms.get('all', False) or perms.get('payments', False)):
            payment_id = request.POST.get('payment_id')
            payment = get_object_or_404(Payment, id=payment_id)
            payment.status = 'approved'
            payment.save()
            messages.success(request, f"Payment {payment.Transaction_id} approved")
        elif 'verify_user' in request.POST and (perms.get('all', False) or perms.get('users', False)):
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            user.is_verified = True
            user.save()
            messages.success(request, f"User {user.username} verified")
        elif 'verify_rental' in request.POST and (perms.get('all', False) or perms.get('rentals', False)):
            rental_id = request.POST.get('rental_id')
            rental = get_object_or_404(Rental, id=rental_id)
            rental.is_verified = True
            rental.save()
            messages.success(request, f"Rental {rental.title} verified")
        elif 'resolve_dispute' in request.POST and (perms.get('all', False) or perms.get('disputes', False)):
            dispute_id = request.POST.get('dispute_id')
            dispute = get_object_or_404(Dispute, id=dispute_id)
            dispute.status = 'resolved'
            dispute.save()
            messages.success(request, f"Dispute resolved")
        elif 'resolve_report' in request.POST and (perms.get('all', False) or perms.get('reports', False)):
            report_id = request.POST.get('report_id')
            report = get_object_or_404(Report, id=report_id)
            report.resolved = True
            report.save()
            messages.success(request, f"Report resolved")
    return render(request, 'core/admin_dashboard.html', context)

def custom_404(request, exception):
    return render(request, 'core/404.html', status=404)