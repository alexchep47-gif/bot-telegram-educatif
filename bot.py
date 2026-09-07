"""Bot Telegram educatif — webhook + Gemini."""
import json
import logging
import os
import urllib.error
import urllib.request
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", "8080"))
WEBHOOK_URL = (
    os.environ.get("WEBHOOK_URL") or os.environ.get("RENDER_EXTERNAL_URL") or ""
).rstrip("/")

_ai = (os.environ.get("AI_API_KEY") or "").strip()
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
if not GEMINI_API_KEY and _ai.startswith("AIza"):
    GEMINI_API_KEY = _ai
GEMINI_BASE_URL = os.environ.get(
    "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
).rstrip("/")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
ANTHROPIC_API_KEY = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()


def _http_post(url, payload, headers, timeout=45):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _gemini_texte(sujet):
    if not GEMINI_API_KEY:
        return None
    url = f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    prompt = (
        "Explique le sujet suivant a un enfant/eleve de maniere simple, "
        f"claire et pedagogique, en francais : {sujet}"
    )
    try:
        data = _http_post(
            url,
            {"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
            {"Content-Type": "application/json"},
        )
        cands = data.get("candidates") or []
        if not cands:
            return None
        parts = (cands[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text") or "" for p in parts).strip()
        return text or None
    except urllib.error.HTTPError as e:
        logger.error("Gemini HTTP %s", e.code)
    except Exception as e:
        logger.error("Gemini : %s", e)
    return None


def _claude_texte(sujet):
    if not ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": (
                "Explique le sujet suivant a un enfant de maniere simple, "
                f"en francais : {sujet}"
            )}],
        )
        return message.content[0].text
    except Exception as e:
        logger.error("Claude : %s", e)
        return None


def generer_texte_educatif(sujet):
    texte = _gemini_texte(sujet) or _claude_texte(sujet)
    if texte:
        return texte
    return (
        f"Fiche sur : {sujet}\n\n"
        "Ajoute GEMINI_API_KEY sur Render (cle Google AI Studio, comme EduMentor)."
    )


def generer_pdf(sujet, contenu):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(f"<b>{sujet}</b>", styles["Title"]), Spacer(1, 0.5 * cm)]
    for paragraphe in contenu.split("\n"):
        if paragraphe.strip():
            safe = paragraphe.replace("&", "&").replace("<", "<")
            story.append(Paragraph(safe, styles["BodyText"]))
            story.append(Spacer(1, 0.3 * cm))
    doc.build(story)
    buffer.seek(0)
    return buffer


def generer_image_schema(titre):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.text(0.5, 0.5, titre, ha="center", va="center", fontsize=16, wrap=True)
    ax.axis("off")
    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer


async def start(update, context):
    await update.message.reply_text(
        "Bienvenue ! Assistant educatif (Gemini).\n\n"
        "/cours <sujet>\n/pdf <sujet>\n/image <sujet>\n\n"
        "Ou envoie une question en texte."
    )


async def cours(update, context):
    sujet = " ".join(context.args) if context.args else None
    if not sujet:
        await update.message.reply_text("Utilisation : /cours <sujet>")
        return
    await update.message.chat.send_action("typing")
    await update.message.reply_text(generer_texte_educatif(sujet))


async def pdf_command(update, context):
    sujet = " ".join(context.args) if context.args else None
    if not sujet:
        await update.message.reply_text("Utilisation : /pdf <sujet>")
        return
    await update.message.chat.send_action("upload_document")
    buffer = generer_pdf(sujet, generer_texte_educatif(sujet))
    await update.message.reply_document(
        document=InputFile(buffer, filename=f"{sujet[:40]}.pdf"),
        caption=f"Fiche : {sujet}",
    )


async def image_command(update, context):
    sujet = " ".join(context.args) if context.args else None
    if not sujet:
        await update.message.reply_text("Utilisation : /image <sujet>")
        return
    await update.message.chat.send_action("upload_photo")
    buffer = generer_image_schema(sujet)
    await update.message.reply_photo(photo=InputFile(buffer, filename="schema.png"))


async def recevoir_texte(update, context):
    await update.message.chat.send_action("typing")
    await update.message.reply_text(generer_texte_educatif(update.message.text))


async def recevoir_photo(update, context):
    await update.message.reply_text("Photo recue. Envoie aussi ta question en texte.")


async def recevoir_document(update, context):
    doc = update.message.document
    await update.message.reply_text(
        f"Document recu : {doc.file_name} ({(doc.file_size or 0) // 1024} Ko)"
    )


async def recevoir_video(update, context):
    await update.message.reply_text("Video recue.")


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
        webhook = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        logger.info("Webhook Telegram : %s port %s", webhook, PORT)
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=webhook,
            drop_pending_updates=True,
        )
    else:
        logger.info("Pas d URL publique — polling")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
