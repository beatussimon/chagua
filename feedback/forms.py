from django import forms
from .models import Review, FAQ
from rentals.models import Media  # Import Media model for file association

# Custom widget and field for multiple file uploads
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data and self.required:
            raise forms.ValidationError("This field is required.")
        elif not data and not self.required:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super(MultipleFileField, self).clean(d, initial) for d in data]

class ReviewForm(forms.ModelForm):
    media_files = MultipleFileField(label="Upload Media", required=False)

    class Meta:
        model = Review
        fields = ['rating', 'comment', 'is_anonymous']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].widget = forms.RadioSelect(choices=[(i, i) for i in range(1, 6)])

    def save(self, commit=True):
        review = super().save(commit=commit)
        if 'media_files' in self.files:
            for file in self.files.getlist('media_files'):
                media = Media.objects.create(file=file, uploaded_by=self.instance.reviewer)
                review.media.add(media)
        return review

class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
            'answer': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }