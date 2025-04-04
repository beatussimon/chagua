from django import forms
from .models import Rental, Media

class RentalForm(forms.ModelForm):
    media_files = forms.FileField(widget=forms.FileInput(), required=False)

    class Meta:
        model = Rental
        fields = ['title', 'description', 'price']

    def save(self, commit=True):
        rental = super().save(commit=commit)
        if 'media_files' in self.files:
            for file in self.files.getlist('media_files'):
                media = Media.objects.create(file=file, uploaded_by=rental.owner)
                rental.media.add(media)
        return rental