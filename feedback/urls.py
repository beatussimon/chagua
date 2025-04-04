from django.urls import path
from . import views

urlpatterns = [
    path('', views.feedback, name='feedback'),
    path('review/<int:user_id>/', views.create_review, name='create_review'),
    path('faq/', views.create_faq, name='create_faq'),
]