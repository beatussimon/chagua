from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from .forms import VerificationForm, ProfilePictureForm
from django.utils import timezone


@login_required
def dashboard(request):
    user = request.user
    user.last_activity = timezone.now()
    user.award_trust_badge()
    user.award_boosted_posts()
    user.save()
    context = {
        'user': user,
        'rentals': user.rentals.all()[:5],
        'reviews': user.reviews_received.all()[:5],
        'conversations': user.conversations.all()[:5],
        'stats': user.get_activity_stats(),
    }
    return render(request, 'dashboard.html', context)

@login_required
def verify_user(request):
    if request.user.is_verified:
        messages.info(request, "You are already verified.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = VerificationForm(request.POST, request.FILES)
        if form.is_valid():
            request.user.verification_documents = form.cleaned_data['documents']
            request.user.save()
            messages.success(request, "Verification documents submitted. Awaiting approval.")
            return redirect('dashboard')
    else:
        form = VerificationForm()
    return render(request, 'verify.html', {'form': form})

@login_required
def update_profile_picture(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES)
        if form.is_valid():
            if request.user.profile_picture:
                request.user.profile_picture.delete()  # Remove old picture
            request.user.profile_picture = form.cleaned_data['profile_picture']
            request.user.save()
            messages.success(request, "Profile picture updated successfully.")
            return redirect('dashboard')
    else:
        form = ProfilePictureForm()
    return render(request, 'update_profile_picture.html', {'form': form})

@login_required
def report_abuse(request, user_id):
    reported_user = get_object_or_404(User, id=user_id)
    if request.user == reported_user:
        messages.error(request, "You cannot report yourself.")
        return redirect('dashboard')
    if request.method == 'POST':
        reported_user.flagged = True
        reported_user.save()
        messages.success(request, "User reported successfully.")
        return redirect('dashboard')
    return render(request, 'report_abuse.html', {'reported_user': reported_user})