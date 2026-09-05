// Podpowiedzi składników pobierane z serwera, po jednym zapytaniu na wpisaną
// frazę. Wcześniej profil i wyszukiwarka ściągały na starcie cały katalog przez
// fetchAllPages, co przy dwudziestu paru tysiącach składników oznaczało ponad
// czterysta zapytań na wejście i kończyło się odpowiedzią 429 z API.

async function searchIngredients(term, limit) {
    const phrase = String(term || '').trim();
    if (phrase.length < 2) return [];

    try {
        const response = await fetch(`/api/ingredients/?search=${encodeURIComponent(phrase)}`);
        if (!response.ok) return [];

        const data = await response.json();
        const results = Array.isArray(data) ? data : (data.results || []);

        return results.slice(0, limit || 10);
    } catch (error) {
        console.error('Ingredient search failed');
        return [];
    }
}

// Bez tego zapytanie leciałoby po każdym znaku, a przy szybkim pisaniu
// odpowiedzi wracały w innej kolejności niż poszły
function debounce(callback, delay) {
    let timer = null;

    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => callback.apply(this, args), delay || 250);
    };
}

// Podświetla w nazwie każde wystąpienie wpisanej frazy. Buduje węzły zamiast
// sklejać HTML, bo fraza pochodzi od użytkownika. Element to span, nie mark:
// mark ma domyślnie żółte tło przeglądarki i wychodziło ono za każdym razem,
// gdy arkusz nie zdążył się przeładować.
function highlightMatch(name, term) {
    const fragment = document.createDocumentFragment();
    const phrase = String(term || '').trim();

    if (!phrase) {
        fragment.appendChild(document.createTextNode(name));
        return fragment;
    }

    const haystack = name.toLowerCase();
    const needle = phrase.toLowerCase();

    let from = 0;
    let at = haystack.indexOf(needle, from);

    while (at !== -1) {
        if (at > from) {
            fragment.appendChild(document.createTextNode(name.slice(from, at)));
        }

        const marked = document.createElement('span');
        marked.className = 'suggestion-match';
        marked.textContent = name.slice(at, at + needle.length);
        fragment.appendChild(marked);

        from = at + needle.length;
        at = haystack.indexOf(needle, from);
    }

    if (from < name.length) {
        fragment.appendChild(document.createTextNode(name.slice(from)));
    }

    return fragment;
}
