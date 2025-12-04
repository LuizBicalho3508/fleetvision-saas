from django.db import models
from apps.core.models import TimeStampedModel
from apps.tenants.models import Tenant

class Vehicle(TimeStampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='vehicles', verbose_name="Empresa")
    traccar_device_id = models.IntegerField(unique=True, verbose_name="ID no Traccar")
    
    name = models.CharField(max_length=100, verbose_name="Nome/Placa")
    plate = models.CharField(max_length=20, blank=True, null=True, verbose_name="Placa")
    model = models.CharField(max_length=50, blank=True, null=True, verbose_name="Modelo")
    year = models.IntegerField(null=True, blank=True, verbose_name="Ano")
    fuel_type = models.CharField(max_length=20, default='diesel', verbose_name="Combustível")
    
    # Hodômetro (Importante para manutenção)
    current_km = models.FloatField(default=0, verbose_name="Km Atual")
    
    # Telemetria
    last_position_lat = models.FloatField(null=True, blank=True)
    last_position_lng = models.FloatField(null=True, blank=True)
    last_speed = models.FloatField(default=0, verbose_name="Velocidade (km/h)")
    last_update = models.DateTimeField(null=True, blank=True, verbose_name="Última Comunicação")
    ignition = models.BooleanField(default=False, verbose_name="Ignição")
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        ordering = ['name']

class Tire(TimeStampedModel):
    POSITION_CHOICES = (
        ('FL', 'Frente Esquerda'),
        ('FR', 'Frente Direita'),
        ('RL', 'Traseira Esquerda'),
        ('RR', 'Traseira Direita'),
        ('SPARE', 'Estepe'),
        ('STOCK', 'Estoque'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='tires')
    serial_number = models.CharField(max_length=50, unique=True, verbose_name="Número de Série/DOT")
    brand = models.CharField(max_length=50, verbose_name="Marca")
    position = models.CharField(max_length=10, choices=POSITION_CHOICES, default='STOCK', verbose_name="Posição")
    
    # Vida Útil
    initial_tread_depth = models.FloatField(verbose_name="Sulco Inicial (mm)", default=8.0)
    current_tread_depth = models.FloatField(verbose_name="Sulco Atual (mm)", default=8.0)
    accumulated_km = models.FloatField(default=0, verbose_name="Km Acumulado")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.brand} - {self.serial_number}"

