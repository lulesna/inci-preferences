# uruchomienie:
#   curl -O https://static.openbeautyfacts.org/data/taxonomies/ingredients.json
#   python manage.py import_inci_taxonomy ingredients.json --csv slownik.csv
#   python manage.py import_inci_taxonomy ingredients.json --commit
import csv
import io
import json
import re
from urllib.request import urlopen

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.ingredients.models import Ingredient

NAME_MAX_LENGTH = Ingredient._meta.get_field('inci_name').max_length
PURPOSE_MAX_LENGTH = Ingredient._meta.get_field('purpose').max_length

# skróty, które w nazwie INCI zostają wielkimi literami
ACRONYMS = {
    'PEG', 'PPG', 'PCA', 'PVP', 'PVM', 'MA', 'CI', 'SD', 'TEA', 'DEA', 'MEA',
    'EDTA', 'BHT', 'BHA', 'AHA', 'PHA', 'UV', 'MIT', 'CIT', 'HDI', 'IPDI',
    'TIPA', 'AMP', 'ATP', 'DNA', 'RNA', 'SH', 'HC', 'VP', 'VA', 'MSM',
}


def tidy_name(raw):
    raw = raw.strip().rstrip('.')

    words = []
    for word in raw.split():
        upper = word.upper()

        # segmenty z cyframi ('C20-40', 'PEG-100') i skroty zostaja jak byly
        if any(char.isdigit() for char in word) or upper.strip('-,()') in ACRONYMS:
            words.append(upper)
            continue

        words.append('-'.join(part.capitalize() for part in word.split('-')))

    return ' '.join(words)


def tidy_functions(raw):
    """'en:skin-conditioning, en:emollient' na 'Skin conditioning, Emollient'"""
    if not raw:
        return ''

    labels = []
    for item in raw.split(','):
        label = item.strip().removeprefix('en:').replace('-', ' ').strip()
        if label:
            labels.append(label.capitalize())

    purpose = ', '.join(labels)

    # pole ma limit, wiec ucinamy na calej funkcji, nie w polowie slowa
    while len(purpose) > PURPOSE_MAX_LENGTH and ',' in purpose:
        purpose = purpose.rsplit(',', 1)[0]

    return purpose[:PURPOSE_MAX_LENGTH]


class Command(BaseCommand):
    help = (
        'Import INCI names and their cosmetic functions from the Open Beauty Facts '
        'ingredients taxonomy (CosIng data). Nothing is written without --commit.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'source',
            help='Path to ingredients.json or a URL to download it from',
        )
        parser.add_argument(
            '--commit',
            action='store_true',
            help='Actually write to the database (without it the run is a dry run)',
        )
        parser.add_argument(
            '--csv',
            help='Write the result as an inci_name,purpose CSV instead of only counting',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Import at most this many ingredients',
        )
        parser.add_argument(
            '--only-with-function',
            action='store_true',
            help='Skip entries that have no declared cosmetic function',
        )

    def handle(self, *args, **options):
        source = options['source']

        try:
            if source.startswith(('http://', 'https://')):
                self.stdout.write(f'pobieranie {source}')
                with urlopen(source, timeout=120) as response:  # nosec B310
                    taxonomy = json.load(response)
            else:
                with io.open(source, encoding='utf-8') as handle:
                    taxonomy = json.load(handle)
        except FileNotFoundError:
            raise CommandError(f'File not found: {source}')
        except ValueError:
            raise CommandError('Source is not valid JSON')

        existing = {
            name.lower() for name in Ingredient.objects.values_list('inci_name', flat=True)
        }

        rows = []
        seen = set()
        skipped_no_name = 0
        skipped_too_long = 0
        skipped_no_function = 0
        skipped_existing = 0

        for entry in taxonomy.values():
            raw_name = (entry.get('name') or {}).get('en', '').strip()
            if not raw_name:
                skipped_no_name += 1
                continue

            purpose = tidy_functions((entry.get('inci_functions') or {}).get('en', ''))
            if options['only_with_function'] and not purpose:
                skipped_no_function += 1
                continue

            name = tidy_name(re.sub(r'\s+', ' ', raw_name))

            # 227 wpisow to opisy chemiczne dluzsze niz pole nazwy, nie nazwy handlowe
            if len(name) > NAME_MAX_LENGTH:
                skipped_too_long += 1
                continue

            key = name.lower()
            if key in seen:
                continue
            seen.add(key)

            if key in existing:
                skipped_existing += 1
                continue

            rows.append((name, purpose))

            if options['limit'] and len(rows) >= options['limit']:
                break

        if options['csv']:
            with io.open(options['csv'], 'w', encoding='utf-8', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(['inci_name', 'purpose'])
                writer.writerows(rows)

        created = 0
        if options['commit'] and rows:
            with transaction.atomic():
                # ignore_conflicts, bo unikalnosc inci_name jest wrazliwa na
                # wielkosc liter, a katalog moze juz miec 'aqua' obok 'Aqua'
                Ingredient.objects.bulk_create(
                    [Ingredient(inci_name=name, purpose=purpose) for name, purpose in rows],
                    batch_size=1000,
                    ignore_conflicts=True,
                )
            created = Ingredient.objects.count() - len(existing)

        mode = 'ZAPISANE' if options['commit'] else 'PROBNY PRZEBIEG, nic nie zapisano'
        self.stdout.write(self.style.MIGRATE_HEADING(f'\n{mode}'))
        self.stdout.write(f'  wpisy w taksonomii:        {len(taxonomy)}')
        self.stdout.write(f'  do dodania:                {len(rows)}')
        self.stdout.write(f'  z opisem zastosowania:     {sum(1 for _, p in rows if p)}')
        self.stdout.write(f'  juz w katalogu:            {skipped_existing}')
        self.stdout.write(f'  bez nazwy:                 {skipped_no_name}')
        self.stdout.write(f'  nazwa dluzsza niz pole:    {skipped_too_long}')
        self.stdout.write(f'  bez funkcji (pominiete):   {skipped_no_function}')

        if options['csv']:
            self.stdout.write(self.style.SUCCESS(f'  plik CSV:                  {options["csv"]}'))

        if options['commit']:
            self.stdout.write(self.style.SUCCESS(f'  dodane do bazy:            {created}'))
        elif rows:
            self.stdout.write('\n  przyklady:')
            for name, purpose in rows[:5]:
                self.stdout.write(f'    {name}  ->  {purpose or "(brak funkcji)"}')
