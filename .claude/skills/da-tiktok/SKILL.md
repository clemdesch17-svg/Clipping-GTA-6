---
name: da-tiktok
description: Charte graphique « Vice City Néon » du compte TikTok GTA 6 — couleurs, polices, mise en page, ton des titres et descriptions. À appliquer à toute vidéo, couverture, titre ou texte publié sur le compte, et à relire avant de modifier le rendu (clipper.py / brand.json).
---

# DA « Vice City Néon »

Objectif : qu'on reconnaisse le compte en une demi-seconde dans le fil.
Les réglages vivent dans `brand.json` (couleurs, police, @pseudo) — ne jamais coder une couleur en dur ailleurs.

## Couleurs
| Rôle | Hex | Usage |
|---|---|---|
| Rose néon | `#FF2D95` | bandeau du titre, mot prononcé, séparateur, barre de progression |
| Cyan | `#19E6FF` | ligne d'accroche « ▶ STREAMER · TWITCH », ombre des sous-titres, liseré |
| Violet nuit | `#2A0A3D` | contour des sous-titres |
| Blanc | `#FFFFFF` | texte des sous-titres et du titre |

## Typo
- `Inter Display Black`, **italique**, MAJUSCULES, léger interlettrage.
- Sous-titres 92 px, 3 mots max par ligne, mot prononcé en rose.

## Mise en page (1080x1920)
- Facecam en haut (pleine largeur) / gameplay en bas, séparés par un trait rose + liseré cyan.
- Sans facecam : gameplay 4:5 au centre sur fond flouté assombri, cadré rose en haut, cyan en bas.
- Titre d'accroche dans un bandeau rose sur la jonction, ligne cyan « ▶ <STREAMER> · TWITCH » au-dessus.
- `@pseudo` en filigrane blanc translucide en haut à droite.
- Barre de progression rose en bas qui se remplit (rétention).
- Gameplay légèrement saturé (`eq=saturation=1.2:contrast=1.06`).

## Ton éditorial
- Titres : ≤ 45 caractères + 2–3 emojis couleur en fin de titre (rendus par `title_card.py`, bandeau rose arrondi + ombre cyan), nom du streamer + situation (« Squeezie n'aide plus personne sur GTA 6 💀😂 »). Objectif : donner envie de rire ou de voir le jeu dès la 1re seconde.
- Descriptions : phrase choc + emojis / question qui fait commenter + 👇 / `🎥 Twitch : <Nom>` / hashtags FR.
- Tutoiement, langage des viewers (« dinguerie », « plus jamais », « il a pas osé »), jamais méchant envers le streamer.

## Vérification
Avant de livrer : extraire une image par vidéo et contrôler bandeau lisible, pas de texte hors écran, facecam correcte, barre visible.
