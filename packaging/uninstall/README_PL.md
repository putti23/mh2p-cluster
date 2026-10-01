# FULL UNINSTALL v1 — całkowite wyłączenie/usunięcie modułu cluster 2.0

To NIE jest RESTORE 2.0. Paczka usuwa aktywny moduł, także jego oryginalne
preloady fifthBro. Nie wykonuje się później drugiego odinstalowania oryginału.
Obsługuje znany zestaw 2.0/r2; przyszłe 2.1/2.2 wymagają ponownego sprawdzenia.

## Przed użyciem

- Zakończ diagnostykę, zbierz jej logi, przywróć 2.0 i zrestartuj PCM.
  Aktywne hooki diagnostyczne lub nieznane launchery powodują odmowę.
- Używaj wyłącznie na postoju, z pewnym zasilaniem i kopią karty.
- Na karcie ma być TYLKO mod `ClusterFullUninstall`. Nie dokładaj go do karty
  z instalatorem 2.0 lub diagnostyką. Ta paczka nie jest teraz zapisywana na D:.
- Uruchom przez dotychczasowy mechanizm ModKit. Stosuj się do komunikatów systemu
  o zakończeniu aktualizacji i usunięciu nośnika; nie przerywaj zapisu.

## Co robi

1. Sprawdza firmware, znane pliki, zapisane oryginały i własny statyczny program
   QNX porównujący dane. Nie używa systemowego `cmp`, tcpdump ani sieci.
2. Kopiuje wszystkie pliki objęte zmianą oraz zapisane oryginały na SD do
   `Backup/Cluster_FULL_UNINSTALL_<czas>_<numer>/`. Sprawdza każdą kopię.
3. Przywraca aktywne `gal` i `dio_manager` z lokalnych `*.real` — nie pobiera
   firmware z Internetu. Są to oryginały zachowane przez wcześniejszą instalację;
   to nie jest reinstalacja ani kryptograficzna atestacja fabrycznego firmware.
4. Usuwa znany JAR 2.0, program cluster, jego biblioteki, konfigurację i znaczniki
   oraz zweryfikowany autostart `ClusterIntegration/Persist/install.sh`.
5. Usuwa znane, nieaktywne pliki diagnostyki v19: bibliotekę oraz launcher `.v19.clean`.
   Nieznane aktywne mody odrzuca; nie usuwa niczego zbiorczo przez `rm -rf`.
6. Sprawdza przywrócone pliki i brak usuniętych komponentów. Przy błędzie podczas
   transakcji próbuje odtworzyć poprzedni stan z dziennika i kopii na SD.

**Sukces wyłącznie: `CLUSTER_FULL_UNINSTALL_RESULT=PASS_COMMITTED` w
`Logs/ClusterFullUninstall.log`.** Samo „Done installing” nie wystarcza.
Po zakończeniu potrzebny jest restart PCM. Skrypt nie zabija procesów.

## Co zostaje celowo

ModKit, inne mody, logi, nieaktywne archiwalne pozostałości starszych diagnostyk,
kopia bazowa 2.0 oraz fabryczne pliki `.real` zostają jako materiał do odzyskiwania.
Nie mają być aktywnym modułem clustera. Zachowaj również kopię na SD — zawiera
oryginały z Twojego urządzenia; nie publikuj jej na GitHubie.
Ponowne uruchomienie uninstallera jest obsługiwane przy zachowanych `.real`.
Ponowna instalacja clustera od zera to osobna procedura, nie ta paczka RESTORE 2.0,
która wymaga istniejącej instalacji.

Nie jest to usuwanie fabrycznej nawigacji ani fabrycznych funkcji CarPlay.
Znikną dodatkowe funkcje tego moda, w tym przekazywane przez niego turn-by-turn.
Testy hostowe nie zastępują testu na PCM. Nie gwarantujemy odzyskania po dowolnym
zaniku zasilania, uszkodzeniu pamięci lub utracie SD podczas zapisu.
