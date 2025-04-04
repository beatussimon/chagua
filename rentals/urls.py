from django.urls import path
from . import views

urlpatterns = [
    path('', views.rentals_list, name='rentals_list'),
    path('<int:rental_id>/', views.rental_detail, name='rental_detail'),
    path('create/', views.create_rental, name='create_rental'),
]