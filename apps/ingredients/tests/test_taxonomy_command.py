import io
import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from apps.ingredients.models import Ingredient


TAXONOMY = {
    'en:aqua': {
        'name': {'en': 'AQUA'},
        'inci_functions': {'en': 'en:solvent'},
        'cosing': {'en': '31959'},
    },
    'en:peg-100-stearate': {
        'name': {'en': 'PEG-100 STEARATE'},
        'inci_functions': {'en': 'en:emulsifying, en:surfactant'},
    },
    'en:caulerpa-racemosa-extract': {
        'name': {'en': 'CAULERPA RACEMOSA EXTRACT'},
        'inci_functions': {'en': 'en:astringent, en:hair-conditioning, en:skin-conditioning'},
    },
    'en:no-function': {
        'name': {'en': 'MYSTERY POWDER'},
    },
    'en:too-long': {
        'name': {'en': 'X' * 140},
        'inci_functions': {'en': 'en:emollient'},
    },
    'en:no-name': {
        'inci_functions': {'en': 'en:emollient'},
    },
}


class ImportInciTaxonomyTest(TestCase):

    def run_import(self, taxonomy=None, **options):
        path = Path(tempfile.mkdtemp()) / 'ingredients.json'
        with io.open(path, 'w', encoding='utf-8') as handle:
            json.dump(taxonomy if taxonomy is not None else TAXONOMY, handle)

        output = io.StringIO()
        call_command('import_inci_taxonomy', str(path), stdout=output, **options)
        return output.getvalue()

    def test_dry_run_writes_nothing(self):
        self.run_import()

        self.assertEqual(Ingredient.objects.count(), 0)

    def test_commit_creates_ingredients_with_purposes(self):
        self.run_import(commit=True)

        aqua = Ingredient.objects.get(inci_name='Aqua')
        self.assertEqual(aqua.purpose, 'Solvent')

    def test_multiple_functions_become_one_purpose(self):
        self.run_import(commit=True)

        extract = Ingredient.objects.get(inci_name='Caulerpa Racemosa Extract')
        self.assertEqual(extract.purpose, 'Astringent, Hair conditioning, Skin conditioning')

    def test_acronyms_and_numbers_keep_their_case(self):
        """'PEG-100 STEARATE' nie może wyjść jako 'Peg-100 Stearate'"""
        self.run_import(commit=True)

        self.assertTrue(Ingredient.objects.filter(inci_name='PEG-100 Stearate').exists())

    def test_name_longer_than_the_field_is_skipped(self):
        self.run_import(commit=True)

        self.assertFalse(Ingredient.objects.filter(inci_name__startswith='XXXX').exists())

    def test_entry_without_name_is_skipped(self):
        self.run_import(commit=True)

        self.assertEqual(Ingredient.objects.count(), 4)

    def test_existing_ingredient_is_not_duplicated(self):
        Ingredient.objects.create(inci_name='aqua', purpose='Rozpuszczalnik')

        self.run_import(commit=True)

        self.assertEqual(Ingredient.objects.filter(inci_name__iexact='aqua').count(), 1)
        self.assertEqual(Ingredient.objects.get(inci_name__iexact='aqua').purpose, 'Rozpuszczalnik')

    def test_only_with_function_skips_entries_without_one(self):
        self.run_import(commit=True, only_with_function=True)

        self.assertFalse(Ingredient.objects.filter(inci_name='Mystery Powder').exists())

    def test_csv_output_matches_import_ingredients_format(self):
        target = Path(tempfile.mkdtemp()) / 'slownik.csv'

        self.run_import(csv=str(target))

        content = io.open(target, encoding='utf-8').read()
        self.assertTrue(content.startswith('inci_name,purpose'))
        self.assertIn('Aqua,Solvent', content)
        self.assertEqual(Ingredient.objects.count(), 0)

    def test_limit_caps_the_number_of_rows(self):
        self.run_import(commit=True, limit=2)

        self.assertEqual(Ingredient.objects.count(), 2)
