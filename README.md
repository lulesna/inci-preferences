# INCI Preferences — Personalizowany Analizator Składów Kosmetycznych

![CI/CD Pipeline](https://github.com/lulesna/inci-preferences/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-6.0-green)
![PostgreSQL](https://img.shields.io/badge/postgresql-15-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-Academic-orange)

Pełnostackowa aplikacja webowa realizująca personalizowaną analizę składów kosmetyków w oparciu o indywidualne profile preferencji użytkowników. System wykorzystuje algorytmy dopasowania składników, OCR do rozpoznawania tekstu ze zdjęć oraz spersonalizowane algorytmy rekomendacji.

Projekt zrealizowany w ramach pracy licencjackiej na kierunku Informatyka, specjalność technologie sieciowe i bazy danych (Uniwersytet Gdański).

**Live demo:** [incipreferences.app](https://incipreferences.app/)

---

## Problem i motywacja

Popularne analizatory składów kosmetyków (CosDNA, INCI Beauty, INCI Decoder) stosują **statyczną, uniwersalną klasyfikację** składników, gdzie każda substancja otrzymuje jedną ocenę bezpieczeństwa, niezależnie od użytkownika. Takie podejście ignoruje kluczowy fakt: **reakcje skóry są indywidualne**.

Osoba z atopowym zapaleniem skóry może źle tolerować niacynamid (uznawany za bezpieczny), podczas gdy inna osoba bez problemu stosuje kwas salicylowy (zwykle oznaczany jako umiarkowany). Klasyfikacje uniwersalne nie odpowiadają rzeczywistości dermatologicznej.

**INCI Preferences** rozwiązuje ten problem, wprowadzając model **spersonalizowanej klasyfikacji składników** oraz algorytmy rekomendacji dopasowane do indywidualnego profilu użytkownika.

---

## Architektura systemu

Aplikacja została podzielona zgodnie z zasadą **Single Responsibility Principle** na cztery niezależne moduły Django:

```
apps/
├── ingredients/    - zarządzanie składnikami INCI (Ingredient model + REST API)
├── cosmetics/      - zarządzanie kosmetykami, parser, algorytmy dupes (Cosmetic model + ViewSet)
├── preferences/    - profile użytkowników, ulubione, algorytmy rekomendacji (UserProfile model)
└── users/          - autentykacja, rejestracja, zarządzanie kontem
```

Backend eksponuje **RESTful API** oparte na Django REST Framework z ViewSetami, custom actions oraz middleware do uwierzytelniania sesyjnego.

Frontend to **SPA-like aplikacja** wykorzystująca vanilla JavaScript z asynchronicznymi wywołaniami `fetch()` do API, dynamicznym renderowaniem DOM oraz komunikacją z backendem przez JSON.

---

## Funkcjonalności

### System kont użytkowników
- Rejestracja i logowanie oparte o Django Authentication
- Zarządzanie profilem: zmiana loginu, zmiana hasła z walidacją (PBKDF2 + SHA256), usuwanie konta
- Session-based authentication z CSRF Protection

### Personalizowana klasyfikacja składników
- Trójpoziomowa klasyfikacja (bezpieczne / umiarkowane / niebezpieczne) per użytkownik
- Interaktywne ustawianie preferencji przez kliknięcie w składnik
- **Automatyczna analiza wzorców** — algorytm wykrywa składniki występujące w ≥50% ulubionych produktów i sugeruje dodanie ich do preferencji

### Wyszukiwarka i zaawansowane filtrowanie
- Full-text search po nazwie kosmetyku i marce (Django `SearchFilter`)
- Kaskadowe filtrowanie po kategoriach (kategoria → podkategoria → typ produktu)
- Wielokrotne filtry składnikowe (must-contain, must-NOT-contain) z autocomplete
- Sortowanie wg bezpieczeństwa, alfabetycznie, wg liczby bezpiecznych składników

### Algorytm oceny bezpieczeństwa
Kosmetyki są klasyfikowane w czasie rzeczywistym poprzez porównanie ich składu z profilem użytkownika:

| Kolor | Warunek |
|-------|---------|
| 🟢 Zielony | Kosmetyk zawiera wyłącznie składniki neutralne lub oznaczone jako bezpieczne |
| 🟡 Żółty | Kosmetyk zawiera co najmniej jeden składnik oznaczony jako umiarkowany |
| 🔴 Czerwony | Kosmetyk zawiera co najmniej jeden składnik oznaczony jako niebezpieczny |

### Algorytmy rekomendacji i wyszukiwania zamienników
- **Top-N recommendations** — ranking bezpiecznych kosmetyków posortowanych wg liczby dopasowanych bezpiecznych składników
- **Dupes finder** — algorytm porównywania oparty na współczynniku Jaccarda (podobieństwo zbiorów), threshold 40%
- Sortowanie wyników wg similarity score

### Skanowanie składów ze zdjęć (OCR)
- Upload zdjęcia z drag & drop lub file picker
- Rozpoznawanie tekstu przez Tesseract.js (WebAssembly, on-device)
- Automatyczne czyszczenie i parsowanie tekstu (usuwanie markerów `Ingredients:`, `INCI:`, normalizacja białych znaków)
- Możliwość edycji rozpoznanego tekstu przed analizą
- Pełna analiza bezpieczeństwa z podziałem na kategorie

---

## Stack technologiczny

### Backend
| Technologia | Cel |
|------------|-----|
| **Python 3.12** | Język programowania |
| **Django 6.0** | Framework webowy (MTV) |
| **Django REST Framework** | RESTful API z ViewSetami |
| **PostgreSQL 15** | Relacyjna baza danych |
| **Gunicorn** | Production WSGI HTTP Server |
| **Whitenoise** | Serwowanie plików statycznych |
| **django-filter** | Zaawansowane filtrowanie API |
| **django-csp** | Content Security Policy |
| **psycopg2** | PostgreSQL adapter |
| **python-decouple** | Environment variables management |

### Frontend
| Technologia | Cel |
|------------|-----|
| **HTML5 / CSS3** | Struktura i stylowanie (Grid, Flexbox, Custom Properties) |
| **Vanilla JavaScript** | Interakcja z API, dynamiczne renderowanie DOM |
| **Tesseract.js** | OCR w przeglądarce (WebAssembly) |
| **Fetch API** | Asynchroniczne wywołania REST API |

### Infrastruktura i DevOps
| Technologia | Cel |
|------------|-----|
| **Docker** | Konteneryzacja aplikacji (multi-stage build, non-root user, healthcheck) |
| **Railway** | Platforma hostingowa (auto-deploy z GitHub) |
| **Supabase** | Managed PostgreSQL z connection poolingiem (port 6543) |
| **GitHub Actions** | CI/CD pipeline (testy, security scan, Docker build) |
| **Porkbun** | Rejestracja domeny + DNS management |
| **Cloudflare** | DNS, CDN, SSL |

### Testowanie i jakość kodu
| Technologia | Cel |
|------------|-----|
| **Django TestCase** | Testy jednostkowe i integracyjne |
| **DRF APIClient** | Testy REST API |
| **coverage.py** | Pomiar pokrycia kodu testami |
| **flake8** | Linter jakości kodu |
| **bandit** | Skanowanie bezpieczeństwa kodu |
| **safety** | Skanowanie zależności pod kątem CVE |

### Bezpieczeństwo
- Session-based authentication (Django Auth)
- CSRF Protection na wszystkich formularzach i żądaniach POST
- Password hashing: PBKDF2 z SHA256 (Django default)
- XSS prevention: HTML escaping w JavaScript, textContent zamiast innerHTML dla user-supplied data
- Content Security Policy (CSP) middleware
- HTTPS wymuszony w produkcji (Let's Encrypt via Cloudflare)
- Environment variables dla wszystkich danych wrażliwych
- Docker non-root user, minimal image size (--no-install-recommends)

---

## CI/CD Pipeline

Automatyczny pipeline uruchamiany przy każdym push oraz pull request na branch `main`:

1. **Test job** — uruchomienie testów Django z bazą PostgreSQL w kontenerze
2. **Security scan** — skanowanie zależności (safety) i kodu (bandit)
3. **Docker build test** — weryfikacja poprawności Dockerfile'a z cache warstw
4. **Deployment notification** — potwierdzenie sukcesu, trigger dla Railway auto-deploy

---

## Modele danych

### Kluczowe relacje

  - `User` (Django) 1:1 `UserProfile` (extended profile z preferencjami)
  - `UserProfile` M:N `Ingredient` (safe/moderate/unsafe — trzy niezależne relacje)
  - `UserProfile` M:N `Cosmetic` (favorites)
  - `Cosmetic` M:N `Ingredient` (skład produktu)
  - `Cosmetic` — hierarchiczne kategorie (main\_category → subcategory → product\_type)

-----

## Roadmap i możliwości rozwoju

Zaplanowane kierunki dalszego rozwoju:

  - **Integracja z LLM (OpenAI API / Claude API)** — inteligentny asystent kosmetyczny odpowiadający na pytania użytkowników
  - **Rozszerzone algorytmy rekomendacji** — collaborative filtering bazujący na preferencjach podobnych użytkowników
  - **Aplikacja mobilna** — React Native lub Flutter z natywnym OCR
  - **Rozszerzenie bazy składników** o dane z EWG Skin Deep i EU CosIng
  - **Push notifications** — alerty o nowych bezpiecznych produktach spełniających preferencje

-----

## Autorki

  - **Łucja Leśna** — architektura systemu, backend, deployment, testy |
    [GitHub](https://github.com/lulesna)
  - **Oliwia Natzke** — projekt UI/UX, frontend, koncepcja funkcjonalności | [GitHub](https://github.com/onatzke)

-----

## Licencja

Projekt akademicki. Wszelkie prawa zastrzeżone.
