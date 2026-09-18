import urllib.parse
from datetime import datetime
import zoneinfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# Estados de la conversación
NOMBRE, CEDULA, LUGAR, MORGUE, CERTIFICADO, SOLVENCIA = range(6)

# Opciones por defecto para el lugar del deceso
LUGARES_COMUNES = ["Emergencia", "UCI", "Hospitalización", "Pabellón"]

DÍAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def obtener_saludo_y_fecha():
    # Zona horaria de Caracas para corregir desfase en servidor
    tz = zoneinfo.ZoneInfo("America/Caracas")
    ahora = datetime.now(tz)
    hora = ahora.hour

    if 5 <= hora < 12:
        saludo = "*Buenos días.*"
    elif 12 <= hora < 19:
        saludo = "*Buenas tardes.*"
    else:
        saludo = "*Buenas noches.*"
    
    dia_nombre = DÍAS[ahora.weekday()]
    mes_nombre = MESES[ahora.month - 1]
    fecha_str = f"*{dia_nombre}, {ahora.day} de {mes_nombre}*"
    return saludo, fecha_str

async def iniciar_deceso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_obj = update.message if update.message else update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    await msg_obj.reply_text(
        "🕊️ *NOTIFICACIÓN DE DECESO*\n\nPor favor, escriba el *Nombre y Apellido* del paciente:",
        parse_mode="Markdown"
    )
    return NOMBRE

async def pedir_cedula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nombre_paciente'] = update.message.text.strip()
    await update.message.reply_text("💳 Escriba la *Cédula de Identidad* del paciente:", parse_mode="Markdown")
    return CEDULA

async def pedir_lugar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cedula_paciente'] = update.message.text.strip()
    
    keyboard = [[InlineKeyboardButton(lugar, callback_data=f"lugar_{lugar}")] for lugar in LUGARES_COMUNES]
    keyboard.append([InlineKeyboardButton("✍️ Otro lugar (Escribir)", callback_data="lugar_otro")])
    
    await update.message.reply_text(
        "🏥 Seleccione o escriba el *Lugar del Deceso*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return LUGAR

async def procesar_lugar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "lugar_otro":
            context.user_data['esperando_lugar_manual'] = True
            await query.message.reply_text("Escriba el *Lugar del Deceso*:", parse_mode="Markdown")
            return LUGAR
        else:
            context.user_data['lugar_deceso'] = data.replace("lugar_", "")
            msg_obj = query.message
    else:
        context.user_data['lugar_deceso'] = update.message.text.strip()
        msg_obj = update.message

    return await pedir_morgue(msg_obj)

async def pedir_morgue(message):
    keyboard = [
        [InlineKeyboardButton("Sí, ingresó a la morgue", callback_data="morgue_Sí")],
        [InlineKeyboardButton("No, no ingresó a la morgue", callback_data="morgue_No")]
    ]
    await message.reply_text("🏛️ *¿Ingresó o no a la morgue?*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MORGUE

async def pedir_certificado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['ingreso_morgue'] = query.data.replace("morgue_", "")

    await query.message.reply_text("📄 Escriba el *Número de Certificado* de defunción:", parse_mode="Markdown")
    return CERTIFICADO

async def pedir_solvencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['num_certificado'] = update.message.text.strip()
    await update.message.reply_text("👤 Escriba el *Nombre de la persona que da la solvencia*:", parse_mode="Markdown")
    return SOLVENCIA

async def generar_reporte_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['persona_solvencia'] = update.message.text.strip()
    saludo, fecha_str = obtener_saludo_y_fecha()

    # Construcción del texto ajustando cada respuesta a la línea siguiente
    texto_reporte = (
        f"{saludo}\n"
        f"*Reporte de Servicio*\n"
        f"*Notificación de Deceso*\n"
        f"{fecha_str}\n\n"
        f"👤 *Nombre y Apellido:*\n{context.user_data['nombre_paciente']}\n"
        f"💳 *Cédula de Identidad:*\n{context.user_data['cedula_paciente']}\n"
        f"🏥 *Lugar del Deceso:*\n{context.user_data['lugar_deceso']}\n"
        f"🏛️ *Ingreso a la Morgue:*\n{context.user_data['ingreso_morgue']}\n"
        f"📄 *Número de Certificado:*\n{context.user_data['num_certificado']}\n"
        f"✍️ *Persona que da la Solvencia:*\n{context.user_data['persona_solvencia']}"
    )

    # Codificación para enlace de WhatsApp
    texto_encoded = urllib.parse.quote(texto_reporte)
    url_whatsapp = f"https://wa.me/?text={texto_encoded}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 Compartir en WhatsApp", url=url_whatsapp)]
    ])

    await update.message.reply_text(f"📋 *REPORTE GENERADO:*\n\n{texto_reporte}", reply_markup=keyboard, parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Notificación de Deceso cancelada.")
    return ConversationHandler.END

# Exportación del Handler
deceso_handler = ConversationHandler(
    entry_points=[
        CommandHandler('deceso', iniciar_deceso),
        CallbackQueryHandler(iniciar_deceso, pattern='^iniciar_deceso$')
    ],
    states={
        NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_cedula)],
        CEDULA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_lugar)],
        LUGAR: [
            CallbackQueryHandler(procesar_lugar),
            MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_lugar)
        ],
        MORGUE: [CallbackQueryHandler(pedir_certificado)],
        CERTIFICADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_solvencia)],
        SOLVENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, generar_reporte_final)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
