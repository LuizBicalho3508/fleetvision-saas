from django.contrib import admin
from .models import (
    Vehicle, Tire, MaintenancePlan, WorkOrder, 
    DriverScore, WorkShift, ShiftEvent,
    DeliveryRoute, RouteStop,
    Contract, Expense, Fine
)

# --- Inlines ---
class ShiftEventInline(admin.TabularInline):
    model = ShiftEvent
    extra = 0
    readonly_fields = ('timestamp', 'latitude', 'longitude')

class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    fields = ('sequence', 'address', 'latitude', 'longitude', 'status')

# --- Admins ---

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'current_km', 'last_update')
    list_filter = ('tenant', 'ignition')
    search_fields = ('name', 'traccar_device_id')

@admin.register(Tire)
class TireAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'brand', 'position', 'vehicle')
    list_filter = ('position', 'tenant')

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'interval_km', 'tenant')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'plan', 'status', 'cost')
    list_filter = ('status', 'tenant')

@admin.register(DriverScore)
class DriverScoreAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'date', 'score')
    list_filter = ('tenant', 'date')

@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    list_display = ('driver', 'start_time', 'end_time', 'status')
    inlines = [ShiftEventInline]

@admin.register(DeliveryRoute)
class DeliveryRouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'status', 'total_km_predicted')
    inlines = [RouteStopInline]

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'value', 'due_day', 'status')
    list_filter = ('status', 'tenant')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'category', 'amount', 'due_date', 'is_paid')
    list_filter = ('category', 'is_paid', 'tenant')

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'amount', 'infraction_date', 'is_paid')
    list_filter = ('is_paid', 'tenant')