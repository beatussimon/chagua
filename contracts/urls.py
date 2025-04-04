from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:rental_id>/', views.create_contract, name='create_contract'),
    path('view/<int:contract_id>/', views.view_contract, name='view_contract'),
    path('download/<int:contract_id>/', views.download_contract, name='download_contract'),
]