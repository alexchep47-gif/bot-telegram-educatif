# Bot Telegram éducatif

## 1. Déploiement sur Render (gratuit)

1. Ce dépôt contient `bot.py`, `requirements.txt` et `render.yaml`.
2. Va sur [render.com](https://render.com) → **New +** → **Web Service** → connecte ce dépôt.
   Render détecte automatiquement `render.yaml`.
3. Dans l'onglet **Environment**, ajoute :
   - `BOT_TOKEN` → ton token donné par @BotFather
   - `ANTHROPIC_API_KEY` → (optionnel, pour la génération de texte par IA)
4. Une fois le premier déploiement terminé, Render te donne une URL du type
   `https://bot-telegram-educatif.onrender.com`.
   Retourne dans **Environment** et ajoute :
   - `WEBHOOK_URL` = `https://bot-telegram-educatif.onrender.com`
5. Redéploie (**Manual Deploy → Deploy latest commit**). Le bot configure
   automatiquement son webhook Telegram au démarrage.

## 2. Éviter la mise en veille (plan gratuit Render)

Le plan gratuit met le service en veille après 15 min d'inactivité. Pour un
vrai fonctionnement 24h/24 :
- Crée un compte gratuit sur [UptimeRobot](https://uptimerobot.com)
- Ajoute un moniteur HTTP qui ping `https://ton-service.onrender.com` toutes
  les 5 minutes.

Alternative sans mise en veille : un VPS **Oracle Cloud Free Tier**
(toujours gratuit) — demande un peu plus de configuration serveur mais reste
actif en permanence sans ping externe.

## 3. Commandes disponibles

- `/start` — présentation
- `/cours <sujet>` — explication pédagogique en texte
- `/pdf <sujet>` — fiche de cours en PDF
- `/image <sujet>` — schéma illustratif simple

Les enfants peuvent aussi envoyer directement une question en texte, une
photo, un document ou une vidéo — le bot répond automatiquement.

## 4. Prochaines étapes possibles

- Génération d'images pédagogiques plus riches (via une API d'image IA)
- Lecture/analyse du contenu des photos et PDF envoyés (OCR)
- Génération de courtes vidéos explicatives (nécessite plus de ressources
  serveur, à prévoir sur un plan payant ou VPS dédié)
