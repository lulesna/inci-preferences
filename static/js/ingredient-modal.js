// Okno oceny składnika, wspólne dla strony produktu i skanera. Ustawia kolor
// w preferencjach użytkownika i przyjmuje zgłoszenie poprawki zastosowania.

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// DRF zwraca błędy walidacji pól jako {"pole": ["komunikat"]}, bez klucza
// "detail". Bez tego użytkownik dostawał ogólne "nie udało się" zamiast
// informacji, co dokładnie jest nie tak.
function extractApiError(data) {
    if (!data || typeof data !== 'object') return null;
    if (typeof data.detail === 'string') return data.detail;

    const first = Object.values(data)[0];
    if (Array.isArray(first) && first.length) return String(first[0]);
    if (typeof first === 'string') return first;
    return null;
}

const IngredientModal = (function () {
    let selected = null;
    let onChange = null;

    const modal = document.getElementById('ingredient-modal');
    const nameEl = document.getElementById('modal-ingredient-name');
    const purposeEl = document.getElementById('modal-ingredient-purpose');
    const proposeForm = document.getElementById('propose-form');
    const proposeField = document.getElementById('propose-purpose');
    const proposeSubmit = document.getElementById('propose-submit-btn');
    const proposeStatus = document.getElementById('propose-status');

    function setStatus(message, kind) {
        proposeStatus.textContent = message;
        proposeStatus.className = kind ? `propose-status ${kind}` : 'propose-status';
    }

    // Formularz zgłoszenia startuje zwinięty i wypełniony obecną wartością,
    // żeby użytkownik poprawiał tekst, a nie pisał go od zera.
    function resetProposeForm(purpose) {
        proposeField.value = purpose || '';
        proposeField.disabled = false;
        proposeForm.style.display = 'none';
        proposeSubmit.disabled = false;
        setStatus('');
    }

    // 'Unknown' wpisuje parser przy składniku spoza bazy, nie ma czego pokazywać
    function knownPurpose(purpose) {
        return purpose && purpose.trim().toLowerCase() !== 'unknown' ? purpose.trim() : '';
    }

    // oceniać da się tylko składnik z katalogu: preferencje i zgłoszenia
    // poprawek wiszą na jego id, nie na nazwie odczytanej ze zdjęcia
    function open(ingredient, currentColour) {
        if (!ingredient || !ingredient.id) return;

        selected = {
            id: ingredient.id,
            inci_name: ingredient.inci_name,
            purpose: ingredient.purpose || ''
        };

        nameEl.textContent = selected.inci_name;

        const purpose = knownPurpose(selected.purpose);
        purposeEl.textContent = purpose;
        purposeEl.style.display = purpose ? 'block' : 'none';

        // obecna ocena podświetlona, żeby było widać, że kliknięcie ją zmienia,
        // a nie ustawia od zera
        modal.querySelectorAll('.preference-btn').forEach(btn => {
            const isCurrent = !!currentColour && btn.classList.contains(currentColour);
            btn.classList.toggle('current', isCurrent);
            btn.querySelector('.preference-state').textContent = isCurrent ? 'Click to clear' : '';
        });

        resetProposeForm(purpose);
        modal.style.display = 'block';
    }

    function close() {
        modal.style.display = 'none';
        selected = null;
    }

    // klikniecie w juz zaznaczona ocene zdejmuje ja, zamiast ustawiac ten sam
    // kolor jeszcze raz. API przyjmuje 'NONE' i czysci wszystkie trzy listy
    async function setPreference(button) {
        if (!selected) return;

        const color = button.classList.contains('current') ? 'NONE' : button.dataset.color;

        try {
            const response = await fetch('/api/preferences/set_ingredient_color/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ingredient_id: selected.id, color: color})
            });

            if (!response.ok) {
                setStatus('Could not save your rating. Please try again.', 'error');
                return;
            }

            close();
            if (onChange) onChange();
        } catch (error) {
            setStatus('Network error. Please try again.', 'error');
        }
    }

    async function submitProposal() {
        if (!selected) return;

        const purpose = proposeField.value.trim();
        if (!purpose) {
            setStatus('Purpose cannot be empty.', 'error');
            return;
        }

        const csrfToken = getCookie('csrftoken');
        if (!csrfToken) {
            setStatus('Your session expired. Please reload the page and log in again.', 'error');
            return;
        }

        proposeSubmit.disabled = true;
        setStatus('Sending...');

        try {
            const response = await fetch(`/api/ingredients/${encodeURIComponent(selected.id)}/`, {
                method: 'PATCH',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({purpose: purpose})
            });

            // 202, nie 200: API przyjmuje zgłoszenie, ale katalogu jeszcze nie zmienia
            if (response.status === 202) {
                setStatus('Thanks! Your suggestion is waiting for admin review.', 'success');
                proposeField.disabled = true;
            } else {
                const data = await response.json().catch(() => ({}));
                setStatus(extractApiError(data) || 'Could not submit the suggestion.', 'error');
                proposeSubmit.disabled = false;
            }
        } catch (error) {
            setStatus('Network error. Please try again.', 'error');
            proposeSubmit.disabled = false;
        }
    }

    modal.querySelectorAll('[data-modal-close]').forEach(node => {
        node.addEventListener('click', close);
    });

    modal.querySelectorAll('.preference-btn').forEach(btn => {
        btn.addEventListener('click', () => setPreference(btn));
    });

    document.getElementById('propose-toggle').addEventListener('click', () => {
        const hidden = proposeForm.style.display === 'none';
        proposeForm.style.display = hidden ? 'block' : 'none';
        if (hidden) proposeField.focus();
    });

    proposeSubmit.addEventListener('click', submitProposal);

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.style.display === 'block') close();
    });

    return {
        init: function (options) {
            onChange = options && options.onChange;
        },
        open: open,
        close: close
    };
})();
