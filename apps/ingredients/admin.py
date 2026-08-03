from django.contrib import admin
from .models import Ingredient, IngredientEditProposal


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['inci_name', 'purpose', 'created_at']
    search_fields = ['inci_name', 'purpose']


@admin.register(IngredientEditProposal)
class IngredientEditProposalAdmin(admin.ModelAdmin):
    list_display = ['ingredient', 'submitted_by', 'status', 'created_at', 'reviewed_by']
    list_filter = ['status']
    readonly_fields = ['ingredient', 'proposed_data', 'submitted_by', 'created_at']
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
