---
name: clip-gta
description: Produire le lot quotidien de clips TikTok GTA 6 (streamers français Twitch) — récupération, facecam, sous-titres, titres d'accroche, descriptions. À utiliser pour « fais les clips du jour », « ajoute un streamer », ou toute production de clips.
---

# Production quotidienne de clips GTA 6

## Ligne éditoriale
- Streamers **français** uniquement, jeu **Grand Theft Auto VI** uniquement (pas GTA V).
- Rotation : `per_day` clips par streamer actif (défaut 5), tous les streamers actifs chaque jour.
- Source : clips Twitch publics les plus vus des 7 derniers jours (déjà validés par les viewers).
- Jamais deux fois le même clip (`history.json`, à committer).
- Toujours créditer le streamer (« 🎥 Twitch : <Nom> » dans la description).

## Procédure
1. `python3 daily.py prepare` → télécharge, détecte la facecam, transcrit. Écrit `work/<date>/manifest.json`.
2. Pour CHAQUE clip du manifest, lire `transcript` (et les mots horodatés dans `<dir>/words.json`) puis écrire :
   - `hook` : titre d'accroche affiché sur la vidéo, ≤ 45 caractères, sans emoji, nom du streamer + situation drôle/choc
     (ex. « Squeezie n'aide plus personne sur GTA 6 », « Le roi de l'infiltration sur GTA 6 »).
   - `start` / `end` (secondes) : couper les blancs du début, finir juste après la punchline. Cible 15–40 s.
   - `description` : 1 phrase punchy + emojis, puis une QUESTION pour faire commenter
     (« T'aurais fait quoi à sa place ? 👇 »), puis `🎥 Twitch : <Nom>`, puis
     `#gta6 #gtavi #gta6fr #<streamer> #twitchfr #streamerfr #gaming #fyp #pourtoi`.
3. `python3 daily.py render` → `output/<date>/<Streamer>/NN.mp4` + `NN.txt` (description).
4. Vérifier visuellement 1 image par vidéo (facecam correcte, titre lisible, sous-titres sans chevauchement).
   Si la facecam est mauvaise : mettre `"facecam": [x, y, w, h]` (repère 1920x1080) ou `null` dans le manifest et relancer `render`.
5. Committer `history.json` (et `streamers.json` si modifié) et pousser.

## Ajouter / retirer un streamer
Éditer `streamers.json` : `{"login": "<pseudo twitch>", "per_day": 5, "active": true}`.

## Pièges connus (voir aussi tasks/lessons.md)
- YouTube bloque les téléchargements depuis le cloud → Twitch uniquement.
- VOD complètes souvent réservées aux abonnés → utiliser les clips publics.
- Whisper invente « Sous-titres réalisés par Amara.org » sur les passages sans voix (filtré dans `clipper.py`).
