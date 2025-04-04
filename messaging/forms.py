from django import forms

class NewConversationForm(forms.Form):
    participants = forms.CharField(label="Participants (comma-separated usernames)", required=True)

class MessageForm(forms.Form):
    content = forms.CharField(label="Message", widget=forms.Textarea, max_length=5000, required=True)