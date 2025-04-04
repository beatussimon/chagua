from django.urls import path
from . import views

urlpatterns = [
    path('', views.messaging, name='messaging'),
    path('<int:conversation_id>/', views.messaging, name='messaging'),
    path('new/', views.new_conversation, name='new_conversation'),
]