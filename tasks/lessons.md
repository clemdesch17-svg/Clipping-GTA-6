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
[2026-11-19] | Clips jugés trop courts (16–30 s) | Durée cible 30–45 s : garder le contexte avant la punchline
[2026-11-19] | Transcription d'un VOD entier de 8 h avec le modèle « base » : texte inexploitable, et bien trop long avec « small » | Partir des clips viewers (signal humain), les localiser dans le VOD par corrélation audio, puis découper 30–45 s autour
[2026-11-19] | ffmpeg/--download-sections ne passe pas par le proxy (DNS) | Télécharger les segments HLS en Python (`vod_cut.py`), puis découper localement
[2026-11-19] | Localisation audio d'un clip avec un score < 0,6 → mauvais passage | Toujours retranscrire la découpe et vérifier qu'elle contient bien la phrase attendue
[2026-11-19] | 1er lot Anyme rejeté : clips viewers peu nombreux et faibles (réglages, manette) | Sur VOD public : repérer les fenêtres les plus « énergiques » (son soutenu vs médiane locale), transcrire en « small », garder délires / action / avis tranchés
[2026-11-19] | Facecam décalée : un ciel de jeu immobile a fusionné avec la webcam | Contrôler la bande facecam sur l'aperçu de CHAQUE vidéo ; corriger via `facecam` dans le manifest
[2026-11-19] | Titres jugés pas assez accrocheurs (phrase seule, sans emoji) ; libass n'affiche pas les emojis couleur | Bandeau titre rendu en PNG par title_card.py (Pillow + Noto Color Emoji), 2–3 emojis par titre ; split(" ") pour garder les espaces insécables
[2026-11-19] | 2e lot Anyme encore jugé moyen (clips d'hier, moments faibles) | Récolter aussi les clips du live du jour ; privilégier les situations absurdes/galères racontées par le streamer (pauvreté, bus, Fenwick, braquage tranquille) plutôt que les réactions au jeu
[2026-11-19] | Le 2e lot Michou a écrasé les vidéos du 1er lot (mêmes noms 01..05 dans output/<date>/<Streamer>/) | Sortie par lot : output/<date>/<Streamer>/<lot>/ ; ne jamais réutiliser un dossier de sortie
