from django.contrib import admin
from django.contrib import messages
from .models import Cosmetic, CosmeticEditProposal


@admin.register(Cosmetic)
class CosmeticAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'main_category', 'subcategory', 'product_type', 'created_at']
    search_fields = ['name', 'brand']
    list_filter = ['main_category', 'subcategory', 'product_type']
    filter_horizontal = ['ingredients']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'brand')
        }),
        ('Categories', {
            'fields': ('main_category', 'subcategory', 'product_type'),
            'description': 'Main: Face/Makeup/Body/Hands. For Face: select subcategory. For Makeup: select area (subcategory) and product type.'
        }),
        ('Ingredients - Option 1: Paste full list', {
            'fields': ('ingredients_text',),
            'description': 'Paste the full INCI ingredients list (comma-separated). Click Save to auto-match ingredients.'
        }),
        ('Ingredients - Option 2: Select manually', {
            'fields': ('ingredients',),
            'classes': ('collapse',),
        }),
    )

    def get_ingredients_count(self, obj):
        return obj.ingredients.count()

    get_ingredients_count.short_description = 'Ingredients'

    def get_ingredients_count(self, obj):
        return obj.ingredients.count()

    get_ingredients_count.short_description = 'Ingredients'

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        obj = form.instance
        if obj.ingredients_text:
            result = obj.parse_and_add_ingredients(auto_create=True)

            if result['matched']:
                messages.success(
                    request,
                    f"Matched {len(result['matched'])} ingredients"
                )

            if result['not_found']:
                messages.warning(
                    request,
                    f"Not found: {', '.join(result['not_found'][:5])}"
                )


@admin.register(CosmeticEditProposal)
class CosmeticEditProposalAdmin(admin.ModelAdmin):
    list_display = ['cosmetic', 'submitted_by', 'status', 'created_at', 'reviewed_by']
    list_filter = ['status']
    readonly_fields = ['cosmetic', 'proposed_data', 'submitted_by', 'created_at']
    actions = ['approve_proposals', 'reject_proposals']

    def approve_proposals(self, request, queryset):
        count = 0
        for proposal in queryset.filter(status='PENDING'):
            proposal.approve(reviewer=request.user)
            count += 1
        self.message_user(request, f'Approved {count} proposal(s).')
    approve_proposals.short_description = 'Approve selected proposals'

    def reject_proposals(self, request, queryset):
        count = 0
        for proposal in queryset.filter(status='PENDING'):
            proposal.reject(reviewer=request.user)
            count += 1
        self.message_user(request, f'Rejected {count} proposal(s).')
    reject_proposals.short_description = 'Reject selected proposals'
