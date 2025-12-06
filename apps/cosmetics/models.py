from django.db import models
from apps.ingredients.models import Ingredient

class Cosmetic(models.Model):
    MAIN_CATEGORIES = [
        ('FACE', 'Face'),
        ('MAKEUP', 'Make-up'),
        ('BODY', 'Body'),
    ]

    FACE_SUBCATEGORIES = [
        ('CLEANSER', 'Cleansers (gels, foams, emulsions)'),
        ('TONER', 'Toners'),
        ('SERUM', 'Serums'),
        ('MOISTURIZER', 'Moisturizers'),
        ('SPF', 'SPFs'),
    ]

    MAKEUP_SUBCATEGORIES = [
        ('EYES', 'Eyes'),
        ('FACE', 'Face'),
        ('LIPS', 'Lips')
    ]

    MAKEUP_EYES_SUBCATEGORIES = [
        ('MASCARA', 'Mascara'),
        ('EYESHADOW', 'Eyeshadow'),
        ('EYELINER', 'Eyeliner'),
        ('BROW_PENCIL', 'Brow Pencil'),
    ]

    MAKEUP_FACE_SUBCATEGORIES = [
        ('FOUNDATION', 'Foundation'),
        ('CONCEALER', 'Concealer'),
        ('POWDER', 'Powder'),
        ('BLUSH', 'Blush'),
        ('BRONZER', 'Bronzer'),
        ('HIGHLIGHTER', 'Highlighter'),
        ('CONTOUR', 'Contour'),
        ('PRIMER', 'Face Primer'),
        ('SETTING_SPRAY', 'Setting Spray'),
    ]

    MAKEUP_LIPS_SUBCATEGORIES = [
        ('LIPSTICK', 'Lipstick'),
        ('LIP_GLOSS', 'Lip Gloss'),
        ('LIP_LINER', 'Lip Liner'),
        ('LIP_BALM', 'Lip Balm'),
        ('LIP_STAIN', 'Lip Stain'),
    ]

    name = models.CharField(max_length=100, verbose_name="Name")
    brand = models.CharField(max_length=100, verbose_name="Brand")
    main_category = models.CharField(
        max_length=20,
        choices=MAIN_CATEGORIES,
        verbose_name="Main Category (Face, Make-up, Body)"
    )
    subcategory = models.CharField(
        max_length=50,
        verbose_name="Subcategory",
        blank=True,
        help_text="Face: Cleanser, Toner, Serum, Moisturizer or SPF, Makeup: Eyes, Face or Lips"
    )
    product_type = models.CharField(
        max_length=50,
        verbose_name="Product Type",
        blank=True,
        help_text="Specific product type (only for Make-up)"
    )
    ingredients = models.ManyToManyField(Ingredient, related_name='cosmetics', verbose_name="Ingredients")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kosmetyk"
        verbose_name_plural = "Kosmetyki"

    def __str__(self):
        return f"{self.name} - {self.brand}"

    def get_full_category(self):
        parts = [self.get_main_category_display()]
        if self.subcategory:
            parts.append(self.subcategory)
        if self.product_type:
            parts.append(self.product_type)
        return " > ".join(parts)
