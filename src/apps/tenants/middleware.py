from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .models import Tenant

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host().split(':')[0].lower()
        tenant = None

        # Tenta buscar por domínio personalizado
        tenant = Tenant.objects.filter(domain=host, is_active=True).first()

        # Se não achou, tenta por subdomínio (ex: empresa.fleetvision.com.br)
        if not tenant:
            parts = host.split('.')
            # Assumindo estrutura sub.dominio.com ou localhost
            if len(parts) > 1:
                subdomain = parts[0]
                tenant = Tenant.objects.filter(subdomain=subdomain, is_active=True).first()

        # Atribui o tenant ao request. Se for None, é o domínio público/admin
        request.tenant = tenant
        
        # Nota: Na Fase 2 implementaremos bloqueio se tenant for obrigatório para certas rotas
        return None