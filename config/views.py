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


def add_cosmetic(request):
    return render(request, 'addcosmetic.html')

def search(request):
    return render(request, 'search.html')

def cosmetic_detail(request, pk):
    return render(request, 'cosmetic_detail.html', {'cosmetic_id': pk})

def profile(request):
    return render(request, 'profile.html')

def favorites(request):
    return render(request, 'favorites.html')
