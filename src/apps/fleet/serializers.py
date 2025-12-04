from rest_framework import serializers
from .models import (
    Vehicle, Tire, MaintenancePlan, WorkOrder, 
    DriverScore, WorkShift, ShiftEvent, 
    DeliveryRoute, RouteStop,
    Contract, Expense, Fine # Novos
)
# ... (Mantenha VehicleSerializer, TireSerializer, etc) ...
class TireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tire
        fields = '__all__'

class MaintenancePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenancePlan
        fields = '__all__'

class WorkOrderSerializer(serializers.ModelSerializer):
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    class Meta:
        model = WorkOrder
        fields = '__all__'

class DriverScoreSerializer(serializers.ModelSerializer):
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    
    class Meta:
        model = DriverScore
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tires = TireSerializer(many=True, read_only=True)
    pending_maintenance = serializers.SerializerMethodField()
    # Adicionamos o score de hoje no veículo para facilidade
    today_score = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = '__all__'

    def get_pending_maintenance(self, obj):
        return obj.work_orders.filter(status='PENDING').count()
    
    def get_today_score(self, obj):
        from django.utils import timezone
        score = obj.scores.filter(date=timezone.now().date()).first()
        return score.score if score else 100
    
class ShiftEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftEvent
        fields = '__all__'

class WorkShiftSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.user.get_full_name', read_only=True)
    events = ShiftEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkShift
        fields = '__all__'

class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = '__all__'

class DeliveryRouteSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    
    class Meta:
        model = DeliveryRoute
        fields = '__all__'


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = '__all__'

class ExpenseSerializer(serializers.ModelSerializer):
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    class Meta:
        model = Expense
        fields = '__all__'

class FineSerializer(serializers.ModelSerializer):
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    driver_name = serializers.CharField(source='driver.user.get_full_name', read_only=True)
    class Meta:
        model = Fine
        fields = '__all__'