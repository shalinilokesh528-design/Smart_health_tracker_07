from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientTask, HealthLog, PatientVisit
from .models import Location, Hospital, SOSAlert, ExerciseVideo

# 🔹 Register the custom User model
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'unique_id', 'role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'unique_id')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('unique_id', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

# 🔹 Register other models
admin.site.register(PatientTask)
admin.site.register(HealthLog)
admin.site.register(PatientVisit)
admin.site.register(Location)
admin.site.register(Hospital)

# 🔹 Register SOS Alert Model
@admin.register(SOSAlert)
class SOSAlertAdmin(admin.ModelAdmin):
    list_display = ('patient', 'status', 'created_at', 'acknowledged_by_doctor', 'acknowledged_by_therapist')
    list_filter = ('status', 'created_at', 'acknowledged_by_doctor', 'acknowledged_by_therapist')
    search_fields = ('patient__username', 'patient__unique_id', 'message')
    readonly_fields = ('created_at', 'acknowledged_at', 'resolved_at')
    ordering = ('-created_at',)

# 🔹 Register Exercise Video Model
@admin.register(ExerciseVideo)
class ExerciseVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'therapist', 'exercise_type', 'difficulty_level', 'is_active', 'views_count', 'created_at')
    list_filter = ('exercise_type', 'difficulty_level', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'therapist__username')
    readonly_fields = ('created_at', 'updated_at', 'views_count')
    ordering = ('-created_at',)
    fieldsets = (
        ('Video Information', {
            'fields': ('title', 'description', 'therapist', 'exercise_type')
        }),
        ('Media Files', {
            'fields': ('video_file', 'thumbnail')
        }),
        ('Details', {
            'fields': ('duration_minutes', 'difficulty_level', 'is_active')
        }),
        ('Statistics', {
            'fields': ('views_count', 'created_at', 'updated_at')
        }),
    )