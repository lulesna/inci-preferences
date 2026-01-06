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
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='cosmetics',
        verbose_name="Ingredients",
        blank=True
    )
    ingredients_text = models.TextField(
        blank=True,
        verbose_name="Paste ingredients list",
        help_text="Paste full INCI list (separated by commas)."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cosmetic"
        verbose_name_plural = "Cosmetics"

    def __str__(self):
        return f"{self.name} - {self.brand}"

    def get_full_category(self):
        parts = [self.get_main_category_display()]
        if self.subcategory:
            parts.append(self.subcategory)
        if self.product_type:
            parts.append(self.product_type)
        return " > ".join(parts)

    def parse_and_add_ingredients(self, auto_create=True):
        if not self.ingredients_text:
            return {'matched': [], 'not_found': []}

        # potrzebne do składników typu '1,2-Hexanediol'
        import re
        ingredients = re.split(r',\s+', self.ingredients_text)

        matched = []
        not_found = []

        for ingredient in ingredients:
            clean_name = ingredient.strip().strip('.')

            if not clean_name:
                continue

            # case-insensitive
            try:
                ingredient = Ingredient.objects.get(inci_name__iexact=clean_name)
                self.ingredients.add(ingredient)
                matched.append(ingredient.inci_name)
            except Ingredient.DoesNotExist:
                not_found.append(clean_name)
                if auto_create:
                    ingredient = Ingredient.objects.create(
                        inci_name=clean_name,
                        purpose='Unknown'
                    )
                    self.ingredients.add(ingredient)
                    matched.append(ingredient.inci_name)
                else:
                    not_found.append(clean_name)

        return {
            'matched': matched,
            'not_found': not_found
        }
