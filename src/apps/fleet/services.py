import requests
import math
from django.conf import settings
from django.utils import timezone
from .models import Vehicle, DriverScore

class TraccarService:
    # ... (Mantenha o código existente da Fase 3 aqui: __init__, get_devices, sync_devices) ...
    def __init__(self):
        self.base_url = settings.TRACCAR_BASE_URL
        self.auth = (settings.TRACCAR_USER, settings.TRACCAR_PASSWORD)

    def get_devices(self):
        try:
            response = requests.get(f"{self.base_url}/api/devices", auth=self.auth)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar no Traccar: {e}")
            return []

    def sync_devices(self, default_tenant=None):
        devices = self.get_devices()
        synced_count = 0
        from .models import Vehicle
        for device in devices:
            if not default_tenant: continue
            obj, created = Vehicle.objects.update_or_create(
                traccar_device_id=device['id'],
                defaults={
                    'name': device.get('name', 'Sem Nome'),
                    'tenant': default_tenant,
                    'last_update': device.get('lastUpdate'),
                }
            )
            synced_count += 1
        return synced_count

class ScoreService:
    """Processa eventos de telemetria e atualiza o Score"""
    
    @staticmethod
    def process_event(vehicle, event_type):
        today = timezone.now().date()
        tenant = vehicle.tenant

        # Pega ou cria o score de hoje
        score_obj, created = DriverScore.objects.get_or_create(
            vehicle=vehicle,
            date=today,
            defaults={'tenant': tenant, 'score': 100}
        )
        
        penalty = 0
        
        # Aplica a penalidade baseada na configuração do Tenant
        if event_type == 'overspeed':
            score_obj.overspeed_count += 1
            penalty = tenant.weight_overspeed
            
        elif event_type == 'hardAcceleration':
            score_obj.harsh_acceleration_count += 1
            penalty = tenant.weight_harsh_acceleration
            
        elif event_type == 'hardBraking':
            score_obj.harsh_braking_count += 1
            penalty = tenant.weight_harsh_braking
            
        elif event_type == 'hardCornering':
            score_obj.harsh_cornering_count += 1
            penalty = tenant.weight_harsh_cornering

        # Atualiza o score (mínimo 0)
        score_obj.score = max(0, score_obj.score - penalty)
        score_obj.save()
        
        return score_obj

class RouteOptimizer:
    """
    Otimiza rotas usando a Heurística do Vizinho Mais Próximo (Nearest Neighbor).
    Simples, rápido e eficaz para rotas do dia a dia.
    """
    
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        """Calcula distância em km entre dois pontos (fórmula de Haversine)"""
        R = 6371  # Raio da Terra em km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2)**2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @classmethod
    def optimize_route(cls, route):
        stops = list(route.stops.filter(status='PENDING'))
        if not stops:
            return 0

        # Ponto de partida (pode ser a posição atual do veículo ou a primeira parada)
        # Aqui assumimos que a primeira parada (sequence 0 ou 1) é o depósito/início
        # Se não tiver ordem, pegamos o primeiro da lista
        current_stop = stops.pop(0) 
        optimized_stops = [current_stop]
        total_distance = 0

        while stops:
            nearest_stop = None
            min_dist = float('inf')

            for stop in stops:
                dist = cls.haversine(
                    current_stop.latitude, current_stop.longitude,
                    stop.latitude, stop.longitude
                )
                if dist < min_dist:
                    min_dist = dist
                    nearest_stop = stop

            if nearest_stop:
                total_distance += min_dist
                optimized_stops.append(nearest_stop)
                stops.remove(nearest_stop)
                current_stop = nearest_stop

        # Salva a nova sequência no banco
        for index, stop in enumerate(optimized_stops):
            stop.sequence = index + 1
            stop.save()
            
        return round(total_distance, 2)

# ... (Mantenha TraccarService, ScoreService, RouteOptimizer) ...

class FinancialService:
    """
    Gerencia cobranças e integração com Gateway de Pagamento (Asaas).
    """
    
    @staticmethod
    def generate_monthly_invoices(tenant):
        """Gera contas a receber baseadas nos contratos ativos"""
        from .models import Contract, Expense # Import local para evitar ciclo
        from django.utils import timezone
        
        today = timezone.now().date()
        contracts = Contract.objects.filter(tenant=tenant, status='ACTIVE')
        generated_count = 0
        
        # Lógica simplificada: Gera um registro de "Receita" (Simulado aqui como log ou print)
        # Em produção, isso criaria um registro numa tabela 'Invoice' ou chamaria o Asaas
        for contract in contracts:
            # Exemplo de payload para o Asaas
            payload = {
                "customer": contract.asaas_customer_id,
                "billingType": "BOLETO",
                "value": float(contract.value),
                "dueDate": f"{today.year}-{today.month}-{contract.due_day}"
            }
            # requests.post('https://api.asaas.com/v3/payments', json=payload, headers=...)
            generated_count += 1
            
        return generated_count