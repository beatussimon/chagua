from django.db import models
from django.core.exceptions import PermissionDenied

class Conversation(models.Model):
    participants = models.ManyToManyField('users.User', related_name='conversations')
    is_group = models.BooleanField(default=False)
    name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def add_participant(self, user):
        if self.participants.count() >= 50 and self.is_group:
            raise PermissionDenied("Group chat limit reached (50 participants).")
        self.participants.add(user)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='messages_sent')
    content = models.TextField(max_length=5000)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()