class MaintenancePlan(TimeStampedModel):
    """Ex: Troca de Óleo a cada 10.000km"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="Nome do Plano")
    interval_km = models.IntegerField(verbose_name="Intervalo (Km)")
    interval_days = models.IntegerField(null=True, blank=True, verbose_name="Intervalo (Dias)")
    
    def __str__(self):
        return f"{self.name} ({self.interval_km}km)"

class WorkOrder(TimeStampedModel):
    """Registro de Manutenção realizada ou agendada"""
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('IN_PROGRESS', 'Em Andamento'),
        ('COMPLETED', 'Concluída'),
        ('CANCELED', 'Cancelada'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='work_orders')
    plan = models.ForeignKey(MaintenancePlan, on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.TextField(verbose_name="Descrição do Serviço")
    km_at_service = models.FloatField(verbose_name="Km no Serviço")
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Custo Total")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"OS #{self.id} - {self.vehicle.name}"
    
# ... (Mantenha Vehicle, Tire, MaintenancePlan, WorkOrder) ...

class DriverScore(TimeStampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='scores')
    date = models.DateField(verbose_name="Data Referência")
    
    # Pontuação (Começa em 100 e desce)
    score = models.IntegerField(default=100, verbose_name="Pontuação")
    
    # Contadores de eventos
    overspeed_count = models.IntegerField(default=0)
    harsh_acceleration_count = models.IntegerField(default=0)
    harsh_braking_count = models.IntegerField(default=0)
    harsh_cornering_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('vehicle', 'date')
        verbose_name = "Score Diário"
        ordering = ['-date', '-score']

    def __str__(self):
        return f"{self.vehicle.name} - {self.date} - Score: {self.score}"
    
# ... (Mantenha todo o código anterior) ...

class WorkShift(TimeStampedModel):
    """
    Representa a jornada diária de um motorista (um 'dia' de trabalho).
    """
    STATUS_CHOICES = (
        ('OPEN', 'Em Aberto'),
        ('CLOSED', 'Fechada'),
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    driver = models.ForeignKey('tenants.UserProfile', on_delete=models.CASCADE, related_name='shifts', verbose_name="Motorista")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Veículo Utilizado")
    
    start_time = models.DateTimeField(verbose_name="Início da Jornada")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Fim da Jornada")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    
    # Totais calculados (cache para relatórios)
    total_driving_seconds = models.IntegerField(default=0)
    total_meal_seconds = models.IntegerField(default=0)
    total_rest_seconds = models.IntegerField(default=0)
    total_wait_seconds = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Jornada de Trabalho"
        verbose_name_plural = "Jornadas"
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.driver.user.username} - {self.start_time.date()}"

class ShiftEvent(TimeStampedModel):
    """
    Eventos dentro da jornada (batidas de ponto).
    """
    TYPE_CHOICES = (
        ('START_SHIFT', 'Início de Jornada'),
        ('START_MEAL', 'Início Refeição'),
        ('END_MEAL', 'Fim Refeição'),
        ('START_REST', 'Início Descanso'),
        ('END_REST', 'Fim Descanso'),
        ('START_WAIT', 'Início Espera'),
        ('END_WAIT', 'Fim Espera'),
        ('END_SHIFT', 'Fim de Jornada'),
    )

    shift = models.ForeignKey(WorkShift, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Tipo de Evento")
    timestamp = models.DateTimeField(verbose_name="Horário")
    
    # Localização da batida (GPS do celular do motorista)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Evento de Jornada"
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.timestamp}"
    
# ... (Mantenha todo o código anterior) ...

class DeliveryRoute(TimeStampedModel):
    STATUS_CHOICES = (
        ('DRAFT', 'Rascunho'),
        ('OPTIMIZED', 'Otimizada'),
        ('IN_PROGRESS', 'Em Andamento'),
        ('COMPLETED', 'Concluída'),
        ('CANCELED', 'Cancelada'),
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="Nome da Rota")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='routes')
    driver = models.ForeignKey('tenants.UserProfile', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(verbose_name="Data da Entrega")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    total_km_predicted = models.FloatField(default=0, verbose_name="Km Previsto")

    class Meta:
        verbose_name = "Rota de Entrega"
        verbose_name_plural = "Rotas de Entrega"

    def __str__(self):
        return f"{self.name} - {self.date}"

class RouteStop(TimeStampedModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('VISITED', 'Visitado/Entregue'),
        ('FAILED', 'Falhou/Não Entregue'),
    )

    route = models.ForeignKey(DeliveryRoute, on_delete=models.CASCADE, related_name='stops')
    sequence = models.IntegerField(default=0, verbose_name="Ordem de Parada")
    
    address = models.CharField(max_length=255, verbose_name="Endereço")
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Validação da entrega (Geofence virtual)
    arrival_time = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['sequence']
        verbose_name = "Parada"

    def __str__(self):
        return f"{self.sequence}. {self.address} ({self.get_status_display()})"
    
# ... (Mantenha todo o código anterior) ...

class Contract(TimeStampedModel):
    """Contratos de Receita (Ex: Mensalidade de Rastreamento)"""
    STATUS_CHOICES = (
        ('ACTIVE', 'Ativo'),
        ('SUSPENDED', 'Suspenso'),
        ('CANCELED', 'Cancelado'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100, verbose_name="Cliente")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Mensal")
    due_day = models.IntegerField(default=10, verbose_name="Dia de Vencimento")
    start_date = models.DateField(verbose_name="Início")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fim")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    asaas_customer_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Asaas")

    class Meta:
        verbose_name = "Contrato"

    def __str__(self):
        return f"{self.customer_name} - R$ {self.value}"

class Expense(TimeStampedModel):
    """Despesas da Frota (IPVA, Seguro, etc)"""
    CATEGORY_CHOICES = (
        ('IPVA', 'IPVA/Licenciamento'),
        ('INSURANCE', 'Seguro'),
        ('FUEL', 'Combustível'),
        ('MAINTENANCE', 'Manutenção'),
        ('OTHER', 'Outros'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=200, verbose_name="Descrição")
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    due_date = models.DateField(verbose_name="Vencimento")
    paid_at = models.DateField(null=True, blank=True, verbose_name="Data Pagamento")
    is_paid = models.BooleanField(default=False, verbose_name="Pago")

    class Meta:
        verbose_name = "Despesa"
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.get_category_display()} - {self.vehicle.name}"

class Fine(TimeStampedModel):
    """Multas de Trânsito"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fines')
    driver = models.ForeignKey('tenants.UserProfile', on_delete=models.SET_NULL, null=True, blank=True)
    
    infraction_date = models.DateField(verbose_name="Data da Infração")
    description = models.CharField(max_length=200, verbose_name="Infração")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    points = models.IntegerField(default=0, verbose_name="Pontos na CNH")
    
    due_date = models.DateField(verbose_name="Vencimento")
    is_paid = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Multa"

    def __str__(self):
        return f"Multa {self.vehicle.plate} - {self.amount}"