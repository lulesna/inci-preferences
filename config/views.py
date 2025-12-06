from django.shortcuts import render


def index(request):
    return render(request, 'index.html')

def categories(request):
    return render(request, 'categories.html')

def skincare(request):
    return render(request, 'skincare.html')

def makeup(request):
    return render(request, 'makeup.html')

def bodycare(request):
    return render(request, 'bodycare.html')

def add_cosmetic(request):
    return render(request, 'addcosmetic.html')

def login_view(request):
    return render(request, 'users/login.html')
