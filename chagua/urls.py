from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('rentals/', include('rentals.urls')),
    path('messaging/', include('messaging.urls')),
    path('feedback/', include('feedback.urls')),
    path('contracts/', include('contracts.urls')),
    path('payments/', include('payments.urls')),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)