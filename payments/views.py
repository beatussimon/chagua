from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Transaction

@login_required
def transaction_detail(request, contract_id):
    contract = get_object_or_404('contracts.Contract', id=contract_id)
    if request.user not in [contract.renter, contract.rental.owner]:
        return render(request, 'error.html', {'message': 'Access denied'})
    transaction, created = Transaction.objects.get_or_create(
        contract=contract,
        defaults={'amount': contract.rental.price}
    )
    return render(request, 'transaction_detail.html', {'transaction': transaction})