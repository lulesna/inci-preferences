(function () {
    'use strict';

    function setupPasswordToggles() {
        document.querySelectorAll('[data-toggle-password]').forEach(function (button) {
            var input = document.getElementById(button.dataset.togglePassword);
            if (!input) {
                return;
            }

            button.addEventListener('click', function () {
                var hidden = input.type === 'password';
                input.type = hidden ? 'text' : 'password';
                button.textContent = hidden ? 'Hide' : 'Show';
                button.setAttribute('aria-label', hidden ? 'Hide password' : 'Show password');
                input.focus();
            });
        });
    }

    function setupPasswordRules() {
        var dataElement = document.getElementById('password-rules-data');
        var input = document.querySelector('[data-password-rules-target]');

        if (!dataElement || !input) {
            return;
        }

        var list = document.getElementById(input.dataset.passwordRulesTarget);
        if (!list) {
            return;
        }

        var rules;
        try {
            rules = JSON.parse(dataElement.textContent);
        } catch (error) {
            return;
        }

        // \p{Ll} i \p{Lu} wymagają flagi 'u'
        var checks = rules.map(function (rule) {
            return {
                element: list.querySelector('[data-rule="' + rule.key + '"]'),
                regex: new RegExp(rule.pattern, 'u')
            };
        }).filter(function (check) {
            return check.element !== null;
        });

        function refresh() {
            var value = input.value;
            var started = value.length > 0;

            list.classList.toggle('is-active', started);

            checks.forEach(function (check) {
                var passed = started && check.regex.test(value);
                check.element.classList.toggle('is-met', passed);
            });
        }

        input.addEventListener('input', refresh);
        refresh();
    }

    // serwer zaznacza odrzucone pola klasą has-error; tutaj tylko aria-invalid
    // i gaszenie czerwieni przy poprawianiu, bo trzymanie jej do kolejnego
    // wysłania wygląda jak błąd nie do naprawienia
    function setupErrorClearing() {
        document.querySelectorAll('.form-group.has-error').forEach(function (group) {
            var fields = group.querySelectorAll('input');

            fields.forEach(function (field) {
                field.setAttribute('aria-invalid', 'true');
            });

            function clear() {
                group.classList.remove('has-error');
                fields.forEach(function (field) {
                    field.removeAttribute('aria-invalid');
                });
            }

            fields.forEach(function (field) {
                var zdarzenie = field.type === 'checkbox' ? 'change' : 'input';
                field.addEventListener(zdarzenie, clear, { once: true });
            });
        });
    }

    function init() {
        setupPasswordToggles();
        setupPasswordRules();
        setupErrorClearing();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
