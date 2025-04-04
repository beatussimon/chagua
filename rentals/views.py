from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Rental, ServicePackage
from .forms import RentalForm

@login_required
def rentals_list(request):
    rentals = Rental.objects.all()
    packages = ServicePackage.objects.all()
    context = {'rentals': rentals, 'packages': packages}
    return render(request, 'rentals_list.html', context)

@login_required
def rental_detail(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    context = {'rental': rental}
    return render(request, 'rental_detail.html', context)

@login_required
def create_rental(request):
    if request.method == 'POST':
        form = RentalForm(request.POST, request.FILES)
        if form.is_valid():
            rental = form.save(commit=False)
            rental.owner = request.user
            rental.save()
            form.save_m2m()  # Save media
            return redirect('rentals_list')
    else:
        form = RentalForm()
    return render(request, 'rental_create.html', {'form': form})


@login_required
def create_rental(request):
    if request.method == 'POST':
        form = RentalForm(request.POST, request.FILES)
        if form.is_valid():
            rental = form.save(commit=False)
            rental.owner = request.user
            rental.save()
            form.save_m2m()  # Save many-to-many fields (e.g., media)
            return redirect('rentals_list')
    else:
        form = RentalForm()
    return render(request, 'rental_create.html', {'form': form})