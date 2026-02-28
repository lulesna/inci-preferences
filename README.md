# Analizator Składów Kosmetyków (Seminarium licencjackie)
**Autorki:** Łucja Leśna i Oliwia Natzke

**Opis projektu:** Aplikacja webowa pozwalająca analizować składy kosmetyków zwracając szczególną uwagę na preferencje użytkownika (preferencje, alergie, nietolerancje...). W odróżnieniu od wielu funkcjonujących już analizatorów składów kosmetyków, aplikacja nie określa, czy składnik jest zły czy dobry dla użytkownika, tylko użytkownik sam musi zaznaczyć, które składniki akceptuje, których woli unikać, a których absolutnie nie toleruje.

**Aktualne funkcjonalności aplikacji:**
- rejestracja i logowanie (unikalny login + hasło)
- wyszukiwanie kosmetyku po nazwie lub marce
- przeglądanie kategorii kosmetyków
- edycja profilu: zmiana loginu, usunięcie konta, dodanie/zmiania/usunięcie preferencji odnośnie składników
- wyświetlanie kosmetyku z podstawowymi informacjami
- zakładka z ulubionymi kosmetykami
- podświetlanie kosmetyku na dany kolor w zależności od preferencji użytkownika: 
  - na zielono - nie ma żadnych składników pomarańczowych ani czerwonych
  - na pomarańczowo - znajduje się 1 lub więcej składników pomarańczowych, ale nie ma składników czerwonych
  - na czerwono - znajduje się przynajmniej 1 składnik czerwony
- podświetlanie składnika na dany kolor w zależności od preferencji użytkownika: 
  - na zielono - składnik, który użytkownik na pewno toleruje i być może preferuje
  - na pomarańczowo - składnik, którego użytkownik wolałby uniknąć
  - na czerwono - składnik, którego użytkownik nie toleruje, np. ma uczulenie na niego
- dodawanie kosmetyku - wystarczy skopiować informacje z dowolnego sklepu internetowego

należy zainstalować potrzebne paczki! `pip install -r requirements.txt`
