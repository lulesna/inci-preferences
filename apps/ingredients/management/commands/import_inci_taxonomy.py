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
    """taksonomia krzyczy 'AQUA', katalog trzyma 'Aqua'"""
    # 'ALCOHOL DENAT.' z kropka na koncu nie zlapie sie z etykieta, gdzie parser
    # kropke obcina
    raw = raw.strip().rstrip('.')

    words = []
    for word in raw.split():
        # o wielkosci liter decyduje pojedynczy czlon, nie cale slowo:
        # 'POLYGLYCERYL-4' to 'Polyglyceryl-4', ale 'PEG-100' zostaje wielkimi,
        # bo PEG to skrot. wczesniej kazde slowo z cyfra szlo capslockiem
        pieces = []
        for piece in re.split(r'([-/])', word):
            if piece in ('-', '/'):
                pieces.append(piece)
            elif piece.upper().strip('(),.') in ACRONYMS:
                pieces.append(piece.upper())
            elif not any(char.isalpha() for char in piece):
                pieces.append(piece)
            else:
                pieces.append(piece.capitalize())

        words.append(''.join(pieces))

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
            '--fill-purposes',
            action='store_true',
            help=(
                'Fill in the purpose of ingredients already in the catalogue that have '
                'none or say Unknown (a purpose set by a human is never overwritten)'
            ),
        )
        parser.add_argument(
            '--fix-names',
            action='store_true',
            help=(
                'Rewrite the spelling of names already in the catalogue to the tidied '
                'form, for example POLYGLYCERYL-4 to Polyglyceryl-4'
            ),
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

        # nazwa malymi literami -> (id, obecna nazwa, obecny opis), bo przy
        # --fill-purposes i --fix-names trzeba wiedziec, co juz w bazie stoi
        existing = {}
        duplicate_keys = set()
        for pk, name, purpose in Ingredient.objects.values_list('id', 'inci_name', 'purpose'):
            key = name.lower()
            if key in existing:
                duplicate_keys.add(key)
            existing[key] = (pk, name, purpose)

        rows = []
        to_fill = []
        to_rename = []
        rename_examples = []
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
                pk, current_name, current_purpose = existing[key]

                # 'Unknown' wpisuje parser skladu przy zakladaniu skladnika,
                # to zapchajdziura, a nie opis, wiec wolno ja nadpisac
                if options['fill_purposes'] and purpose:
                    if not current_purpose.strip() or current_purpose.strip().lower() == 'unknown':
                        to_fill.append(Ingredient(id=pk, purpose=purpose))

                # zmiana samej pisowni, wiec kolizja z unikalnoscia jest mozliwa
                # tylko wtedy, gdy katalog ma juz dwa wpisy roznie zapisane
                if options['fix_names'] and current_name != name and key not in duplicate_keys:
                    to_rename.append(Ingredient(id=pk, inci_name=name))
                    rename_examples.append((current_name, name))

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

        if options['commit'] and to_fill:
            with transaction.atomic():
                Ingredient.objects.bulk_update(to_fill, ['purpose'], batch_size=1000)

        if options['commit'] and to_rename:
            with transaction.atomic():
                Ingredient.objects.bulk_update(to_rename, ['inci_name'], batch_size=1000)

        mode = 'ZAPISANE' if options['commit'] else 'PROBNY PRZEBIEG, nic nie zapisano'
        self.stdout.write(self.style.MIGRATE_HEADING(f'\n{mode}'))
        self.stdout.write(f'  wpisy w taksonomii:        {len(taxonomy)}')
        self.stdout.write(f'  do dodania:                {len(rows)}')
        self.stdout.write(f'  z opisem zastosowania:     {sum(1 for _, p in rows if p)}')
        self.stdout.write(f'  juz w katalogu:            {skipped_existing}')
        self.stdout.write(f'  opisy do uzupelnienia:     {len(to_fill)}')
        self.stdout.write(f'  nazwy do poprawienia:      {len(to_rename)}')
        self.stdout.write(f'  bez nazwy:                 {skipped_no_name}')
        self.stdout.write(f'  nazwa dluzsza niz pole:    {skipped_too_long}')
        self.stdout.write(f'  bez funkcji (pominiete):   {skipped_no_function}')

        if options['csv']:
            self.stdout.write(self.style.SUCCESS(f'  plik CSV:                  {options["csv"]}'))

        if options['commit']:
            self.stdout.write(self.style.SUCCESS(f'  dodane do bazy:            {created}'))
            if to_fill:
                self.stdout.write(self.style.SUCCESS(f'  uzupelnione opisy:         {len(to_fill)}'))
            if to_rename:
                self.stdout.write(self.style.SUCCESS(f'  poprawione nazwy:          {len(to_rename)}'))
        elif to_rename:
            self.stdout.write('\n  przyklady poprawek nazw:')
            for before, after in rename_examples[:5]:
                self.stdout.write(f'    {before}  ->  {after}')

        elif to_fill:
            self.stdout.write('\n  opisy, ktore zostana uzupelnione:')
            for item in to_fill[:5]:
                name = Ingredient.objects.get(pk=item.pk).inci_name
                self.stdout.write(f'    {name}  ->  {item.purpose}')
        elif rows:
            self.stdout.write('\n  przyklady:')
            for name, purpose in rows[:5]:
                self.stdout.write(f'    {name}  ->  {purpose or "(brak funkcji)"}')
