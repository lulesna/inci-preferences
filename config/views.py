from django.shortcuts import render


def index(request):
    return render(request, 'index.html')

def categories(request):
    return render(request, 'categories.html')

def add_cosmetic(request):
    return render(request, 'addcosmetic.html')

def login_view(request):
    return render(request, 'login.html')
