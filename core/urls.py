from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import (HomeView, SearchView, ListingView, ProfileView, BookingView, signup, payment, notifications,
                    like_post, add_comment, AddListingView, AddPostView, add_review, chat, DashboardView)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('search/', SearchView.as_view(), name='search'),
    path('listing/<int:pk>/', ListingView.as_view(), name='listing'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('signup/', signup, name='signup'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('booking/<int:item_id>/', BookingView.as_view(), name='booking'),
    path('payment/<int:reservation_id>/', payment, name='payment'),
    path('notifications/', notifications, name='notifications'),
    path('like/<int:post_id>/', like_post, name='like_post'),
    path('comment/<int:post_id>/', add_comment, name='add_comment'),
    path('add-listing/', AddListingView.as_view(), name='add_listing'),
    path('add-post/', AddPostView.as_view(), name='add_post'),
    path('review/<int:item_id>/', add_review, name='add_review'),
    path('chat/<int:user_id>/', chat, name='chat'),
]