from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('verify/', views.verify_user, name='verify_user'),
    path('update_profile_picture/', views.update_profile_picture, name='update_profile_picture'),
    path('report_abuse/<int:user_id>/', views.report_abuse, name='report_abuse'),
]