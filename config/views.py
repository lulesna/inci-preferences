from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def index(request):
    return render(request, 'index.html')

def categories(request):
    return render(request, 'categories.html')

def skincare(request):
    return render(request, 'categories/skincare.html')

def makeup(request):
    return render(request, 'categories/makeup.html')

def bodycare(request):
    return render(request, 'categories/bodycare.html')

def makeup_eyes(request):
    return render(request, 'categories/makeup/makeup_eyes.html')

def makeup_face(request):
    return render(request, 'categories/makeup/makeup_face.html')

def makeup_lips(request):
    return render(request, 'categories/makeup/makeup_lips.html')

def skincare_moisturizer(request):
    return render(request, 'categories/skincare/skincare_moisturizer.html')

def skincare_cleanser(request):
    return render(request, 'categories/skincare/skincare_cleanser.html')

def skincare_toner(request):
    return render(request, 'categories/skincare/skincare_toner.html')

def skincare_sunscreen(request):
    return render(request, 'categories/skincare/skincare_sunscreen.html')

def skincare_serum(request):
    return render(request, 'categories/skincare/skincare_serum.html')


def _choices_to_options(choices):
    return [{'value': value, 'label': label} for value, label in choices]


# kategorie z modelu, nie z kopii w szablonie — te dwie listy zdążyły się już
# rozjechać, formularz wysyłał 'BROWS' zamiast 'BROW_PENCIL'
def add_cosmetic(request):
    from apps.cosmetics.models import Cosmetic

    return render(request, 'addcosmetic.html', {
        'category_data': {
            'subcategories': {
                'FACE': _choices_to_options(Cosmetic.FACE_SUBCATEGORIES),
                'MAKEUP': _choices_to_options(Cosmetic.MAKEUP_SUBCATEGORIES),
                'BODY': [],
            },
            'productTypes': {
                'EYES': _choices_to_options(Cosmetic.MAKEUP_EYES_SUBCATEGORIES),
                'FACE': _choices_to_options(Cosmetic.MAKEUP_FACE_SUBCATEGORIES),
                'LIPS': _choices_to_options(Cosmetic.MAKEUP_LIPS_SUBCATEGORIES),
            },
        },
        'main_categories': _choices_to_options(Cosmetic.MAIN_CATEGORIES),
    })

def search(request):
    return render(request, 'search.html')

def cosmetic_detail(request, pk):
    return render(request, 'cosmetic_detail.html', {'cosmetic_id': pk})

# obie strony pokazują tylko dane zalogowanego, bez dekoratora anonim dostawał
# pustą stronę zamiast logowania
@login_required
def profile(request):
    return render(request, 'profile.html')


@login_required
def favorites(request):
    return render(request, 'favorites.html')
