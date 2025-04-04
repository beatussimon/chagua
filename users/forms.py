from django import forms
from .models import User

class VerificationForm(forms.Form):
    documents = forms.FileField(label="Upload Verification Documents", required=True)

    def clean_documents(self):
        doc = self.cleaned_data['documents']
        if doc.size > 10 * 1024 * 1024:
            raise forms.ValidationError("File must not exceed 10MB.")
        return doc

class ProfilePictureForm(forms.Form):
    profile_picture = forms.ImageField(label="Upload Profile Picture", required=True)

    def clean_profile_picture(self):
        pic = self.cleaned_data['profile_picture']
        if pic.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Image must not exceed 5MB.")
        return pic