from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('rental/<int:rental_id>/', views.rental_detail, name='rental_detail'),
    path('rental/create/', views.rental_create, name='rental_create'),
    path('rental/<int:rental_id>/edit/', views.rental_edit, name='rental_edit'),
    path('rental/<int:rental_id>/delete/', views.rental_delete, name='rental_delete'),
    path('rental/<int:rental_id>/like/', views.like_rental, name='like_rental'),
    path('rental/<int:rental_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('messaging/', views.messaging, name='messaging'),
    path('messaging/group/<int:group_id>/', views.messaging, name='messaging_group'),
    path('messaging/create-group/', views.create_group, name='create_group'),
    path('team/<int:team_id>/manage/', views.team_manage, name='team_manage'),
    path('team/<int:team_id>/history/', views.team_history, name='team_history'),
    path('feedback/', views.feedback, name='feedback'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('contract/<int:contract_id>/download/', views.download_contract, name='download_contract'),
    path('service-package/create/', views.service_package_create, name='service_package_create'),
]

handler404 = 'core.views.custom_404'