import urllib.parse
from datetime import datetime
import zoneinfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# Estados de la conversación
(
    LUGAR_HALLAZGO, PERSONA_ENTREGA, PERSONA_RECIBE, 
    HORA_ENTREGA, DESCRIPCION_BIEN, ADICIONAL_PREGUNTA, INFO_ADICIONAL
) = range(7)

# Opciones por defecto para el lugar del hallazgo
LUGARES_COMUNES = ["Emergencia", "Hospitalización", "Piso 1", "Piso 2", "Piso 3", "Piso 4", "Estacionamiento", "Cafetería"]

DÍAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def obtener_saludo_y_fecha():
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

async def iniciar_bienes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(lugar, callback_data=f"lugar_{lugar}")] for lugar in LUGARES_COMUNES]
    keyboard.append([InlineKeyboardButton("Otro lugar (Escribir)", callback_data="lugar_otro")])
    
    texto = "*REPORTE DE BIENES HALLADOS*\n\nSeleccione o escriba el *Lugar donde se encontró el bien*:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    return LUGAR_HALLAZGO

async def procesar_lugar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "lugar_otro":
            await query.message.reply_text("Escriba el *Lugar donde se encontró el bien*:", parse_mode="Markdown")
            return LUGAR_HALLAZGO
        else:
            context.user_data['lugar_hallazgo'] = data.replace("lugar_", "")
            msg_obj = query.message
    else:
        context.user_data['lugar_hallazgo'] = update.message.text.strip()
        msg_obj = update.message

    await msg_obj.reply_text("Escriba el *Nombre y Apellido de la persona que realiza la entrega en CECON*:", parse_mode="Markdown")
    return PERSONA_ENTREGA

async def recibir_persona_entrega(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['persona_entrega'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Nombre y Apellido de la persona que recibe el bien en CECON*:", parse_mode="Markdown")
    return PERSONA_RECIBE

async def recibir_persona_recibe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['persona_recibe'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Hora de la entrega* (ejemplo: 10:30 am):", parse_mode="Markdown")
    return HORA_ENTREGA

async def recibir_hora_entrega(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hora_entrega'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Descripción del bien hallado*:", parse_mode="Markdown")
    return DESCRIPCION_BIEN

async def recibir_descripcion_bien(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['descripcion_bien'] = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton("Sí", callback_data="adic_si")],
        [InlineKeyboardButton("No", callback_data="adic_no")]
    ]
    await update.message.reply_text("*¿Desea añadir alguna observación adicional al reporte?*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ADICIONAL_PREGUNTA

async def respuesta_adicional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "adic_si":
        await query.message.reply_text("Escriba la observación adicional:")
        return INFO_ADICIONAL
    else:
        context.user_data['info_adicional'] = None
        return await generar_reporte_final(query.message, context)

async def recibir_info_adicional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['info_adicional'] = update.message.text.strip()
    return await generar_reporte_final(update.message, context)

async def generar_reporte_final(message_obj, context: ContextTypes.DEFAULT_TYPE):
    saludo, fecha_str = obtener_saludo_y_fecha()

    lineas_reporte = [
        f"{saludo}",
        "*Reporte de Servicio*",
        "*Bienes Hallados*",
        f"{fecha_str}\n",
        f"*Lugar del Hallazgo:* {context.user_data['lugar_hallazgo']}",
        f"*Entregado en CECON por:* {context.user_data['persona_entrega']}",
        f"*Recibido en CECON por:* {context.user_data['persona_recibe']}",
        f"*Hora de Entrega:* {context.user_data['hora_entrega']}",
        f"*Descripción del Bien:* {context.user_data['descripcion_bien']}"
    ]

    info_adic = context.user_data.get('info_adicional')
    if info_adic:
        lineas_reporte.append(f"*Observaciones Adicionales:* {info_adic}")

    texto_reporte = "\n".join(lineas_reporte)

    texto_encoded = urllib.parse.quote(texto_reporte)
    url_whatsapp = f"https://wa.me/?text={texto_encoded}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Compartir en WhatsApp", url=url_whatsapp)],
        [InlineKeyboardButton("Nuevo Reporte", callback_data="volver_menu")]
    ])

    await message_obj.reply_text(f"*REPORTE GENERADO:*\n\n{texto_reporte}", reply_markup=keyboard, parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Reporte de Bienes Hallados cancelado.")
    return ConversationHandler.END

# Exportación del Handler
bienes_hallados_handler = ConversationHandler(
    entry_points=[
        CommandHandler('bienes_hallados', iniciar_bienes),
        CallbackQueryHandler(iniciar_bienes, pattern='^iniciar_bienes$')
    ],
    states={
        LUGAR_HALLAZGO: [
            CallbackQueryHandler(procesar_lugar),
            MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_lugar)
        ],
        PERSONA_ENTREGA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_persona_entrega)],
        PERSONA_RECIBE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_persona_recibe)],
        HORA_ENTREGA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_hora_entrega)],
        DESCRIPCION_BIEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_descripcion_bien)],
        ADICIONAL_PREGUNTA: [CallbackQueryHandler(respuesta_adicional)],
        INFO_ADICIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_info_adicional)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
