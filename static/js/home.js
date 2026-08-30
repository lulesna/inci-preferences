// przełącznik przykładowych profili w karcie demo
(function () {
    'use strict';

    var zakladki = [].slice.call(document.querySelectorAll('.demo-tab'));
    if (zakladki.length === 0) {
        return;
    }

    var profile = [].slice.call(document.querySelectorAll('.demo-profile'));

    function pokaz(nazwa) {
        zakladki.forEach(function (z) {
            var aktywna = z.dataset.profile === nazwa;
            z.classList.toggle('is-active', aktywna);
            z.setAttribute('aria-selected', aktywna ? 'true' : 'false');
        });
        profile.forEach(function (blok) {
            blok.hidden = blok.dataset.profile !== nazwa;
        });
    }

    zakladki.forEach(function (z) {
        z.addEventListener('click', function () {
            pokaz(z.dataset.profile);
        });
    });
})();

// rekomendacje na stronie głównej, tylko dla zalogowanych

(function () {
    'use strict';

    var lista = document.getElementById('recommendations-list');
    if (!lista) {
        return;
    }

    function zFormatowanaKategoria(tekst) {
        if (!tekst) {
            return '';
        }
        return tekst.charAt(0).toUpperCase() + tekst.slice(1).toLowerCase();
    }

    function akapit(tresc) {
        var p = document.createElement('p');
        p.className = 'recommendations-note';
        p.textContent = tresc;
        return p;
    }

    function pustaLista() {
        var p = akapit('No recommendations yet. ');
        var odnosnik = document.createElement('a');
        odnosnik.href = '/profile/';
        odnosnik.textContent = 'Mark a few ingredients';
        p.appendChild(odnosnik);
        p.appendChild(document.createTextNode(' and they will show up here.'));
        return p;
    }

    // budowane przez DOM, nie innerHTML - nazwy kosmetyków pochodzą od użytkowników
    function karta(kosmetyk) {
        var element = document.createElement('div');
        element.className = 'cosmetic-result-card safe';

        // liczba dopasowanych składników to jedyny powód, dla którego produkt
        // tu trafił, więc idzie na odznakę zamiast w kolejny wiersz danych
        var ile = typeof kosmetyk.safe_ingredients_count === 'number'
            ? kosmetyk.safe_ingredients_count : 0;
        var odznaka = document.createElement('span');
        odznaka.className = 'safety-badge';
        odznaka.textContent = ile + ' safe';
        odznaka.title = ile + ' ingredients you marked as safe';
        element.appendChild(odznaka);

        var tresc = document.createElement('div');
        tresc.className = 'card-content';

        var naglowek = document.createElement('h3');
        naglowek.textContent = kosmetyk.name || '';
        naglowek.title = kosmetyk.name || '';
        tresc.appendChild(naglowek);

        var marka = document.createElement('p');
        marka.className = 'card-brand';
        marka.textContent = kosmetyk.brand || '';
        tresc.appendChild(marka);

        var opis = [
            zFormatowanaKategoria(kosmetyk.main_category),
            zFormatowanaKategoria(kosmetyk.product_type || kosmetyk.subcategory || '')
        ].filter(Boolean).join(' · ');

        if (opis) {
            var kategoria = document.createElement('p');
            kategoria.className = 'card-category';
            kategoria.textContent = opis;
            tresc.appendChild(kategoria);
        }

        element.appendChild(tresc);

        var odnosnik = document.createElement('a');
        odnosnik.href = '/cosmetic/' + encodeURIComponent(kosmetyk.id) + '/';
        odnosnik.textContent = 'View details';
        element.appendChild(odnosnik);

        return element;
    }

    async function wczytaj() {
        try {
            var odpowiedz = await fetch('/api/cosmetics/recommended/');
            if (!odpowiedz.ok) {
                throw new Error('HTTP ' + odpowiedz.status);
            }

            var dane = await odpowiedz.json();
            lista.textContent = '';

            if (!dane.recommendations || dane.recommendations.length === 0) {
                lista.appendChild(pustaLista());
                return;
            }

            var siatka = document.createElement('div');
            siatka.className = 'cosmetics-grid';
            dane.recommendations.forEach(function (kosmetyk) {
                siatka.appendChild(karta(kosmetyk));
            });
            lista.appendChild(siatka);
        } catch (blad) {
            lista.textContent = '';
            lista.appendChild(akapit('Could not load recommendations. Try refreshing the page.'));
        }
    }

    wczytaj();
})();
