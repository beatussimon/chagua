from django.urls import path
from . import views

urlpatterns = [
    path('transaction/<int:contract_id>/', views.transaction_detail, name='transaction_detail'),
]