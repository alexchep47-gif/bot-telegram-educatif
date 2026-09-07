"""
Bot Telegram éducatif — fonctionnement 24h/24
Capacités : lecture et génération de texte, PDF, images, vidéos.

Déploiement : mode webhook (Render Web Service gratuit).
Variables d'environnement nécessaires :
    BOT_TOKEN        -> token donné par @BotFather
    WEBHOOK_URL       -> URL publique du service (ex: https://mon-bot.onrender.com)
                         Sur Render, tu peux utiliser RENDER_EXTERNAL_URL automatiquement.
    PORT              -> fourni automatiquement par Render
    ANTHROPIC_API_KEY -> (optionnel) pour générer du contenu pédagogique via l'IA
"""

import os
import logging
from io import BytesIO

from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", "8080"))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") or os.environ.get("RENDER_EXTERNAL_URL")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


# ---------------------------------------------------------------------------
# Génération de contenu pédagogique (texte)
# ---------------------------------------------------------------------------

def generer_texte_educatif(sujet: str) -> str:
    """
    Génère une explication pédagogique sur un sujet donné.
    Utilise Claude (Anthropic) si une clé API est configurée,
    sinon renvoie un modèle simple à compléter manuellement.
    """
    if ANTHROPIC_API_KEY:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=800,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Explique le sujet suivant à un enfant/élève de manière "
                            f"simple, claire et pédagogique, en français : {sujet}"
                        ),
                    }
                ],
            )
            return message.content[0].text
        except Exception as e:
            logger.error("Erreur génération IA : %s", e)

    return (
        f"📘 Fiche sur : {sujet}\n\n"
        "Contenu à compléter — connecte une clé ANTHROPIC_API_KEY pour "
        "générer automatiquement des explications détaillées."
    )


# ---------------------------------------------------------------------------
# Génération de PDF
# ---------------------------------------------------------------------------

def generer_pdf(sujet: str, contenu: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"<b>{sujet}</b>", styles["Title"]),
        Spacer(1, 0.5 * cm),
    ]
    for paragraphe in contenu.split("\n"):
        if paragraphe.strip():
            story.append(Paragraph(paragraphe, styles["BodyText"]))
            story.append(Spacer(1, 0.3 * cm))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# Génération d'image (diagramme/illustration pédagogique simple)
# ---------------------------------------------------------------------------

def generer_image_schema(titre: str) -> BytesIO:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.text(0.5, 0.5, titre, ha="center", va="center", fontsize=16, wrap=True)
    ax.axis("off")
    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenue !\n\n"
        "Je suis ton assistant éducatif. Voici ce que je sais faire :\n\n"
        "/cours <sujet> — explication pédagogique en texte\n"
        "/pdf <sujet> — fiche de cours en PDF\n"
        "/image <sujet> — schéma illustratif\n\n"
        "Tu peux aussi m'envoyer une photo, un PDF ou une vidéo directement."
    )


async def cours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sujet = " ".join(context.args) if context.args else None
    if not sujet:
        await update.message.reply_text("Utilisation : /cours <sujet>")
        return
    await update.message.chat.send_action("typing")
    texte = generer_texte_educatif(sujet)
    await update.message.reply_text(texte)


async def pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sujet = " ".join(context.args) if context.args else None
    if not sujet:
        await update.message.reply_text("Utilisation : /pdf <sujet>")
        return
    await update.message.chat.send_action("upload_document")
    contenu = generer_texte_educatif(sujet)
    buffer = generer_pdf(sujet, contenu)
    await update.message.reply_document(
        document=InputFile(buffer, filename=f"{sujet[:40]}.pdf"),
        caption=f"📄 Fiche : {sujet}",
    )


async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sujet = " ".join(context.args) if context.args else None
    if not sujet:
        await update.message.reply_text("Utilisation : /image <sujet>")
        return
    await update.message.chat.send_action("upload_photo")
    buffer = generer_image_schema(sujet)
    await update.message.reply_photo(photo=InputFile(buffer, filename="schema.png"))


# ---------------------------------------------------------------------------
# Réception de fichiers envoyés par les utilisateurs (lecture)
# ---------------------------------------------------------------------------

async def recevoir_texte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    await update.message.chat.send_action("typing")
    reponse = generer_texte_educatif(question)
    await update.message.reply_text(reponse)


async def recevoir_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📷 Photo bien reçue ! (analyse d'image détaillée à venir dans une "
        "prochaine version)"
    )


async def recevoir_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    await update.message.reply_text(
        f"📎 Document reçu : {doc.file_name} ({doc.file_size // 1024} Ko)"
    )


async def recevoir_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Vidéo bien reçue ! (traitement vidéo à venir dans une prochaine "
        "version — nécessite plus de ressources serveur)"
    )


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("cours", cours))
    app.add_handler(CommandHandler("pdf", pdf_command))
    app.add_handler(CommandHandler("image", image_command))

    app.add_handler(MessageHandler(filters.PHOTO, recevoir_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, recevoir_document))
    app.add_handler(MessageHandler(filters.VIDEO, recevoir_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_texte))

    if WEBHOOK_URL:
        logger.info("Démarrage en mode webhook sur le port %s", PORT)
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}",
        )
    else:
        logger.info("WEBHOOK_URL non défini — démarrage en mode polling (local/dev)")
        app.run_polling()


if __name__ == "__main__":
    main()
