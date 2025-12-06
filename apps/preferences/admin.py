from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'skin_type',
        'vegan_only',
        'cruelty_free_only',
        'get_allergies_count',
        'updated_at'
    ]

    list_filter = ['skin_type', 'vegan_only', 'cruelty_free_only', 'fragrance_free']
    search_fields = ['user__username', 'user__email']

    filter_horizontal = ['allergic_to', 'avoided_ingredients', 'preferred_ingredients']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Ingredients Preferences', {
            'fields': ('allergic_to', 'avoided_ingredients', 'preferred_ingredients'),
            'description': 'Select ingredients the user is allergic to, wants to avoid, or prefers.'
        }),
        ('Skin Information', {
            'fields': ('skin_type', 'skin_concerns')
        }),
        ('Product Preferences', {
            'fields': ('vegan_only', 'cruelty_free_only', 'fragrance_free')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def get_allergies_count(self, obj):
        return obj.allergic_to.count()

    get_allergies_count.short_description = 'Allergies'
