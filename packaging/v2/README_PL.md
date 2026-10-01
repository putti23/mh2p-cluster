# Cluster 2.0 — natywna mapa i turn-by-turn

Wydanie forka putti23, oparte na projekcie fifthBro. Bez naszych eksperymentów
AltScreen/111 i bez dodatkowej diagnostyki. Natywna mapa pozostaje na zegarach;
nie jest to mapa Apple/Google przeniesiona z telefonu.

- CarPlay i Android Auto nadal przekazują strzałki/dystans przez BAP.
- Usunięto odrzucanie dystansów od 20 000 m (np. 35 km).
- Renderowanie obrazu telefonu na zegarach zablokowane w obu klasach Javy.
  Stare ustawienie enableMapRender=true na USB/SD nie włączy go ponownie.
- Domyślny tekst ekranu logo: `(c) fifthBro v2.0`. Nie wymuszamy wyświetlania
  logo nad natywną mapą; znacznik zobaczysz, gdy wyświetlany jest ekran logo.
- Bazą przywracania jest 2.0. Kolejne zmiany: 2.1, 2.2 itd.; pliki 2.0 nie
  będą zastępowane nową zawartością pod tym samym numerem.

INSTALL i RESTORE instalują TEN SAM, przypięty sumami kontrolnymi zestaw 2.0.
RESTORE nie oznacza usunięcia całego modułu ani powrotu do fabrycznego firmware.
Nie używaj starego uninstall do przywracania 2.0.

## Instalacja po zakończeniu diagnostyki

1. Najpierw zbierz i wycofaj v0.18 jego własną kartą. Zrestartuj PCM bez karty.
2. Rozpakuj INSTALL na osobną/pustą kartę FAT32. Nie mieszaj jej z diagnostyką.
3. Instaluj na postoju przy stabilnym zasilaniu. Wyjmij kartę tylko na wyraźne
   „Please remove update media”, pozwól PCM zrestartować się bez karty.
4. Sprawdź CarPlay, strzałki/HUD, odcinek ponad 20 km oraz natywny obraz zegarów.

Instalator wymaga już działającego mh2p-cluster i czystych launcherów gal oraz
dio_manager. Odmawia nadpisania aktywnej diagnostyki lub nieznanej konfiguracji
launcherów. Zachowuje dotychczasowe pliki na karcie w Backup, nie zabija usług.
Zapisuje nienadpisywaną bazę 2.0 w /mnt/ota/modkit/cluster_baselines/2.0.
Trwający test v0.18 nie zna jeszcze tej bazy: jego przywracanie pozostaje bez zmian.

Paczka zawiera pełny standardowy cluster_config.json z mapRender=false; poprzedni
plik zostanie zachowany w Backup. Indywidualne ustawienia wymagają porównania.

## Sposób budowania i ograniczenia

Przypięta baza: upstream ClusterIntegration_v0034_beta2_candidate_90d0b76.zip.
Nie udajemy pełnej kompilacji z nieobecnym prywatnym SDK: skrypt zmienia JAR
instrukcjami o tej samej długości i efekcie stosu oraz jeden napis ELF, bez zmiany
rozmiaru/adresów. Odpowiedniki zmian są w źródłach. MANIFEST opisuje każde miejsce.
Nie zmieniamy kryptografii, bibliotek preload ani protokołu iAP2.
Testy poza autem nie gwarantują zgodności wszystkich ekranów/HUD ani przywrócenia
po utracie zasilania. To pierwsze wydanie 2.0, wymagające sprawdzenia w samochodzie.
