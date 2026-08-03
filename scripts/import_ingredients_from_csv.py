import csv
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.ingredients.models import Ingredient

FILE_PATH = 'static/data/ingredients.csv'

def import_ingredients_from_csv(FILE_PATH):
    added = 0
    skipped = 0

    with open(FILE_PATH, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            inci_name = row['inci_name']
            purpose = row['purpose']

            if Ingredient.objects.filter(inci_name=inci_name).exists():
                skipped += 1
            else:
                Ingredient.objects.create(
                    inci_name=inci_name,
                    purpose=purpose
                )
                added += 1

    print(f'Total: {added} added, {skipped} skipped')


if __name__ == '__main__':
    import_ingredients_from_csv(FILE_PATH)
