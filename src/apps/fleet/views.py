from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import WorkShift, ShiftEvent
from .serializers import WorkShiftSerializer, ShiftEventSerializer
from django.utils import timezone
from django.db import transaction
from .models import DeliveryRoute, RouteStop
from .serializers import DeliveryRouteSerializer, RouteStopSerializer
from .services import RouteOptimizer
from .models import Contract, Expense, Fine
from .serializers import ContractSerializer, ExpenseSerializer, FineSerializer
from .services import FinancialService
from .forms import VehicleForm, DeliveryRouteForm, ExpenseForm, ContractForm
from .models import Vehicle, Tire, MaintenancePlan, WorkOrder, DriverScore
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import VehicleForm
from .serializers import (
    VehicleSerializer, TireSerializer, MaintenancePlanSerializer, 
    WorkOrderSerializer, DriverScoreSerializer
)
from apps.tenants.models import Tenant
from .services import TraccarService, ScoreService

class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.tenant:
            return Vehicle.objects.filter(tenant=user.profile.tenant)
        if user.is_superuser:
            return Vehicle.objects.all()
        return Vehicle.objects.none()

    @action(detail=False, methods=['post'])
    def sync_traccar(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Apenas admin pode sincronizar"}, status=403)
        tenant_id = request.data.get('tenant_id')
        tenant = Tenant.objects.filter(id=tenant_id).first() if tenant_id else Tenant.objects.first()
        if not tenant:
            return Response({"error": "Nenhum Tenant encontrado"}, status=400)
        service = TraccarService()
        count = service.sync_devices(default_tenant=tenant)
        return Response({"status": "Sincronizado", "veiculos_processados": count})

class TireViewSet(viewsets.ModelViewSet):
    serializer_class = TireSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Tire.objects.filter(tenant=self.request.user.profile.tenant)

class MaintenancePlanViewSet(viewsets.ModelViewSet):
    serializer_class = MaintenancePlanSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return MaintenancePlan.objects.filter(tenant=self.request.user.profile.tenant)

class WorkOrderViewSet(viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return WorkOrder.objects.filter(tenant=self.request.user.profile.tenant)

class DriverScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """Exibe o Ranking de motoristas"""
    serializer_class = DriverScoreSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return DriverScore.objects.filter(tenant=self.request.user.profile.tenant).order_by('-date', '-score')

# ...
class MapDashboardView(LoginRequiredMixin, TemplateView):
    # ATUALIZADO: Aponta para o novo template integrado
    template_name = "fleet/map_dashboard.html"
# ...

class TraccarWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        positions = data if isinstance(data, list) else [data]
        channel_layer = get_channel_layer()

        for pos in positions:
            device_id = pos.get('deviceId')
            if not device_id: continue
                
            try:
                vehicle = Vehicle.objects.get(traccar_device_id=device_id)
                
                # 1. Atualiza Telemetria Básica
                vehicle.last_position_lat = pos.get('latitude')
                vehicle.last_position_lng = pos.get('longitude')
                vehicle.last_speed = pos.get('speed', 0) * 1.852
                attributes = pos.get('attributes', {})
                vehicle.ignition = attributes.get('ignition', False)
                
                # Atualiza Hodômetro se disponível (totalDistance vem em metros)
                if 'totalDistance' in attributes:
                     vehicle.current_km = attributes['totalDistance'] / 1000.0
                
                vehicle.save()

                # 2. Processa Eventos de Score (Alarmes)
                # O Traccar envia alarmes no campo 'attributes': {'alarm': 'overspeed'}
                alarm_type = attributes.get('alarm')
                score_updated = None
                
                if alarm_type:
                    # Mapeia eventos do Traccar para nossa lógica
                    # (overspeed, hardAcceleration, hardBraking, hardCornering)
                    score_updated = ScoreService.process_event(vehicle, alarm_type)

                # 3. Envia para WebSocket (Real-Time)
                payload = {
                    'id': vehicle.id,
                    'name': vehicle.name,
                    'lat': vehicle.last_position_lat,
                    'lng': vehicle.last_position_lng,
                    'speed': round(vehicle.last_speed, 1),
                    'ignition': vehicle.ignition,
                    'score': score_updated.score if score_updated else None
                }

                async_to_sync(channel_layer.group_send)(
                    f"tenant_{vehicle.tenant.id}",
                    {"type": "vehicle_update", "message": payload}
                )
                
                # Envia para admin global também
                async_to_sync(channel_layer.group_send)(
                    "admin_global",
                    {"type": "vehicle_update", "message": payload}
                )

            except Vehicle.DoesNotExist:
                pass
        
        return Response(status=status.HTTP_200_OK)
    
class WorkShiftViewSet(viewsets.ModelViewSet):
    """
    Gestão de Jornada.
    Endpoint principal para App Mobile.
    """
    serializer_class = WorkShiftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Se for motorista, vê apenas as suas
        if hasattr(user, 'profile') and user.profile.role == 'driver':
            return WorkShift.objects.filter(driver=user.profile).order_by('-start_time')
        # Gestores veem tudo do tenant
        return WorkShift.objects.filter(tenant=user.profile.tenant).order_by('-start_time')

    @action(detail=False, methods=['post'])
    def clock_event(self, request):
        """
        Registra um evento (Início, Refeição, Fim, etc).
        Se for START_SHIFT, cria nova jornada.
        Se for END_SHIFT, fecha a jornada.
        """
        user_profile = request.user.profile
        event_type = request.data.get('event_type')
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        vehicle_id = request.data.get('vehicle_id')
        
        if not event_type:
            return Response({"error": "Tipo de evento obrigatório"}, status=400)

        with transaction.atomic():
            # Tenta achar jornada aberta
            current_shift = WorkShift.objects.filter(driver=user_profile, status='OPEN').last()

            # Lógica de Abertura
            if event_type == 'START_SHIFT':
                if current_shift:
                    return Response({"error": "Você já possui uma jornada aberta."}, status=400)
                
                vehicle = Vehicle.objects.get(id=vehicle_id) if vehicle_id else None
                
                current_shift = WorkShift.objects.create(
                    tenant=user_profile.tenant,
                    driver=user_profile,
                    vehicle=vehicle,
                    start_time=timezone.now(),
                    status='OPEN'
                )

            # Validação para outros eventos
            if not current_shift and event_type != 'START_SHIFT':
                return Response({"error": "Nenhuma jornada aberta. Inicie a jornada primeiro."}, status=400)

            # Registro do Evento
            ShiftEvent.objects.create(
                shift=current_shift,
                event_type=event_type,
                timestamp=timezone.now(),
                latitude=lat,
                longitude=lng
            )

            # Lógica de Fechamento
            if event_type == 'END_SHIFT':
                current_shift.status = 'CLOSED'
                current_shift.end_time = timezone.now()
                current_shift.save()
                
                # TODO: Aqui poderíamos disparar o cálculo das horas (Fase futura)

            return Response(WorkShiftSerializer(current_shift).data, status=201)
        
class DeliveryRouteViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryRouteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DeliveryRoute.objects.filter(tenant=self.request.user.profile.tenant).order_by('-date')

    @action(detail=True, methods=['post'])
    def optimize(self, request, pk=None):
        """Reordena as paradas para a menor distância total"""
        route = self.get_object()
        
        # Chama o serviço de otimização
        total_km = RouteOptimizer.optimize_route(route)
        
        route.status = 'OPTIMIZED'
        route.total_km_predicted = total_km
        route.save()
        
        return Response({
            "status": "Rota otimizada com sucesso",
            "total_km_previsto": total_km,
            "stops": RouteStopSerializer(route.stops.all().order_by('sequence'), many=True).data
        })

class RouteStopViewSet(viewsets.ModelViewSet):
    serializer_class = RouteStopSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RouteStop.objects.filter(route__tenant=self.request.user.profile.tenant)
    

class ContractViewSet(viewsets.ModelViewSet):
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Contract.objects.filter(tenant=self.request.user.profile.tenant)

    @action(detail=False, methods=['post'])
    def generate_invoices(self, request):
        """Dispara a geração de cobranças do mês"""
        tenant = request.user.profile.tenant
        count = FinancialService.generate_monthly_invoices(tenant)
        return Response({"status": "Cobranças geradas", "total": count})

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Expense.objects.filter(tenant=self.request.user.profile.tenant)

class FineViewSet(viewsets.ModelViewSet):
    serializer_class = FineSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Fine.objects.filter(tenant=self.request.user.profile.tenant)
    

class VehicleListView(LoginRequiredMixin, ListView):
    model = Vehicle
    template_name = 'fleet/vehicle_list.html'
    context_object_name = 'vehicles'

    def get_queryset(self):
        # Filtra pelo tenant do usuário
        return Vehicle.objects.filter(tenant=self.request.user.profile.tenant)

class VehicleCreateView(LoginRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'fleet/vehicle_form.html'
    success_url = reverse_lazy('vehicle-list')

    def form_valid(self, form):
        # Atribui o tenant automaticamente antes de salvar
        form.instance.tenant = self.request.user.profile.tenant
        return super().form_valid(form)

class VehicleUpdateView(LoginRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'fleet/vehicle_form.html'
    success_url = reverse_lazy('vehicle-list')

    def get_queryset(self):
        return Vehicle.objects.filter(tenant=self.request.user.profile.tenant)

class VehicleDeleteView(LoginRequiredMixin, DeleteView):
    model = Vehicle
    template_name = 'fleet/vehicle_confirm_delete.html'
    success_url = reverse_lazy('vehicle-list')

    def get_queryset(self):
        return Vehicle.objects.filter(tenant=self.request.user.profile.tenant)
    

# --- Logística Views ---

class DeliveryRouteListView(LoginRequiredMixin, ListView):
    model = DeliveryRoute
    template_name = 'fleet/route_list.html'
    context_object_name = 'routes'

    def get_queryset(self):
        return DeliveryRoute.objects.filter(tenant=self.request.user.profile.tenant).order_by('-date')

class DeliveryRouteCreateView(LoginRequiredMixin, CreateView):
    model = DeliveryRoute
    form_class = DeliveryRouteForm
    template_name = 'fleet/route_form.html'
    success_url = reverse_lazy('route-list')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.profile.tenant
        return super().form_valid(form)

# --- Financeiro Views ---

class FinancialListView(LoginRequiredMixin, TemplateView):
    template_name = 'fleet/financial_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.profile.tenant
        
        context['expenses'] = Expense.objects.filter(tenant=tenant).order_by('-due_date')[:10]
        context['contracts'] = Contract.objects.filter(tenant=tenant)
        
        # Totais simples
        from django.db.models import Sum
        context['total_expenses'] = Expense.objects.filter(tenant=tenant, is_paid=False).aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_revenue'] = Contract.objects.filter(tenant=tenant, status='ACTIVE').aggregate(Sum('value'))['value__sum'] or 0
        
        return context

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'fleet/expense_form.html'
    success_url = reverse_lazy('financial-list')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.profile.tenant
        return super().form_valid(form)

class ContractCreateView(LoginRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'fleet/expense_form.html' # Reutilizando template genérico de form
    success_url = reverse_lazy('financial-list')

    def form_valid(self, form):
        form.instance.tenant = self.request.user.profile.tenant
        return super().form_valid(form)