from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from portfolio.views import LoginView, MeView, LogoutView, ChangePasswordView
urlpatterns=[path('admin/',admin.site.urls),path('api/auth/login/',LoginView.as_view()),path('api/auth/refresh/',TokenRefreshView.as_view()),path('api/auth/me/',MeView.as_view()),path('api/auth/logout/',LogoutView.as_view()),path('api/auth/change-password/',ChangePasswordView.as_view()),path('api/',include('portfolio.urls'))]
if settings.DEBUG: urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
