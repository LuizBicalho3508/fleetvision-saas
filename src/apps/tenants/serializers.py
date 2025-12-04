from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserProfile, Tenant

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'subdomain', 'logo_url', 'primary_color']

class UserProfileSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['role', 'phone', 'tenant']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customiza o payload do JWT para incluir dados do Tenant e Role
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Adicionar campos customizados ao token
        token['username'] = user.username
        
        if hasattr(user, 'profile'):
            token['role'] = user.profile.role
            if user.profile.tenant:
                token['tenant_id'] = str(user.profile.tenant.id)
                token['tenant_name'] = user.profile.tenant.name
                token['tenant_subdomain'] = user.profile.tenant.subdomain
        
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Retorna também os dados do usuário na resposta do login
        serializer = UserSerializer(self.user)
        data['user'] = serializer.data
        return data