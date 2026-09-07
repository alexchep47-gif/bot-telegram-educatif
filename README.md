# Bot Telegram educatif

Webhook Telegram + Gemini (meme logique qu EduMentor).

## Render

1. New + Web Service, depot `bot-telegram-educatif`.
2. Variables :
   - `BOT_TOKEN` (BotFather)
   - `GEMINI_API_KEY` (cle Google AI Studio, celle de EduMentor si elle commence par AIza)
   - `WEBHOOK_URL` = URL Render sans slash final
     (sinon `RENDER_EXTERNAL_URL` est utilise tout seul)
3. Deploy. Au demarrage le bot enregistre :
   `https://TON-SERVICE.onrender.com/<BOT_TOKEN>`

Ping l URL toutes les 5 min (UptimeRobot) sur le plan gratuit.

## Commandes

`/start` `/cours` `/pdf` `/image` — ou une question en texte.
Priorite IA : Gemini 2.5 Flash, puis Claude si present.
