from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Conversation, Message
from .forms import NewConversationForm, MessageForm
from django.contrib.auth.models import User

@login_required
def messaging(request, conversation_id=None):
    conversations = request.user.conversations.all()
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if request.user not in conversation.participants.all():
            return render(request, 'error.html', {'message': 'Access denied'})
        messages_list = conversation.messages.all().order_by('timestamp')
        for msg in messages_list.filter(is_read=False).exclude(sender=request.user):
            msg.mark_as_read()
        if request.method == 'POST':
            form = MessageForm(request.POST)
            if form.is_valid():
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=form.cleaned_data['content']
                )
                return redirect('messaging', conversation_id=conversation.id)
        else:
            form = MessageForm()
    else:
        conversation = None
        messages_list = []
        form = None
    context = {
        'conversations': conversations,
        'conversation': conversation,
        'messages': messages_list,
        'form': form,
        'filters': ['all', 'unread', 'flagged'],
    }
    return render(request, 'messaging.html', context)

@login_required
def new_conversation(request):
    if request.method == 'POST':
        form = NewConversationForm(request.POST)
        if form.is_valid():
            participants = form.cleaned_data['participants'].split(',')
            conversation = Conversation.objects.create(is_group=len(participants) > 1)
            conversation.participants.add(request.user)
            for username in participants:
                try:
                    user = User.objects.get(username=username.strip())
                    conversation.add_participant(user)
                except User.DoesNotExist:
                    messages.error(request, f"User {username} not found.")
            return redirect('messaging', conversation_id=conversation.id)
    else:
        form = NewConversationForm()
    return render(request, 'new_conversation.html', {'form': form})