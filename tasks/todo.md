# TODO — Outil de clipping GTA 6

## Fait
- [x] Env cloud : réseau ouvert ; YouTube bloqué (403), Twitch OK
- [x] `clipper.py` : 16:9 -> 9:16, sous-titres Whisper mot par mot, titre accroche (retour à la ligne), mise en page sans facecam (fond flouté)
- [x] `facecam.py` : détection auto (visage stable + zone à faible variance temporelle) — vérifiée sur 7 clips Squeezie
- [x] `daily.py prepare|render` + `streamers.json` + `history.json` (anti-doublon)
- [x] Filtre strict GTA VI (les clips GTA V de Michou étaient acceptés à tort)
- [x] Skill `.claude/skills/clip-gta/SKILL.md`
- [x] Premier lot : 5 clips Squeezie dans output/2026-11-18/Squeezie/, vérifiés image par image

## En attente utilisateur
- [ ] Retour sur le lot du jour
- [ ] Lien TikTok -> voir ce qui est faisable côté publication

## Prochaines étapes
- [ ] Livraison quotidienne dans Google Drive
- [ ] Tâche planifiée quotidienne (prepare -> hooks par Claude -> render -> Drive)
- [ ] Ajouter des streamers FR qui jouent à GTA 6 (Michou joue encore à GTA V)
