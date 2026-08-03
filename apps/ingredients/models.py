from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Ingredient(models.Model):
    inci_name = models.CharField(max_length=100, unique=True, verbose_name="INCI Name")
    purpose = models.CharField(max_length=100, verbose_name="Purpose", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"
        ordering = ['id']

    def __str__(self):
        return self.inci_name


class IngredientEditProposal(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='edit_proposals')
    proposed_data = models.JSONField(help_text="Fields and values proposed for this edit.")
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Ingredient Edit Proposal"
        verbose_name_plural = "Ingredient Edit Proposals"
        ordering = ['-created_at']

    def __str__(self):
        return f"Edit proposal for {self.ingredient} ({self.status})"

    def approve(self, reviewer):
        for field, value in self.proposed_data.items():
            setattr(self.ingredient, field, value)
        self.ingredient.save()

        self.status = 'APPROVED'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()

    def reject(self, reviewer):
        self.status = 'REJECTED'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
