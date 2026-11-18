# TODO — Outil de clipping GTA 6

## Fait
- [x] Env cloud : réseau ouvert ; YouTube bloqué (403), Twitch OK
- [x] `clipper.py` v1 : 16:9 -> 9:16 (facecam haut / gameplay bas), sous-titres Whisper mot par mot, titre accroche
- [x] Test validé par l'utilisateur (output/test_bagarre.mp4)

## Plan v2 — Production quotidienne en rotation (EN ATTENTE DE VALIDATION)
Objectif : chaque jour, 5 clips par streamer, plusieurs streamers en rotation, sans intervention.

1. [ ] `streamers.json` : liste des streamers (pseudo Twitch, nb de clips/jour)
2. [ ] Récupération : clips Twitch publics les plus vus (24 h / 7 j), filtrés GTA (titre ou catégorie),
       en sautant ceux déjà publiés (`history.json`)
3. [ ] Détection auto de la facecam (différence entre images : zone fixe + visage) ; repli = sans facecam (fond flouté)
4. [ ] Montage : `clipper.py` (déjà fait) + coupe auto sur la partie parlée/forte (15–40 s)
5. [ ] Titre d'accroche + description + hashtags générés à partir de la transcription
6. [ ] `daily.py` : une commande -> dossier `output/AAAA-MM-JJ/<streamer>/` avec vidéos + textes
7. [ ] Livraison : dossier Google Drive du jour (pour poster depuis le téléphone)
8. [ ] Automatisation : tâche planifiée quotidienne
9. [ ] Skill `.claude/skills/clip-gta/SKILL.md` : style, règles, procédure (écrit par Claude)

## Vérification
- Lancer `daily.py` sur 2 streamers, contrôler visuellement chaque vidéo (facecam, sous-titres, durée)
