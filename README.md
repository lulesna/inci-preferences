# Analizator Składów Kosmetyków - INCI Preferences
   ![CI/CD Pipeline](https://github.com/lulesna/analizator-skladow-kosmetykow/actions/workflows/ci.yml/badge.svg)
   ![Docker](https://img.shields.io/badge/docker-ready-blue)
   ![Kubernetes](https://img.shields.io/badge/kubernetes-yes-blue)

Aplikacja webowa do analizy składów kosmetyków oparta na indywidualnych preferencjach użytkownika. W przeciwieństwie do popularnych analizatorów składów, które klasyfikują substancje w sposób uniwersalny, INCI Preferences pozwala każdemu użytkownikowi samodzielnie określić, które składniki toleruje, a których powinien unikać.

Projekt powstał w ramach seminarium licencjackiego.

## Motywacja za projektem

Skóra każdego człowieka reaguje inaczej na te same składniki kosmetyczne. Osoba z atopowym zapaleniem skóry może źle tolerować substancje powszechnie uznawane za bezpieczne, podczas gdy inne osoby nie mają z nimi żadnych problemów. Standardowe analizatory składów oceniają substancje w sposób uogólniony, co nie odpowiada rzeczywistym potrzebom osób z wrażliwą skórą, alergiami czy chorobami dermatologicznymi.

INCI Preferences rozwiązuje ten problem, umożliwiając tworzenie spersonalizowanych profili preferencji, które są następnie wykorzystywane do oceny bezpieczeństwa produktów i generowania rekomendacji.

## Funkcjonalności

### System kont użytkowników
- Rejestracja i logowanie (unikalny login + hasło)
- Zarządzanie profilem: zmiana loginu, hasła, usuwanie konta

### Zarządzanie preferencjami składników
- Trójpoziomowa klasyfikacja składników (bezpieczne / umiarkowane / niebezpieczne)
- Szybkie ustawianie preferencji przez kliknięcie w składnik na stronie produktu
- Analiza ulubionych kosmetyków - automatyczne wykrywanie często występujących składników z sugestiami dodania ich do preferencji

### Przeglądanie i wyszukiwanie
- Wyszukiwanie kosmetyków po nazwie lub marce
- Zaawansowane filtrowanie (kaskadowe kategorie, składniki must-contain/must-not-contain, sortowanie, filtrowanie po bezpieczeństwie)
- Hierarchiczna nawigacja po kategoriach produktów
- Wyświetlanie pełnego składu INCI z kolorowymi tagami zgodnie z preferencjami

### System oceny bezpieczeństwa
Kosmetyki są automatycznie oznaczane kolorem na podstawie preferencji użytkownika:
- **Zielony** - produkt nie zawiera składników umiarkowanych ani niebezpiecznych
- **Pomarańczowy** - produkt zawiera co najmniej jeden składnik umiarkowany
- **Czerwony** - produkt zawiera co najmniej jeden składnik niebezpieczny

### Rekomendacje i wyszukiwanie zamienników
- Spersonalizowany system rekomendacji - top 10 produktów bez składników niebezpiecznych i umiarkowanych
- Wyszukiwanie zamienników (dupes) - algorytm porównywania składów z progiem podobieństwa 40%

### Dodatkowe funkcje
- Ulubione kosmetyki z dedykowaną zakładką
- Dodawanie nowych kosmetyków przez wklejenie danych ze sklepu internetowego
- Skanowanie składu ze zdjęcia (OCR) z możliwością edycji rozpoznanego tekstu i pełną analizą bezpieczeństwa

## Technologie

### Backend
- **Python 3.12**
- **Django 6.0** - framework webowy
- **Django REST Framework** - budowa RESTful API
- **PostgreSQL** - relacyjna baza danych
- **Gunicorn** - production-ready WSGI HTTP Server
- **Whitenoise** - serwowanie plików statycznych w produkcji
- **psycopg2** - PostgreSQL adapter dla Pythona
- **python-decouple** - zarządzanie zmiennymi środowiskowymi
- **django-filter** - zaawansowane filtrowanie w API

### Frontend
- **HTML5** i **CSS3** - struktura i stylowanie (CSS Grid, Flexbox, Custom Properties)
- **Vanilla JavaScript** - bez frameworków dla lepszej wydajności
- **Tesseract.js** - biblioteka OCR do skanowania składów ze zdjęć

### Infrastruktura
- **Supabase** - hosting bazy PostgreSQL z connection poolingiem
- **Railway** - platforma hostingowa dla aplikacji
- **Git & GitHub** - kontrola wersji i CI/CD

### Bezpieczeństwo
- Session-based authentication
- CSRF Protection
- Hashowanie haseł algorytmem PBKDF2 z SHA256
- Zmienne środowiskowe dla danych wrażliwych

## Struktura projektu

Aplikacja została podzielona na cztery moduły Django zgodnie z zasadą Single Responsibility Principle:

- **ingredients** - zarządzanie składnikami INCI
- **cosmetics** - zarządzanie produktami kosmetycznymi
- **preferences** - preferencje użytkowników i ulubione produkty
- **users** - rejestracja, logowanie, zarządzanie kontem

## Demo

Aplikacja dostępna online: [incipreferences.app](https://incipreferences.app/)

## Autorki

- **Łucja Leśna** - [GitHub](https://github.com/lulesna)
- **Oliwia Natzke** - [GitHub](https://github.com/onatzke)

## Licencja

Projekt akademicki. Wszelkie prawa zastrzeżone.
