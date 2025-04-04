from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Contract
from .forms import ContractForm
from messaging.models import Conversation, Message
from django.utils import timezone
from django.contrib import messages

@login_required
def create_contract(request, rental_id):
    rental = get_object_or_404('rentals.Rental', id=rental_id)
    if rental.owner == request.user:
        return render(request, 'error.html', {'message': "You cannot rent your own listing."})
    if Contract.objects.filter(rental=rental, renter=request.user, status='pending').exists():
        return render(request, 'error.html', {'message': "You already have a pending contract for this rental."})
    if request.method == 'POST':
        form = ContractForm(request.POST)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.rental = rental
            contract.renter = request.user
            contract.save()
            contract.generate_contract_file()
            return redirect('view_contract', contract_id=contract.id)
    else:
        form = ContractForm()
    return render(request, 'contract_create.html', {'form': form, 'rental': rental})

@login_required
def view_contract(request, contract_id):
    contract = get_object_or_404(Contract, id=contract_id)
    if request.user not in [contract.renter, contract.rental.owner]:
        return render(request, 'error.html', {'message': 'Access denied'})
    if request.method == 'POST':
        if 'agree' in request.POST and contract.status == 'pending':
            contract.agreed_at = timezone.now()
            contract.status = 'agreed'
            contract.save()
            messages.success(request, "Contract agreed successfully.")
        elif 'dispute' in request.POST:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, contract.rental.owner)
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=f"Dispute initiated for contract #{contract.id}: {request.POST.get('dispute_reason', 'No reason provided')}"
            )
            contract.status = 'disputed'
            contract.save()
            return redirect('messaging', conversation_id=conversation.id)
    return render(request, 'contract_view.html', {'contract': contract})

@login_required
def download_contract(request, contract_id):
    contract = get_object_or_404(Contract, id=contract_id)
    if request.user not in [contract.renter, contract.rental.owner]:
        return HttpResponse("Unauthorized", status=403)
    if not contract.contract_file:
        return HttpResponse("Contract file not available", status=404)
    response = HttpResponse(contract.contract_file, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="contract_{contract.id}.txt"'
    return response