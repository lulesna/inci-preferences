(function () {
    'use strict';

    var form = document.getElementById('add-cosmetic-form');
    if (!form) {
        return;
    }

    var dane = JSON.parse(document.getElementById('category-data').textContent);
    var subcategories = dane.subcategories;
    var productTypes = dane.productTypes;

    var pola = {
        name: document.getElementById('name'),
        brand: document.getElementById('brand'),
        main_category: document.getElementById('main_category'),
        subcategory: document.getElementById('subcategory'),
        product_type: document.getElementById('product_type'),
        ingredients_text: document.getElementById('ingredients_text')
    };

    // nazwy pól z API na etykiety dla użytkownika
    var ETYKIETY = {
        name: 'Product name',
        brand: 'Brand',
        main_category: 'Main category',
        subcategory: 'Subcategory',
        product_type: 'Product type',
        ingredients_text: 'Ingredients'
    };

    var przycisk = form.querySelector('button[type="submit"]');
    var komunikat = document.getElementById('result-message');

    function grupaPola(nazwa) {
        return pola[nazwa] ? pola[nazwa].closest('.form-group') : null;
    }

    function pokazBlad(nazwa, tresc) {
        var grupa = grupaPola(nazwa);
        if (!grupa) {
            return false;
        }

        grupa.classList.add('has-error');
        pola[nazwa].setAttribute('aria-invalid', 'true');

        var akapit = grupa.querySelector('.field-error');
        if (!akapit) {
            akapit = document.createElement('p');
            akapit.className = 'field-error';
            grupa.appendChild(akapit);
        }
        akapit.textContent = tresc;
        return true;
    }

    function wyczyscBledy() {
        form.querySelectorAll('.form-group.has-error').forEach(function (grupa) {
            grupa.classList.remove('has-error');
            var pole = grupa.querySelector('input, select, textarea');
            if (pole) {
                pole.removeAttribute('aria-invalid');
            }
            var akapit = grupa.querySelector('.field-error');
            if (akapit) {
                akapit.remove();
            }
        });
        komunikat.textContent = '';
        komunikat.className = '';
    }

    // czerwień gaśnie, gdy użytkownik zaczyna poprawiać dane
    Object.keys(pola).forEach(function (nazwa) {
        var pole = pola[nazwa];
        if (!pole) {
            return;
        }
        var zdarzenie = pole.tagName === 'SELECT' ? 'change' : 'input';
        pole.addEventListener(zdarzenie, function () {
            var grupa = pole.closest('.form-group');
            if (grupa && grupa.classList.contains('has-error')) {
                grupa.classList.remove('has-error');
                pole.removeAttribute('aria-invalid');
                var akapit = grupa.querySelector('.field-error');
                if (akapit) {
                    akapit.remove();
                }
            }
        });
    });

    function pokazKomunikat(tresc, rodzaj) {
        komunikat.textContent = tresc;
        komunikat.className = 'alert alert-' + rodzaj;
    }

    function wypelnijSelect(select, opcje, tekstDomyslny) {
        select.innerHTML = '';
        var domyslna = document.createElement('option');
        domyslna.value = '';
        domyslna.textContent = tekstDomyslny;
        select.appendChild(domyslna);

        opcje.forEach(function (opcja) {
            var element = document.createElement('option');
            element.value = opcja.value;
            element.textContent = opcja.label;
            select.appendChild(element);
        });
    }

    pola.main_category.addEventListener('change', function () {
        var wybrana = this.value;
        var listaPod = subcategories[wybrana] || [];

        document.getElementById('product-type-container').hidden = true;
        pola.product_type.value = '';

        if (listaPod.length > 0) {
            wypelnijSelect(pola.subcategory, listaPod, 'Select subcategory');
            document.getElementById('subcategory-container').hidden = false;
        } else {
            pola.subcategory.value = '';
            document.getElementById('subcategory-container').hidden = true;
        }
    });

    pola.subcategory.addEventListener('change', function () {
        var listaTypow = productTypes[this.value] || [];

        if (listaTypow.length > 0) {
            wypelnijSelect(pola.product_type, listaTypow, 'Select product type');
            document.getElementById('product-type-container').hidden = false;
        } else {
            pola.product_type.value = '';
            document.getElementById('product-type-container').hidden = true;
        }
    });

    // musi liczyć tak samo jak parser w apps/cosmetics/models.py, inaczej
    // licznik obiecywałby co innego, niż trafi do bazy. znak po znaku, bo
    // Safari obsługuje lookbehind dopiero od 16.4
    function policzSkladniki(tekst) {
        if (!tekst.trim()) {
            return 0;
        }

        var pozycje = [];
        var biezaca = '';

        for (var i = 0; i < tekst.length; i++) {
            var znak = tekst[i];
            var miedzyCyframi = znak === ',' &&
                /[0-9]/.test(tekst[i - 1] || '') &&
                /[0-9]/.test(tekst[i + 1] || '');

            if (znak === ',' && !miedzyCyframi) {
                pozycje.push(biezaca);
                biezaca = '';
            } else {
                biezaca += znak;
            }
        }
        pozycje.push(biezaca);

        return pozycje.filter(function (czesc) {
            return czesc.trim().replace(/\.+$/, '').length > 0;
        }).length;
    }

    var licznik = document.getElementById('ingredient-count');

    function odswiezLicznik() {
        var tekst = pola.ingredients_text.value;
        var ile = policzSkladniki(tekst);

        if (!tekst.trim()) {
            licznik.textContent = '';
            licznik.className = 'field-hint';
            return;
        }

        licznik.textContent = ile === 1
            ? '1 ingredient detected — if you pasted a full list, check that entries are separated by commas'
            : ile + ' ingredients detected';
        licznik.className = ile === 1 ? 'field-hint ingredient-count-warning' : 'field-hint';
    }

    pola.ingredients_text.addEventListener('input', odswiezLicznik);
    odswiezLicznik();

    function getCookie(name) {
        var wartosc = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(function (surowe) {
                var cookie = surowe.trim();
                if (cookie.substring(0, name.length + 1) === name + '=') {
                    wartosc = decodeURIComponent(cookie.substring(name.length + 1));
                }
            });
        }
        return wartosc;
    }

    function zbierzDane() {
        return {
            name: pola.name.value.trim(),
            brand: pola.brand.value.trim(),
            main_category: pola.main_category.value,
            subcategory: pola.subcategory.value || '',
            product_type: pola.product_type.value || '',
            ingredients_text: pola.ingredients_text.value.trim()
        };
    }

    function sprawdzLokalnie(dane) {
        var brakujace = [];

        ['name', 'brand', 'main_category', 'ingredients_text'].forEach(function (nazwa) {
            if (!dane[nazwa]) {
                pokazBlad(nazwa, ETYKIETY[nazwa] + ' is required.');
                brakujace.push(nazwa);
            }
        });

        return brakujace;
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        wyczyscBledy();

        var dane = zbierzDane();
        var brakujace = sprawdzLokalnie(dane);

        if (brakujace.length > 0) {
            // kursor w pierwszym problematycznym polu, żeby nie szukać go
            // wzrokiem w długim formularzu
            pola[brakujace[0]].focus();
            pola[brakujace[0]].scrollIntoView({ block: 'center', behavior: 'smooth' });
            return;
        }

        przycisk.disabled = true;
        var etykietaPrzycisku = przycisk.textContent;
        przycisk.textContent = 'Adding…';

        try {
            var odpowiedz = await fetch('/api/cosmetics/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(dane)
            });

            if (odpowiedz.ok) {
                var utworzony = await odpowiedz.json();
                pokazKomunikat('Cosmetic added. Opening it now…', 'success');

                if (typeof utworzony.id === 'number' && utworzony.id > 0) {
                    window.location.href = '/cosmetic/' + encodeURIComponent(utworzony.id) + '/';
                    return;
                }

                form.reset();
                document.getElementById('subcategory-container').hidden = true;
                document.getElementById('product-type-container').hidden = true;
                odswiezLicznik();
            } else {
                var bledy = await odpowiedz.json().catch(function () { return null; });
                var pozostale = [];

                if (bledy && typeof bledy === 'object') {
                    Object.keys(bledy).forEach(function (poleApi) {
                        var tresc = [].concat(bledy[poleApi]).join(' ');
                        if (!pokazBlad(poleApi, tresc)) {
                            pozostale.push((ETYKIETY[poleApi] || poleApi) + ': ' + tresc);
                        }
                    });
                }

                if (pozostale.length > 0) {
                    pokazKomunikat(pozostale.join(' '), 'error');
                } else if (!bledy) {
                    pokazKomunikat('Could not add the cosmetic. Please try again.', 'error');
                }

                var pierwszyBlad = form.querySelector('.form-group.has-error');
                if (pierwszyBlad) {
                    pierwszyBlad.scrollIntoView({ block: 'center', behavior: 'smooth' });
                }
            }
        } catch (blad) {
            pokazKomunikat('Could not reach the server. Check your connection and try again.', 'error');
        } finally {
            przycisk.disabled = false;
            przycisk.textContent = etykietaPrzycisku;
        }
    });
})();
