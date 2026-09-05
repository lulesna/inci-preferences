# uruchomienie:
#   python manage.py import_cosmetics --api --report-unknown nowe.csv
#   python manage.py import_cosmetics --api --commit
#   python manage.py import_cosmetics openbeautyfacts-products.jsonl.gz --commit
#
# zrodlo: Open Beauty Facts, licencja ODbL
import csv
import gzip
import io
import json
import re
import time
from collections import Counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.cosmetics.models import Cosmetic
from apps.ingredients.models import Ingredient

# kategorie z Open Beauty Facts na taksonomie modelu. tagi wziete z
# https://world.openbeautyfacts.org/categories.json, czyli z tego, co w zrzucie
# naprawde wystepuje. kolejnosc ma znaczenie, bo produkt nosi kilka tagow naraz
# i wygrywa pierwszy trafiony, czyli najbardziej szczegolowy
CATEGORY_MAP = [
    ('en:mascara', ('MAKEUP', 'EYES', 'MASCARA')),
    ('en:eyes-makeup', ('MAKEUP', 'EYES', '')),
    ('en:lip-balms', ('MAKEUP', 'LIPS', 'LIP_BALM')),
    ('en:lipsticks', ('MAKEUP', 'LIPS', 'LIPSTICK')),
    ('en:lip-makeup', ('MAKEUP', 'LIPS', '')),
    ('en:lip-cosmetics', ('MAKEUP', 'LIPS', '')),
    ('en:face-makeup', ('MAKEUP', 'FACE', '')),

    ('en:sunscreen', ('FACE', 'SPF', '')),
    ('en:in-sun-protections', ('FACE', 'SPF', '')),
    ('en:cleansing-waters', ('FACE', 'CLEANSER', '')),
    ('en:cleansers', ('FACE', 'CLEANSER', '')),
    ('en:toners', ('FACE', 'TONER', '')),
    ('en:serums', ('FACE', 'SERUM', '')),
    ('en:anti-aging-face-care-products', ('FACE', 'MOISTURIZER', '')),
    ('en:facial-creams', ('FACE', 'MOISTURIZER', '')),

    ('en:hand-creams', ('BODY', '', '')),
    ('en:body-creams', ('BODY', '', '')),
    ('en:body-milks', ('BODY', '', '')),
    ('en:body-oils', ('BODY', '', '')),
    ('en:anti-dandruff-shampoos', ('BODY', '', '')),
    ('en:2-in-1-shampoos', ('BODY', '', '')),
    ('en:shampoos-shower-gels', ('BODY', '', '')),
    ('en:shampoos', ('BODY', '', '')),
    ('en:shampoo', ('BODY', '', '')),
    ('en:hair-conditioners', ('BODY', '', '')),
    ('en:hair-gel', ('BODY', '', '')),
    ('en:shower-gels', ('BODY', '', '')),
    ('en:showers-and-baths', ('BODY', '', '')),
    ('en:liquid-soaps', ('BODY', '', '')),
    ('en:bar-soaps', ('BODY', '', '')),
    ('en:soaps', ('BODY', '', '')),
    ('en:roll-on-deodorants', ('BODY', '', '')),
    ('en:deodorants', ('BODY', '', '')),

    # ogolniki na koniec, zeby nie przykryly kategorii szczegolowej
    ('en:makeup', ('MAKEUP', '', '')),
    ('en:face', ('FACE', '', '')),
    ('en:body', ('BODY', '', '')),
]

# zapowiedzi skladu na etykiecie, w kilku jezykach naraz
LIST_START = re.compile(
    r'(ingredients|ingr[eé]dients|ingredientes|inci|zutaten|composition|sk[lł]ad)\s*[:.\-]?\s*',
    re.IGNORECASE,
)

# i to, co juz skladem nie jest
LIST_END = re.compile(
    r'\b(made in|best before|f\.?i\.?l|net wt|www\.|batch|lot no)',
    re.IGNORECASE,
)


def clean_ingredients_text(text):
    cleaned = re.sub(r'\s+', ' ', str(text or '')).strip()

    start = LIST_START.search(cleaned)
    if start:
        cleaned = cleaned[start.end():].strip()

    end = LIST_END.search(cleaned)
    if end and end.start() > 0:
        cleaned = cleaned[:end.start()].strip()

    return cleaned.strip(' .,')


