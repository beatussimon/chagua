from django import forms
from django.forms.widgets import FileInput
from .models import Rental, Review, FAQ, Comment, User, Availability, Message, Dispute, SavedSearch, Task, Contract

# Custom widget to handle multiple file uploads
class MultiFileInput(FileInput):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is None:
            attrs = {}
        attrs.update({'multiple': 'multiple'})
        self.attrs = attrs

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        return [files.get(name)]

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ['title', 'description', 'price', 'category', 'city', 'country', 'latitude', 'longitude']

class ReviewForm(forms.ModelForm):
    media_files = forms.FileField(widget=MultiFileInput(), required=False)  # Use custom MultiFileInput
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