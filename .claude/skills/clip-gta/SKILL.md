---
name: clip-gta
description: Produire le lot quotidien de clips TikTok GTA 6 (streamers français Twitch) — récupération, facecam, sous-titres, titres d'accroche, descriptions. À utiliser pour « fais les clips du jour », « ajoute un streamer », ou toute production de clips.
---

# Production quotidienne de clips GTA 6

## Ligne éditoriale
- Streamers **français** uniquement, jeu **Grand Theft Auto VI** uniquement (pas GTA V).
- Rotation : `per_day` clips par streamer actif (défaut 5), tous les streamers actifs chaque jour.
- Source : tous les clips Twitch publics GTA VI des 7 derniers jours, sélectionnés à la lecture des transcriptions (pas seulement aux vues).
- Jamais deux fois le même clip (`history.json`, à committer).
- Toujours créditer le streamer (« 🎥 Twitch : <Nom> » dans la description).

## Goût du propriétaire (validé sur ses choix)
Clips gardés : la dépanneuse, Bambi, la bagarre et le saut en moto de Michou ; les galères d'Anyme (bus, camping, Fenwick).
Priorité, dans cet ordre :
1. **Action / tirs / bagarres** (fusillades, courses-poursuites, embrouilles qui dégénèrent).
2. **Ça doit faire rire** : galère, fail, mort absurde, réaction du streamer.
3. **RP intéressant** : le streamer qui joue un rôle, invente une histoire, parle aux PNJ comme dans un film.
À éviter : réglages, découverte de la carte, discussions calmes sur le jeu, blagues crues (ban TikTok).

## Procédure
0. **Sélection (le plus important)** : `python3 harvest.py <login> work/harvest/<login>` récupère et transcrit
   TOUS les clips GTA VI de la semaine. Lire toutes les transcriptions et ne garder que les moments
   **drôles** (réaction, galère, punchline) ou où il **parle du jeu** (mécaniques, détails, comparaison).
   Le nombre de vues seul donne des clips moyens. Un même moment clippé plusieurs fois → garder la meilleure version.
   **Si les VOD du streamer sont publics** (`"vod_public": true`) : localiser chaque bon clip dans le VOD
   (`vod_cut.py locate`, score ≥ 0,6), puis `vod_cut.py cut <vod> <début> <fin>` pour obtenir 30–45 s avec plus
   de contexte. Retranscrire la découpe pour vérifier. Webcam plein écran → `"facecam": {"full": <x du visage>}`.
1. `python3 daily.py prepare` → télécharge, détecte la facecam, transcrit. Écrit `work/<date>/manifest.json`.
2. Pour CHAQUE clip du manifest, lire `transcript` (et les mots horodatés dans `<dir>/words.json`) puis écrire :
   - `hook` : titre d'accroche affiché sur la vidéo, ≤ 45 caractères + **2 à 3 emojis en fin de titre** qui donnent
     le ton (😂💀😭 pour le drôle, 🤯🔥😱 pour le jeu, 🚔💸🦀✈️ pour illustrer). Nom du streamer + situation drôle/choc
     (ex. « Squeezie n'aide plus personne sur GTA 6 💀😂 », « Anyme découvre l'arme ultime : le crabe 🦀😂 »).
     Les emojis sont rendus en couleur par `title_card.py`.
   - `start` / `end` (secondes) : couper les blancs du début, finir juste après la punchline. **Durée cible : 30–45 s** (demande du propriétaire du compte) — garder le contexte avant la punchline plutôt que couper trop serré.
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