def split_names(text):
    # przecinek miedzy cyframi to czesc nazwy ('1,2-Hexanediol'), tak samo
    # jak w parserze modelu
    parts = re.split(r'(?<!\d),(?!\d)|[;•·]', text)

    names = []
    for part in parts:
        # 'AQUA / WATER' to jedna substancja pod dwiema nazwami, bierzemy
        # pierwsza. ukosnik bez spacji zostaje, bo siedzi w srodku nazwy
        # ('Caprylic/Capric Triglyceride')
        name = re.split(r'\s+/\s+', part.strip())[0]

        # nawias na etykiecie niesie druga nazwe tej samej substancji:
        # 'Aqua (Water)' albo 'Butyrospermum Parkii (Shea) Butter'
        name = re.sub(r'\([^)]*\)', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip(' .,*|')

        if len(name) < 3 or len(name) > 80:
            continue

        letters = len(re.findall(r'[A-Za-z]', name))
        if letters < 3 or letters < len(name.replace(' ', '')) / 2:
            continue

        names.append(name)

    return names


def normalise_name(name):
    # katalog trzyma nazwy zapisane 'Aqua', a zrzut czesto krzyczy 'AQUA'
    if name.isupper() or name.islower():
        return ' '.join(word.capitalize() if word.isalpha() else word for word in name.split())
    return name


def looks_latin(text):
    # w zrzucie sa nazwy greckie i cyrylica, w katalogu po angielsku wygladalyby
    # jak przypadkowe znaki
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False

    latin = sum(1 for char in letters if char.isascii() or char.lower() in 'ąćęłńóśźżäöüßéèêàçñ')
    return latin >= len(letters) * 0.8


def match_category(tags):
    tags = set(tags or [])
    for tag, mapped in CATEGORY_MAP:
        if tag in tags:
            return mapped
    return None


class Command(BaseCommand):
    help = (
        'Import cosmetics from an Open Beauty Facts JSONL dump. '
        'By default nothing is written to the database, pass --commit to save.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            nargs='?',
            help='Path to the .jsonl or .jsonl.gz dump (not needed with --api)',
        )
        parser.add_argument(
            '--api',
            action='store_true',
            help='Read products from the Open Beauty Facts API instead of a local dump',
        )
        parser.add_argument(
            '--category',
            action='append',
            help='Category tag to pull in --api mode, can be repeated',
        )
        parser.add_argument(
            '--pages',
            type=int,
            default=3,
            help='Pages of 100 products per category in --api mode (default 3)',
        )
        parser.add_argument(
            '--commit',
            action='store_true',
            help='Actually write to the database (without it the run is a dry run)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=500,
            help='How many products to import at most (default 500)',
        )
        parser.add_argument(
            '--min-known',
            type=float,
            default=0.8,
            help=(
                'Minimum share of ingredients already present in the catalogue, '
                'products below the threshold are skipped (default 0.8)'
            ),
        )
        parser.add_argument(
            '--create-ingredients',
            action='store_true',
            help='Also create catalogue entries for unknown ingredients (off by default)',
        )
        parser.add_argument(
            '--report-unknown',
            help='Write unknown ingredient names with their counts to this CSV file',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        min_known = options['min_known']
        commit = options['commit']

        if options['api']:
            categories = options['category'] or [tag for tag, _ in CATEGORY_MAP]
            records = self._records_from_api(categories, options['pages'])
        elif options['file_path']:
            records = self._records_from_file(options['file_path'])
        else:
            raise CommandError('Give a path to the dump or pass --api')

        known_ingredients = {
            name.lower() for name in Ingredient.objects.values_list('inci_name', flat=True)
        }
        existing_products = {
            (brand.strip().lower(), name.strip().lower())
            for name, brand in Cosmetic.objects.values_list('name', 'brand')
        }

        unknown_counter = Counter()
        stats = Counter()
        imported = 0

        for record in records:
            if imported >= limit:
                break

            stats['read'] += 1

            if record is None:
                stats['broken_json'] += 1
                continue

            name = (record.get('product_name_en') or record.get('product_name') or '').strip()
            brand = (record.get('brands') or '').split(',')[0].strip()
            raw_text = record.get('ingredients_text_en') or record.get('ingredients_text') or ''

            if not name or not brand:
                stats['no_name_or_brand'] += 1
                continue

            if len(name) > 100 or len(brand) > 100:
                stats['name_too_long'] += 1
                continue

            if not looks_latin(name):
                stats['other_alphabet'] += 1
                continue

            category = match_category(record.get('categories_tags'))
            if not category:
                stats['category_not_mapped'] += 1
                continue

            if (brand.lower(), name.lower()) in existing_products:
                stats['duplicate'] += 1
                continue

            names = [normalise_name(item) for item in split_names(clean_ingredients_text(raw_text))]
            if len(names) < 3:
                stats['no_ingredients'] += 1
                continue

            unknown = [item for item in names if item.lower() not in known_ingredients]
            known_ratio = 1 - len(unknown) / len(names)

            if known_ratio < min_known:
                stats['below_threshold'] += 1
                unknown_counter.update(unknown)
                continue

            unknown_counter.update(unknown)

            if commit:
                self._save(name, brand, category, names, options['create_ingredients'])

            existing_products.add((brand.lower(), name.lower()))
            imported += 1
            stats['imported'] += 1

        self._report(stats, imported, commit, unknown_counter, options.get('report_unknown'))

    def _records_from_file(self, path):
        try:
            stream = gzip.open(path, 'rt', encoding='utf-8') if path.endswith('.gz')                 else io.open(path, 'r', encoding='utf-8')
        except FileNotFoundError:
            raise CommandError(f'File not found: {path}')

        with stream:
            for line in stream:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    yield None

    # API zwraca po 100 produktow na strone. przerwa miedzy zapytaniami jest
    # celowa, bo to darmowy serwis spolecznosciowy, a nie hurtownia danych
    def _records_from_api(self, categories, pages):
        fields = ','.join([
            'code', 'product_name', 'product_name_en', 'brands',
            'categories_tags', 'ingredients_text', 'ingredients_text_en',
        ])

        for tag in categories:
            for page in range(1, pages + 1):
                query = urlencode({
                    'categories_tags': tag,
                    'fields': fields,
                    'page_size': 100,
                    'page': page,
                })
                url = f'https://world.openbeautyfacts.org/api/v2/search?{query}'
                request = Request(url, headers={
                    'User-Agent': 'INCIPreferences/1.0 (incipreferences.app, academic project)',
                })

                try:
                    with urlopen(request, timeout=60) as response:  # nosec B310
                        payload = json.load(response)
                except Exception as error:
                    self.stderr.write(f'{tag} strona {page}: {error}')
                    break

                products = payload.get('products') or []
                self.stdout.write(f'  {tag} strona {page}: {len(products)} produktow')

                for product in products:
                    yield product

                if len(products) < 100:
                    break

                time.sleep(1)

    def _save(self, name, brand, category, names, create_ingredients):
        main_category, subcategory, product_type = category

        # kazdy produkt osobno, zeby jeden zly rekord nie cofal calego przebiegu
        with transaction.atomic():
            cosmetic = Cosmetic.objects.create(
                name=name,
                brand=brand,
                main_category=main_category,
                subcategory=subcategory,
                product_type=product_type,
                ingredients_text=', '.join(names),
            )
            cosmetic.parse_and_add_ingredients(auto_create=create_ingredients)

    def _report(self, stats, imported, commit, unknown_counter, report_path):
        mode = 'ZAPISANE' if commit else 'PROBNY PRZEBIEG, nic nie zapisano'
        self.stdout.write(self.style.MIGRATE_HEADING(f'\n{mode}'))
        self.stdout.write(f'  wczytane linie:            {stats["read"]}')
        self.stdout.write(f'  zaimportowane produkty:    {imported}')
        self.stdout.write(f'  bez nazwy albo marki:      {stats["no_name_or_brand"]}')
        self.stdout.write(f'  nazwa dluzsza niz pole:    {stats["name_too_long"]}')
        self.stdout.write(f'  nazwa w innym alfabecie:   {stats["other_alphabet"]}')
        self.stdout.write(f'  kategoria bez mapowania:   {stats["category_not_mapped"]}')
        self.stdout.write(f'  juz w katalogu:            {stats["duplicate"]}')
        self.stdout.write(f'  sklad pusty albo krotki:   {stats["no_ingredients"]}')
        self.stdout.write(f'  ponizej progu znajomosci:  {stats["below_threshold"]}')
        self.stdout.write(f'  niepoprawny JSON:          {stats["broken_json"]}')

        if unknown_counter:
            self.stdout.write(self.style.WARNING(
                f'\n  skladniki spoza katalogu:  {len(unknown_counter)} roznych nazw'
            ))
            for name, count in unknown_counter.most_common(15):
                self.stdout.write(f'    {count:5d}  {name}')

        if report_path:
            with io.open(report_path, 'w', encoding='utf-8', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(['inci_name', 'purpose', 'wystapienia'])
                for name, count in unknown_counter.most_common():
                    writer.writerow([name, '', count])

            self.stdout.write(self.style.SUCCESS(
                f'\n  raport nieznanych skladnikow: {report_path}\n'
                f'  po uzupelnieniu kolumny purpose: python manage.py import_ingredients {report_path}'
            ))
