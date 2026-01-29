from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_safe_count', 'get_moderate_count', 'get_unsafe_count', 'updated_at']
    search_fields = ['user__username']
    filter_horizontal = ['safe_ingredients', 'moderate_ingredients', 'unsafe_ingredients']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Safety Preferences', {
            'fields': ('safe_ingredients', 'moderate_ingredients', 'unsafe_ingredients'),
            'description': 'Select ingredients by safety level for this user.'
        }),
    )

    def get_safe_count(self, obj):
        return obj.safe_ingredients.count()

    get_safe_count.short_description = 'Safe (Green)'

    def get_moderate_count(self, obj):
        return obj.moderate_ingredients.count()

    get_moderate_count.short_description = 'Moderate (Yellow)'

    def get_unsafe_count(self, obj):
        return obj.unsafe_ingredients.count()

    get_unsafe_count.short_description = 'Unsafe (Red)'
