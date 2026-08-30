// menu mobilne i rozwinięcie konta

(function () {
    'use strict';

    var hamburger = document.querySelector('.hamburger');
    var linki = document.getElementById('nav-links');

    if (hamburger && linki) {
        hamburger.addEventListener('click', function () {
            var otwarte = linki.classList.toggle('open');
            hamburger.classList.toggle('active', otwarte);
            hamburger.setAttribute('aria-expanded', otwarte ? 'true' : 'false');
        });
    }

    // <details> samo się nie zamyka po kliknięciu obok ani po Escape
    var konto = document.querySelector('.account-menu details');
    if (!konto) {
        return;
    }

    document.addEventListener('click', function (zdarzenie) {
        if (konto.open && !konto.contains(zdarzenie.target)) {
            konto.open = false;
        }
    });

    document.addEventListener('keydown', function (zdarzenie) {
        if (zdarzenie.key === 'Escape' && konto.open) {
            konto.open = false;
            konto.querySelector('summary').focus();
        }
    });
})();
