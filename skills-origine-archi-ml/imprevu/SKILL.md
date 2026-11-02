---
name: imprevu
description: "Gérer un imprévu ou un changement de disponibilité. Couvre : une séance ML impossible, déplacée ou annulée ; un rattrapage dans le tampon ; un week-end ou des jours sautés ; un changement durable de créneaux ; le « mode minimal ». À utiliser quand l'utilisateur écrit « imprévu : … », « je ne peux pas jeudi 16h30 », « annule la séance », « décale … », « je ne serai pas là ce week-end », « nouveaux horaires », « mode minimal » ou « semaine chargée »."
---

# Imprévu et changement de disponibilité

- **Durée** : environ 1 min.
- **Modèle conseillé** : Sonnet 5.5, effort low à medium.
- **Principe** (ARCHITECTURE §7) : un imprévu ne déclenche qu'un **déplacement local**. La semaine n'est réorganisée en entier qu'au check-in.
- **Aucun reproche.**

## 1. Lire (le minimum)

- `state/semaine.yaml` : les séances touchées et les séances restantes.
- `state/dispo.yaml` : `libres`, `exceptions`, `imprevus`, `tampon`.
- Au besoin, `python tools/cal.py semaine <date>` donne les créneaux datés et la capacité de la semaine.

## 2. Classer la demande

| Cas | Exemple | Section |
|---|---|---|
| A. Créneau(x) perdu(s) ponctuellement | « jeudi 16h30 je ne peux pas » | §3 |
| B. Période sans ML | « ce week-end je pars », « malade jusqu'à mercredi » | §3 |
| C. Changement durable | « désormais le mardi je finis à 21h » | §6 |
| D. Mode minimal | « mode minimal », « semaine impossible » | §7 |

Si la demande est ambiguë (quelle séance, quelle date), poser **une** question courte.

## 3. Enregistrer l'imprévu (cas A et B)

### Dans `state/dispo.yaml`
- **Cas A** : une entrée par créneau ML perdu, sous `imprevus` :
  `- {date: AAAA-MM-JJ, creneau: "HH:MM-HH:MM", note: "<motif court>"}`.
- **Cas B** : sous `exceptions`, ajouter
  `- {du: AAAA-MM-JJ, au: AAAA-MM-JJ, type: off, note: "<motif>", statut: confirme}`
  (`statut: provisoire` si ce n'est pas sûr).
- **Exception déjà listée en `provisoire`** (voir `docs/PROFIL.md`) et que l'utilisateur confirme : passer son `statut` à `confirme`.

### Dans `state/semaine.yaml`, pour chaque séance touchée
- `statut: deplacee` si elle sera rattrapée, cette semaine ou la suivante ;
- `statut: sautee` si l'utilisateur renonce au rattrapage. Le contenu sera replanifié au check-in.

## 4. Proposer des rattrapages : l'utilisateur confirme

Proposer **2 ou 3 options au plus**, en une liste courte.

### Option 1 : cette semaine, dans le tampon
- Un bloc de 2 h, entièrement contenu dans un créneau **libre déclaré** (`libres`) d'un jour restant.
- Il ne doit chevaucher **aucune** séance existante et ne pas tomber pendant une exception `off`.
- **Budget** : le total des rattrapages de la semaine reste ≤ `tampon.heures_semaine` (6 h).
- Rappel : le tampon est partagé avec l'ESSEC, les sorties et Phaness.

### Option 2 : la semaine suivante
- La séance reste `deplacee` et apparaît dans « À rattraper » de `NOW.md`.
- Le check-in la placera.

### Option 3 : abandonner
- Statut `sautee`.
- Le contenu est décalé au check-in, le jalon recalculé.

### Hors créneau libre
Un horaire hors créneau libre n'est possible que **si l'utilisateur le demande explicitement**. Il s'écrit alors avec `hors_creneau: true`.

**Ne rien placer sans confirmation.** Quand l'utilisateur a choisi :

### Créer la séance de rattrapage dans `state/semaine.yaml`

```yaml
  - id: <date>-<lettre>          # lettre suivante libre ce jour-là (a, b, c…)
    date: <date>
    creneau: "HH:MM-HH:MM"
    type: rattrapage
    module: <module de la séance remplacée>
    tache: "Rattrapage : <tache de la séance remplacée>"
    ressources: <identiques>
    livrable: <identique>
    statut: prevue
    heures_reelles: null
    hors_creneau: false            # true seulement sur demande explicite
    remplace: <id de la séance remplacée>
```

La séance d'origine garde `statut: deplacee`.

## 5. Rester local

- Ne modifier **aucune autre séance**, à une exception près. Si la séance perdue précède une séance du même module cette semaine (séance n, puis n+1), on peut **échanger les contenus** (`tache`, `ressources`, `livrable`) pour respecter l'ordre du cours. Le signaler.
- Ne pas toucher à `ROADMAP.md` ni à `state/jalons.yaml` : ils sont revus au check-in.

## 6. Changement durable de disponibilité (cas C)

1. **Reformuler** le changement et le faire confirmer : nouveaux créneaux, date de début.
2. Mettre à jour `state/dispo.yaml` :
   - `creneaux_ml` et/ou `libres` ;
   - `heures_ml_semaine` si le total change.
   - Il s'applique à partir de la **semaine suivante**. Les séances de la semaine en cours qui ne tiennent plus se traitent comme au cas A.
3. Mettre à jour le tableau correspondant de `docs/PROFIL.md` (section « Emploi du temps ») : il fait foi pour les contraintes.
4. Si la capacité baisse, lancer `python tools/cal.py jalons` et signaler les jalons à risque. Les arbitrages se font au check-in, et c'est l'utilisateur qui tranche.

## 7. Mode minimal (cas D)

- Il est déclenché d'un mot. On ne demande **aucune justification**, on ne fait aucun reproche.
- Par défaut, il court jusqu'à la fin de la semaine ISO en cours, ou sur la période indiquée.

1. Dans `state/dispo.yaml`, sous `exceptions`, ajouter
   `- {du: <aujourd'hui>, au: <dimanche>, type: quota, heures: 4, note: "mode minimal", statut: confirme}`.
2. **Garder 2 séances (4 h)** parmi les séances restantes. Proposer les plus utiles :
   - un prérequis de la suite ;
   - une consolidation d'une compétence fragile ;
   - un maintien dû.
   L'utilisateur confirme.
3. Passer les autres séances restantes en `sautee`, sans rattrapage.
4. Anki continue (5 min par jour suffisent). Les debriefs peuvent être courts (4 questions) ou en log rapide.
5. Le check-in a lieu quand même (version courte). S'il faut prolonger, c'est lui qui renouvelle l'exception. Au retour, appliquer le protocole de reprise (skill `checkin`).

## 8. Vérifier, régénérer, commiter

Les commandes se lancent **une par une** :

1. `python tools/check.py`. Corriger jusqu'à ce qu'il passe.
2. `python tools/now.py`.
3. `git add state/dispo.yaml state/semaine.yaml NOW.md` (et `docs/PROFIL.md` dans le cas C).
4. `git commit -m "imprevu: <résumé court>"`.
   - Exemples : `imprevu: jeu 05/11 16:30 -> sam 07/11 11:00`, `imprevu: mode minimal jusqu'au 15/11`.
5. `git push origin main`.

Répondre en 2 ou 3 lignes : ce qui a bougé, et où se trouve maintenant la séance (`NOW.md` à jour).
