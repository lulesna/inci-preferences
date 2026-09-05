import io
import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from apps.cosmetics.models import Cosmetic
from apps.ingredients.models import Ingredient


def record(**overrides):
    data = {
        'product_name_en': 'Calm Barrier Cream',
        'brands': 'Meadow & Root, Meadow',
        'categories_tags': ['en:cosmetics', 'en:face', 'en:facial-creams'],
        'ingredients_text_en': 'INGREDIENTS: AQUA / WATER, GLYCERIN, PANTHENOL.',
    }
    data.update(overrides)
    return data


class ImportCosmeticsCommandTest(TestCase):

    def setUp(self):
        for name in ('Aqua', 'Glycerin', 'Panthenol'):
            Ingredient.objects.create(inci_name=name, purpose='Unknown')

    def run_import(self, records, **options):
        path = Path(tempfile.mkdtemp()) / 'dump.jsonl'
        with io.open(path, 'w', encoding='utf-8') as handle:
            for item in records:
                handle.write(json.dumps(item) + '\n')

        output = io.StringIO()
        call_command('import_cosmetics', str(path), stdout=output, **options)
        return output.getvalue()

    def test_dry_run_writes_nothing(self):
        self.run_import([record()])

        self.assertEqual(Cosmetic.objects.count(), 0)

    def test_commit_creates_cosmetic_with_mapped_category(self):
        self.run_import([record()], commit=True)

        cosmetic = Cosmetic.objects.get()
        self.assertEqual(cosmetic.name, 'Calm Barrier Cream')
        self.assertEqual(cosmetic.brand, 'Meadow & Root')
        self.assertEqual(cosmetic.main_category, 'FACE')
        self.assertEqual(cosmetic.subcategory, 'MOISTURIZER')

    def test_synonyms_and_case_are_normalised(self):
        """'AQUA / WATER' to jeden składnik pod dwiema nazwami, katalog trzyma pierwszą"""
        self.run_import([record()], commit=True)

        names = list(Cosmetic.objects.get().ingredients.values_list('inci_name', flat=True))
        self.assertCountEqual(names, ['Aqua', 'Glycerin', 'Panthenol'])
        self.assertEqual(Ingredient.objects.count(), 3)

    def test_unknown_ingredients_do_not_land_in_catalogue(self):
        """próg znajomości chroni katalog przed śmieciami z cudzego zrzutu"""
        self.run_import([record(
            ingredients_text_en='Aqua, Zzzqqq Extract, Wwwppp Powder, Kkklll Oil'
        )], commit=True)

        self.assertEqual(Cosmetic.objects.count(), 0)
        self.assertEqual(Ingredient.objects.count(), 3)

    def test_create_ingredients_flag_adds_them(self):
        """próg znajomości obowiązuje nadal, flaga pozwala tylko dopisać resztę"""
        self.run_import(
            [record(ingredients_text_en='Aqua, Glycerin, Panthenol, Squalane')],
            commit=True,
            create_ingredients=True,
            min_known=0.5,
        )

        self.assertTrue(Ingredient.objects.filter(inci_name__iexact='Squalane').exists())

    def test_parenthesis_synonym_is_stripped(self):
        """etykiety pisza 'Aqua (Water)', katalog trzyma sama nazwe INCI"""
        self.run_import([record(
            ingredients_text_en='Aqua (Water), Glycerin, Panthenol'
        )], commit=True)

        names = list(Cosmetic.objects.get().ingredients.values_list('inci_name', flat=True))
        self.assertCountEqual(names, ['Aqua', 'Glycerin', 'Panthenol'])

    def test_middle_parenthesis_is_removed_from_the_name(self):
        Ingredient.objects.create(inci_name='Butyrospermum Parkii Butter', purpose='Emollient')

        self.run_import([record(
            ingredients_text_en='Aqua, Glycerin, Butyrospermum Parkii (Shea) Butter'
        )], commit=True)

        names = list(Cosmetic.objects.get().ingredients.values_list('inci_name', flat=True))
        self.assertIn('Butyrospermum Parkii Butter', names)

    def test_product_named_in_another_alphabet_is_skipped(self):
        """grecka nazwa w angielskim katalogu wyglada jak przypadkowe znaki"""
        self.run_import([record(
            product_name_en='',
            product_name='ΕΝΥΔΑΤΙΚΗ ΚΡΕΜΑ ΣΕ ΜΟΡΦΗ ΤΖΕΛ',
        )], commit=True)

        self.assertEqual(Cosmetic.objects.count(), 0)

    def test_polish_name_is_kept(self):
        self.run_import([record(
            product_name_en='',
            product_name='Krem nawilżający do twarzy',
        )], commit=True)

        self.assertEqual(Cosmetic.objects.count(), 1)

    def test_middle_dot_separator_is_understood(self):
        self.run_import([record(
            ingredients_text_en='Aqua · Glycerin · Panthenol'
        )], commit=True)

        self.assertEqual(Cosmetic.objects.get().ingredients.count(), 3)

    def test_generic_tag_does_not_win_over_the_specific_one(self):
        self.run_import([record(
            categories_tags=['en:makeup', 'en:eyes-makeup', 'en:mascara']
        )], commit=True)

        cosmetic = Cosmetic.objects.get()
        self.assertEqual(cosmetic.main_category, 'MAKEUP')
        self.assertEqual(cosmetic.subcategory, 'EYES')
        self.assertEqual(cosmetic.product_type, 'MASCARA')

    def test_unmapped_category_is_skipped(self):
        self.run_import([record(categories_tags=['en:candles'])], commit=True)

        self.assertEqual(Cosmetic.objects.count(), 0)

    def test_duplicate_of_existing_product_is_skipped(self):
        Cosmetic.objects.create(
            name='Calm Barrier Cream',
            brand='Meadow & Root',
            main_category='FACE',
            subcategory='MOISTURIZER',
        )

        self.run_import([record()], commit=True)

        self.assertEqual(Cosmetic.objects.count(), 1)

    def test_duplicate_inside_the_dump_is_imported_once(self):
        self.run_import([record(), record()], commit=True)

        self.assertEqual(Cosmetic.objects.count(), 1)

    def test_limit_stops_the_import(self):
        records = [record(product_name_en=f'Cream {index}') for index in range(5)]

        self.run_import(records, commit=True, limit=2)

        self.assertEqual(Cosmetic.objects.count(), 2)

    def test_name_longer_than_the_field_is_skipped(self):
        self.run_import([record(product_name_en='x' * 120)], commit=True)

        self.assertEqual(Cosmetic.objects.count(), 0)

    def test_report_lists_unknown_names(self):
        report = Path(tempfile.mkdtemp()) / 'unknown.csv'

        self.run_import(
            [record(ingredients_text_en='Aqua, Glycerin, Panthenol, Squalane')],
            report_unknown=str(report),
        )

        content = io.open(report, encoding='utf-8').read()
        self.assertIn('inci_name,purpose,wystapienia', content)
        self.assertIn('Squalane', content)
