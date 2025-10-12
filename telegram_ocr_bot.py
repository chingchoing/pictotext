#!/usr/bin/env python3
"""
telegram_ocr_bot.py
Simple Telegram bot: image -> OCR text using Tesseract (pytesseract).
Requires: python-telegram-bot==13.15, Pillow, pytesseract, and tesseract binary installed.
"""

import os
import logging
from io import BytesIO
from PIL import Image, ImageOps, ImageFilter
import pytesseract
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ---- Config ----
TOKEN = os.environ.get("8262121748:AAH_tqT0xvv0yOUY1O4hGuiU8Cvt6_MVNME", "8262121748:AAH_tqT0xvv0yOUY1O4hGuiU8Cvt6_MVNME")
# If on Windows and tesseract binary not in PATH, set like:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Optional: which Tesseract language(s) to use, e.g. "eng+fra" or "eng". Make sure the language data (.traineddata) is installed.
TESSERACT_LANG = os.environ.get("TESSERACT_LANG", "eng")

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- Helpers ----
def preprocess_image_for_ocr(pil_img: Image.Image) -> Image.Image:
    """
    Basic preprocessing: convert to grayscale, increase contrast, optionally resize and denoise.
    Tweak as needed.
    """
    # convert to grayscale
    img = pil_img.convert("L")
    # auto-contrast
    img = ImageOps.autocontrast(img)
    # slight sharpening
    img = img.filter(ImageFilter.SHARPEN)
    # optional: resize if very small (improve OCR)
    max_dim = 1600
    if max(img.size) < 1000:
        scale = min(max_dim / max(img.size), 2.0)
        new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
        img = img.resize(new_size, Image.BILINEAR)
    return img

def perform_ocr(pil_img: Image.Image, lang: str = TESSERACT_LANG) -> str:
    try:
        img = preprocess_image_for_ocr(pil_img)
        # pytesseract.image_to_string supports config arguments too (e.g. psm)
        custom_config = r'--oem 3 --psm 3'  # oem 3 = default LSTM; psm 3 = fully automatic page segmentation
        text = pytesseract.image_to_string(img, lang=lang, config=custom_config)
        return text.strip()
    except Exception as e:
        logger.exception("OCR failed")
        return ""

# ---- Bot handlers ----
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Hi — send me a photo (or a document image) and I'll extract the text from it using OCR.\n"
        "Tip: For best results send a clear photo with readable text."
    )

def help_cmd(update: Update, context: CallbackContext):
    update.message.reply_text("Send an image (photo or document) and I will reply with the extracted text.")

def handle_photo(update: Update, context: CallbackContext):
    message = update.message
    # Photos arrive as sizes; pick the biggest
    try:
        if message.photo:
            photo = message.photo[-1]
            file = photo.get_file()
        elif message.document and message.document.mime_type.startswith("image/"):
            file = message.document.get_file()
        else:
            message.reply_text("Please send an image (photo or image file).")
            return

        # Download into memory
        bio = BytesIO()
        file.download(out=bio)
        bio.seek(0)
        pil_img = Image.open(bio).convert("RGB")

        msg = message.reply_text("Processing image for OCR...")

        text = perform_ocr(pil_img)
        if text:
            # If too long, send as a text file
            if len(text) > 4000:
                bio_out = BytesIO()
                bio_out.name = "ocr_result.txt"
                bio_out.write(text.encode("utf-8"))
                bio_out.seek(0)
                message.reply_document(document=bio_out, filename="ocr_result.txt", caption="Extracted text (file).")
            else:
                message.reply_text(f"Extracted text:\n\n{text}")
        else:
            message.reply_text("I couldn't find any text in the image. Try a clearer photo or higher resolution.")

        msg.delete()  # remove processing message
    except Exception as e:
        logger.exception("Error handling image")
        update.message.reply_text("Sorry, something went wrong while processing the image.")

def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("I don't understand. Send an image to perform OCR, or /help.")

# ---- Main ----
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(MessageHandler(Filters.photo | (Filters.document & Filters.document.mime_type("image/")), handle_photo))
    dp.add_handler(MessageHandler(Filters.command, unknown))

    logger.info("Starting bot...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
