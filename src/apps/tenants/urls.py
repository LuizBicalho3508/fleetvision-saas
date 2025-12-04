from django.urls import path
from .views import CustomTokenObtainPairView, MeView, DashboardView # Importe DashboardView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='user_me'),
    path('', DashboardView.as_view(), name='dashboard'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]