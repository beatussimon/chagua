from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Review, FAQ  # Import your Media model
from rentals.models import Media 
from .forms import ReviewForm, FAQForm

@login_required
def feedback(request):
    reviews = Review.objects.all().order_by('-likes', '-created_at')
    faqs = FAQ.objects.all().order_by('-helpful_votes')
    context = {'reviews': reviews, 'faqs': faqs}
    return render(request, 'feedback.html', context)

@login_required
def create_review(request, user_id):
    reviewed = get_object_or_404('users.User', id=user_id)
    if request.user == reviewed:
        return render(request, 'error.html', {'message': "You cannot review yourself."})
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.reviewed = reviewed
            review.save()

            for file in form.cleaned_data.get('media_files', []):
                media = Media.objects.create(file=file, uploaded_by=request.user)
                review.media.add(media)

            return redirect('feedback')
        else:
            return render(request, 'create_review.html', {'form': form, 'reviewed': reviewed})
    else:
        form = ReviewForm()
    return render(request, 'create_review.html', {'form': form, 'reviewed': reviewed})

@login_required
def create_faq(request):
    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            faq = form.save(commit=False)
            faq.user_contribution = request.user
            faq.save()
            return redirect('feedback')
        else:
            return render(request, 'create_faq.html', {'form': form})
    else:
        form = FAQForm()
    return render(request, 'create_faq.html', {'form': form})