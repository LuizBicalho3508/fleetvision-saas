from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import CustomTokenObtainPairSerializer, UserSerializer
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.fleet.models import Vehicle, WorkOrder, DriverScore
from django.utils import timezone

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class MeView(RetrieveAPIView):
    """
    Retorna os dados do usuário logado atual
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtra dados do Tenant do usuário
        tenant = self.request.user.profile.tenant
        
        # Estatísticas Reais
        context['total_vehicles'] = Vehicle.objects.filter(tenant=tenant).count()
        context['active_vehicles'] = Vehicle.objects.filter(tenant=tenant, ignition=True).count()
        context['maintenance_pending'] = WorkOrder.objects.filter(tenant=tenant, status='PENDING').count()
        
        # Alertas Hoje (Baseado no Score que baixou pontos hoje)
        today = timezone.now().date()
        # Conta quantos scores foram criados/atualizados hoje com pontuação < 100
        context['alerts_today'] = DriverScore.objects.filter(
            tenant=tenant, 
            date=today, 
            score__lt=100
        ).count()
        
        return context