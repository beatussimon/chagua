from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MaxValueValidator
from .models import User, UserProfile, Reservation, RentalItem, SocialPost, Review
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class SignUpForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, help_text=_("Enter a valid phone number"))
    currency = forms.ChoiceField(choices=[('KES', 'KES'), ('USD', 'USD'), ('GBP', 'GBP'), ('EUR', 'EUR')], label=_("Preferred Currency"))
    agree_to_terms = forms.BooleanField(required=True, label=_("I agree to Chagua's Terms and Conditions"))
    captcha = forms.CharField(label=_("Enter 'CHAGUA'"), help_text=_("Type the word 'CHAGUA' to verify"))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone_number', 'currency')

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if UserProfile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(_("This phone number is already registered."))
        return phone

    def clean_captcha(self):
        captcha = self.cleaned_data['captcha'].strip().upper()
        if captcha != 'CHAGUA':
            raise forms.ValidationError(_("Incorrect CAPTCHA. Please enter 'CHAGUA'."))
        return captcha

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                currency=self.cleaned_data['currency']
            )
        return user

class ReservationForm(forms.ModelForm):
    contract_agreed = forms.BooleanField(required=True, label=_("I agree to the rental/service contract"))

    class Meta:
        model = Reservation
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError(_("End date must be after start date."))
            if start_date < timezone.now():
                raise forms.ValidationError(_("Start date cannot be in the past."))
        return cleaned_data

class RentalItemForm(forms.ModelForm):
    class Meta:
        model = RentalItem
        fields = ['type', 'title', 'description', 'base_price', 'base_currency', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'type': forms.Select(attrs={'class': 'form-input'}),
            'base_currency': forms.Select(attrs={'class': 'form-input'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'form-input'}),
        }

class SocialPostForm(forms.ModelForm):
    class Meta:
        model = SocialPost
        fields = ['caption', 'media']
        widgets = {
            'caption': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': _('What’s on your mind?')}),
            'media': forms.FileInput(attrs={'class': 'form-input'}),
        }

class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(min_value=1, max_value=5, widget=forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 5}))

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': _('Leave your feedback...')}),
        }