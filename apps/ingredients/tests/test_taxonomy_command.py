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
    'en:babassu': {
        'name': {'en': 'BABASSU OIL POLYGLYCERYL-4 ESTERS'},
        'inci_functions': {'en': 'en:emulsifying'},
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

        # piec nazw z szesciu wpisow, jeden jest bez nazwy, jeden za dlugi
        self.assertEqual(Ingredient.objects.count(), 5)

    def test_existing_ingredient_is_not_duplicated(self):
        Ingredient.objects.create(inci_name='aqua', purpose='Rozpuszczalnik')

        self.run_import(commit=True)

        self.assertEqual(Ingredient.objects.filter(inci_name__iexact='aqua').count(), 1)
        self.assertEqual(Ingredient.objects.get(inci_name__iexact='aqua').purpose, 'Rozpuszczalnik')

    def test_fill_purposes_replaces_the_parser_placeholder(self):
        """'Unknown' wpisuje parser skladu, to zapchajdziura, nie opis"""
        Ingredient.objects.create(inci_name='Aqua', purpose='Unknown')

        self.run_import(commit=True, fill_purposes=True)

        self.assertEqual(Ingredient.objects.get(inci_name='Aqua').purpose, 'Solvent')

    def test_fill_purposes_fills_an_empty_one(self):
        Ingredient.objects.create(inci_name='Aqua', purpose='')

        self.run_import(commit=True, fill_purposes=True)

        self.assertEqual(Ingredient.objects.get(inci_name='Aqua').purpose, 'Solvent')

    def test_fill_purposes_never_overwrites_a_real_description(self):
        Ingredient.objects.create(inci_name='Aqua', purpose='Rozpuszczalnik')

        self.run_import(commit=True, fill_purposes=True)

        self.assertEqual(Ingredient.objects.get(inci_name='Aqua').purpose, 'Rozpuszczalnik')

    def test_without_the_flag_existing_purposes_stay_untouched(self):
        Ingredient.objects.create(inci_name='Aqua', purpose='Unknown')

        self.run_import(commit=True)

        self.assertEqual(Ingredient.objects.get(inci_name='Aqua').purpose, 'Unknown')

    def test_fill_purposes_writes_nothing_in_a_dry_run(self):
        Ingredient.objects.create(inci_name='Aqua', purpose='Unknown')

        output = self.run_import(fill_purposes=True)

        self.assertEqual(Ingredient.objects.get(inci_name='Aqua').purpose, 'Unknown')
        self.assertIn('Aqua', output)

    def test_fix_names_repairs_capslock_after_a_hyphen(self):
        """'POLYGLYCERYL-4' w srodku nazwy to zostalosc po pierwszej wersji importu"""
        Ingredient.objects.create(
            inci_name='Babassu Oil POLYGLYCERYL-4 Esters', purpose='Emulsifying'
        )

        self.run_import(commit=True, fix_names=True)

        self.assertTrue(
            Ingredient.objects.filter(inci_name='Babassu Oil Polyglyceryl-4 Esters').exists()
        )
        self.assertEqual(Ingredient.objects.filter(inci_name__icontains='babassu').count(), 1)

    def test_fix_names_keeps_real_acronyms_upper(self):
        Ingredient.objects.create(inci_name='Peg-100 Stearate', purpose='Emulsifying')

        self.run_import(commit=True, fix_names=True)

        self.assertTrue(Ingredient.objects.filter(inci_name='PEG-100 Stearate').exists())

    def test_without_the_flag_names_stay_as_they_are(self):
        Ingredient.objects.create(inci_name='Babassu Oil POLYGLYCERYL-4 Esters', purpose='')

        self.run_import(commit=True)

        self.assertTrue(
            Ingredient.objects.filter(inci_name='Babassu Oil POLYGLYCERYL-4 Esters').exists()
        )

    def test_fix_names_writes_nothing_in_a_dry_run(self):
        Ingredient.objects.create(inci_name='Babassu Oil POLYGLYCERYL-4 Esters', purpose='')

        self.run_import(fix_names=True)

        self.assertTrue(
            Ingredient.objects.filter(inci_name='Babassu Oil POLYGLYCERYL-4 Esters').exists()
        )

    def test_fix_names_leaves_a_case_duplicate_alone(self):
        """dwa wpisy roznie zapisane zderzylyby sie z unikalnoscia nazwy"""
        Ingredient.objects.create(inci_name='AQUA', purpose='')
        Ingredient.objects.create(inci_name='Aqua', purpose='Solvent')

        self.run_import(commit=True, fix_names=True)

        self.assertEqual(Ingredient.objects.filter(inci_name__iexact='aqua').count(), 2)

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
