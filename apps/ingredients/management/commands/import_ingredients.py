# uruchomienie: python manage.py import_ingredients
# format:
"""
inci_name,purpose
Aqua,Solvent
Glycerin,Humectant
Hyaluronic Acid,Humectant
Panthenol,Moisturizer
"""
import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.ingredients.models import Ingredient

DEFAULT_FILE_PATH = 'static/data/ingredients.csv'


class Command(BaseCommand):
    help = (
        'Import ingredients from a CSV file (columns: inci_name, purpose). '
        'Skips names that already exist, case-insensitively.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            nargs='?',
            default=DEFAULT_FILE_PATH,
            help=f'Path to the CSV file (default: {DEFAULT_FILE_PATH})',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                rows = list(csv.DictReader(file))
        except FileNotFoundError:
            raise CommandError(f'File not found: {file_path}')

        existing_names = {
            name.lower() for name in Ingredient.objects.values_list('inci_name', flat=True)
        }

        to_create = []
        seen_in_file = set()
        skipped = 0
        malformed = 0

        for row in rows:
            inci_name = (row.get('inci_name') or '').strip()
            purpose = (row.get('purpose') or '').strip()

            if not inci_name:
                malformed += 1
                continue

            key = inci_name.lower()
            if key in existing_names or key in seen_in_file:
                skipped += 1
                continue

            seen_in_file.add(key)
            to_create.append(Ingredient(inci_name=inci_name, purpose=purpose))

        with transaction.atomic():
            Ingredient.objects.bulk_create(to_create)

        message = f'Total: {len(to_create)} added, {skipped} skipped (duplicates)'
        if malformed:
            message += f', {malformed} skipped (missing inci_name)'
        self.stdout.write(self.style.SUCCESS(message))
