import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)

# Importar los handlers desde la carpeta reportes/
from reportes.traslado_valores import traslado_handler
from reportes.notificacion_deceso import deceso_handler
from reportes.acta_emergencia import acta_handler
from reportes.plantilla_guardia import plantilla_handler
from reportes.entrega_cadaver import entrega_cadaver_handler  # <--- NUEVA IMPORTACIÓN

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Traslado de Valores", callback_data="iniciar_traslado")],
        [InlineKeyboardButton("Notificación de Deceso", callback_data="iniciar_deceso")],
        [InlineKeyboardButton("Entrega de Cadáver", callback_data="iniciar_entrega")],  # <--- NUEVA OPCIÓN
        [InlineKeyboardButton("Acta de Emergencia", callback_data="iniciar_acta")],
        [InlineKeyboardButton("Plantilla de Guardia", callback_data="iniciar_plantilla")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = (
        "*SISTEMA DE REPORTES - GERENCIA DE SEGURIDAD INTEGRAL*\n\n"
        "Bienvenido. Seleccione el tipo de reporte que desea realizar:"
    )
    
    if update.message:
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, reply_markup=reply_markup, parse_mode="Markdown")

if __name__ == '__main__':
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TOKEN:
        raise ValueError("Error: La variable de entorno TELEGRAM_TOKEN no está configurada.")

    app = ApplicationBuilder().token(TOKEN).build()

    # Registrar módulos de reportes
    app.add_handler(traslado_handler)
    app.add_handler(deceso_handler)
    app.add_handler(entrega_cadaver_handler)  # <--- NUEVO HANDLER REGISTRADO
    app.add_handler(acta_handler)
    app.add_handler(plantilla_handler)

    # Registrar comandos del menú general
    app.add_handler(CommandHandler('start', start_menu))
    app.add_handler(CommandHandler('menu', start_menu))
    app.add_handler(CallbackQueryHandler(start_menu, pattern='^volver_menu$'))

    print("Bot @ReportPcmBot en marcha desde Report.py...")
    app.run_polling()
