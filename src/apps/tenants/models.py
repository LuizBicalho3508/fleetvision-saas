from django.db import models
from apps.core.models import TimeStampedModel
from django.contrib.auth.models import User

class Tenant(TimeStampedModel):
    name = models.CharField(max_length=100, verbose_name="Nome da Empresa")
    subdomain = models.CharField(max_length=100, unique=True, verbose_name="Subdomínio")
    domain = models.CharField(max_length=255, blank=True, null=True, unique=True, verbose_name="Domínio Personalizado")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    
    # White Label Configuration
    primary_color = models.CharField(max_length=7, default="#007bff", verbose_name="Cor Primária")
    logo_url = models.URLField(blank=True, null=True, verbose_name="URL do Logo")

    # --- Configuração de Score (Fase 6) ---
    weight_overspeed = models.IntegerField(default=10, verbose_name="Peso: Excesso de Velocidade")
    weight_harsh_acceleration = models.IntegerField(default=5, verbose_name="Peso: Aceleração Brusca")
    weight_harsh_braking = models.IntegerField(default=5, verbose_name="Peso: Freada Brusca")
    weight_harsh_cornering = models.IntegerField(default=5, verbose_name="Peso: Curva Brusca")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Inquilino (Tenant)"
        verbose_name_plural = "Inquilinos (Tenants)"

class UserProfile(TimeStampedModel):
    """
    Extensão do usuário para suportar multitenancy e roles.
    """
    ROLE_CHOICES = (
        ('global_admin', 'Admin Geral (SaaS)'),
        ('tenant_admin', 'Admin da Empresa'),
        ('manager', 'Gestor de Frota'),
        ('driver', 'Motorista'),
        ('viewer', 'Visualizador'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Usuário")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users', null=True, blank=True, verbose_name="Empresa")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer', verbose_name="Cargo")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"