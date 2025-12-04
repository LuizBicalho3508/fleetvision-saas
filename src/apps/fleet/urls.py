from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # API ViewSets
    VehicleViewSet, TraccarWebhookView, MapDashboardView,
    TireViewSet, MaintenancePlanViewSet, WorkOrderViewSet,
    DriverScoreViewSet, WorkShiftViewSet, 
    DeliveryRouteViewSet, RouteStopViewSet,
    ContractViewSet, ExpenseViewSet, FineViewSet,
    # Frontend Views (Novas)
    VehicleListView, VehicleCreateView, VehicleUpdateView, VehicleDeleteView
)
from .views import (
    # ... views anteriores ...
    DeliveryRouteListView, DeliveryRouteCreateView,
    FinancialListView, ExpenseCreateView, ContractCreateView
)

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'tires', TireViewSet, basename='tire')
router.register(r'maintenance-plans', MaintenancePlanViewSet, basename='maintenance-plan')
router.register(r'work-orders', WorkOrderViewSet, basename='work-order')
router.register(r'scores', DriverScoreViewSet, basename='driver-score')
router.register(r'shifts', WorkShiftViewSet, basename='work-shift')
router.register(r'routes', DeliveryRouteViewSet, basename='delivery-route')
router.register(r'stops', RouteStopViewSet, basename='route-stop')
router.register(r'financial/contracts', ContractViewSet, basename='contract')
router.register(r'financial/expenses', ExpenseViewSet, basename='expense')
router.register(r'financial/fines', FineViewSet, basename='fine')

urlpatterns = [
    # ... rotas anteriores (API, Webhook, Map, Vehicle) ...
    path('', include(router.urls)),
    path('integrations/traccar/webhook/', TraccarWebhookView.as_view(), name='traccar-webhook'),
    path('map/', MapDashboardView.as_view(), name='live-map'),
    
    # Frontend Veículos
    path('frontend/vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('frontend/vehicles/new/', VehicleCreateView.as_view(), name='vehicle-create'),
    path('frontend/vehicles/<uuid:pk>/edit/', VehicleUpdateView.as_view(), name='vehicle-update'),
    path('frontend/vehicles/<uuid:pk>/delete/', VehicleDeleteView.as_view(), name='vehicle-delete'),

    # Frontend Logística (Novas)
    path('frontend/routes/', DeliveryRouteListView.as_view(), name='route-list'),
    path('frontend/routes/new/', DeliveryRouteCreateView.as_view(), name='route-create'),

    # Frontend Financeiro (Novas)
    path('frontend/financial/', FinancialListView.as_view(), name='financial-list'),
    path('frontend/financial/expenses/new/', ExpenseCreateView.as_view(), name='expense-create'),
    path('frontend/financial/contracts/new/', ContractCreateView.as_view(), name='contract-create'),
]