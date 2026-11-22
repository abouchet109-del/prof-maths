# Anki du PC secondaire : état du 21/11/2026

**Pour synchroniser, l'Anki du PC principal est la référence.** La session Anki faite sur le PC secondaire le 21/11 est de qualité moyenne : ces fichiers servent seulement à retrouver ce qu'elle contient, si besoin.

## Ce qui a été fait sur le PC secondaire le 21/11
- Avant ces changements, son Anki s'est synchronisé avec AnkiWeb à 14h19. Il lui manquait alors 507 cartes : les imports du 18/11 au soir n'avaient pas été envoyés depuis le PC principal.
- Les 507 cartes ont été régénérées depuis `matieres/*/cartes.yaml` (`anki.py --reexporter`), avec les mêmes GUID, puis importées. `registre.csv` n'a pas été modifié.
- 18 doublons du retri du 18/11 (`state/tri_anciennes.yaml`) ont été suspendus.
- L'Anki a ensuite été synchronisé avec AnkiWeb.

## Sur le PC principal
1. Synchroniser en forçant l'envoi : Préférences → Synchronisation → « Forcer les changements dans un sens » → **Envoyer vers AnkiWeb**. Il a déjà les 507 cartes et le retri, donc rien de structurel n'est perdu. Ne pas faire de synchro normale avant : les 507 cartes ont des identifiants de note différents sur chaque PC, et une fusion les dédoublerait.
2. Sur le PC secondaire, faire ensuite **Télécharger depuis AnkiWeb**.
3. Seules les révisions du 21/11 faites sur le PC secondaire seront perdues. Elles sont ici, pour les refaire ou les reporter à la main si besoin.

## Fichiers
- `2026-11-21-revisions.csv` : chaque révision du 21/11 (259 révisions sur 224 cartes), avec l'heure, la réponse, le type, l'intervalle et la facilité.
- `2026-11-21-etat.csv` : l'état de ces 224 cartes à la fin de la journée.
- Colonne `cle` :
  - `id` désigne une carte du système (champ `Id`, stable d'un PC à l'autre) ;
  - `nid` désigne un identifiant de note Anki, stable pour les anciennes cartes synchronisées par AnkiWeb (ECG, AoutLicenceMath, etc.).
- La recherche `rated:1` n'est pas datée, elle ramène les cartes revues le jour de la recherche : ces fichiers peuvent donc inclure des révisions du 21/11 synchronisées depuis un autre appareil.
