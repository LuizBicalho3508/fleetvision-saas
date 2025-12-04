from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="FleetVision API",
      default_version='v1',
      description="API completa para Gestão de Frotas e Telemetria SaaS",
      contact=openapi.Contact(email="contato@fleetvision.com.br"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Alteração na urlpatterns
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Frontend (Dashboard na Raiz)
    path('', include('apps.tenants.urls')), 
    
    # API (Mantém prefixo /api/v1/)
    path('api/v1/', include('apps.tenants.urls')),
    path('api/v1/', include('apps.fleet.urls')),
    
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]