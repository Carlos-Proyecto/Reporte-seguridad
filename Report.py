import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)

# Importar los handlers desde la carpeta reportes/ (Orden alfabético)
from reportes.acta_emergencia import acta_handler
from reportes.bienes_hallados import bienes_hallados_handler
from reportes.entrega_cadaver import entrega_cadaver_handler
from reportes.evento_estacionamiento import evento_estacionamiento_handler
from reportes.notificacion_deceso import deceso_handler
from reportes.plantilla_guardia import plantilla_handler
from reportes.traslado_valores import traslado_handler

# Cargar variables de entorno (.env)
load_dotenv()

# Configuración de logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Botones ordenados alfabéticamente
    keyboard = [
        [InlineKeyboardButton("Acta de Emergencia", callback_data="iniciar_acta")],
        [InlineKeyboardButton("Bienes Hallados", callback_data="iniciar_bienes")],
        [InlineKeyboardButton("Entrega de Cadáver", callback_data="iniciar_entrega")],
        [InlineKeyboardButton("Evento en Estacionamiento", callback_data="iniciar_evento_estac")],
        [InlineKeyboardButton("Notificación de Deceso", callback_data="iniciar_deceso")],
        [InlineKeyboardButton("Plantilla de Guardia", callback_data="iniciar_plantilla")],
        [InlineKeyboardButton("Traslado de Valores", callback_data="iniciar_traslado")],
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

    # Registrar todos los módulos de reportes con prioridad de disparo
    app.add_handler(acta_handler)
    app.add_handler(bienes_hallados_handler)
    app.add_handler(entrega_cadaver_handler)
    app.add_handler(evento_estacionamiento_handler)
    app.add_handler(deceso_handler)
    app.add_handler(plantilla_handler)
    app.add_handler(traslado_handler)

    # Registrar comandos del menú general
    app.add_handler(CommandHandler('start', start_menu))
    app.add_handler(CommandHandler('menu', start_menu))
    app.add_handler(CallbackQueryHandler(start_menu, pattern='^volver_menu$'))

    print("Bot @ReportPcmBot en marcha desde Report.py...")
    app.run_polling()
