# Lessons

Format : [date] | ce qui a mal tourné | règle pour l’éviter

(aucune pour l’instant)

[2026-11-18] | Téléchargement YouTube depuis l'env cloud : réseau ouvert mais YouTube renvoie 403 (anti-bot sur IP serveur) | Ne pas compter sur YouTube comme source : faire passer les vidéos par Google Drive (ou fichier fourni par l'utilisateur)
[2026-11-18] | faster-whisper plante en lisant le mp4 (incompatibilité PyAV) | Décoder l'audio avec ffmpeg en PCM 16 kHz et passer un tableau numpy
[2026-11-18] | Sous-titres superposés : le dernier mot d'un groupe débordait sur le groupe suivant, et le zoom du mot surligné chevauchait ses voisins | Borner la fin de chaque groupe au début du suivant, pas de zoom sur le mot actif ; vérifier les images rendues
[2026-11-18] | Filtre jeu « Grand Theft Auto » laissait passer GTA V | Comparer la catégorie exacte « Grand Theft Auto VI »
[2026-11-18] | Titres longs coupés hors écran (WrapStyle 2) | WrapStyle 0 + marges ; vérifier une image par vidéo
[2026-11-18] | `daily.py render` a réécrit les .txt avec les anciennes descriptions du manifest | Toute modif de texte se fait dans work/<date>/manifest.json, jamais directement dans output/
[2026-11-18] | Envoi des vidéos sur Drive refusé : limite de 4,2 Mo par appel du connecteur | Le connecteur Drive ne sert qu'aux textes ; les vidéos passent par un autre canal
[2026-11-19] | Sélection des clips au nombre de vues = clips moyens | Transcrire TOUS les clips GTA VI (~90) et choisir à la lecture : drôle ou analyse du jeu
[2026-11-19] | Facecam ratée sur gameplay calme / visages du jeu | Positions connues par streamer (`facecams` dans streamers.json) en secours, avec vérification d'un visage qui bouge
[2026-11-19] | Double sous-titres : le streamer a ses propres sous-titres incrustés | Ne garder que le haut du gameplay (GAME_SRC_H = 940) ; vérifier une image par vidéo
