from django import forms
from .models import Rental, Review, FAQ, Comment, User, Availability, Message, Dispute, SavedSearch, Task, Contract

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ['title', 'description', 'price', 'category', 'city', 'country', 'latitude', 'longitude']

class ReviewForm(forms.ModelForm):
    media_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'is_anonymous']

class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['start_date', 'end_date', 'is_recurring', 'recurrence_rule']
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'}), 'end_date': forms.DateInput(attrs={'type': 'date'})}

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'attachment']

class DisputeForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ['description']

class SavedSearchForm(forms.ModelForm):
    class Meta:
        model = SavedSearch
        fields = ['name', 'filters']

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['description', 'assignee', 'status']

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['terms', 'start_date', 'end_date', 'emergency_clause']
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'}), 'end_date': forms.DateInput(attrs={'type': 'date'})}