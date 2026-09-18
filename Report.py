import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Importar el handler del archivo trasladovalores.py
from traslado_valores import traslado_handler

# Cargar variables de entorno (.env)
load_dotenv()

# Configuración de logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏦 Traslado de Valores", callback_data="iniciar_traslado")],
        # Aquí podrás agregar botones para futuros reportes cuando los creemos
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "👮‍♂️ *SISTEMA DE REPORTES - GERENCIA DE SEGURIDAD INTEGRAL*\n\n"
        "Bienvenido. Seleccione el tipo de reporte que desea realizar:"
    )
    await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")

if __name__ == '__main__':
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TOKEN:
        raise ValueError("Error: La variable de entorno TELEGRAM_TOKEN no está configurada.")

    app = ApplicationBuilder().token(TOKEN).build()

    # Registrar el menú general
    app.add_handler(CommandHandler('start', start_menu))
    app.add_handler(CommandHandler('menu', start_menu))

    # Registrar el módulo de Traslado de Valores
    app.add_handler(traslado_handler)

    print("Bot @ReportPcmBot en marcha desde Report.py...")
    app.run_polling()

