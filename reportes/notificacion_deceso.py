import urllib.parse
from datetime import datetime
import zoneinfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# Estados de la conversación (Se incluyó EDAD)
(
    NOMBRE, CEDULA, EDAD, LUGAR, MORGUE, HORA_MORGUE, 
    CERTIFICADO, SOLVENCIA, ADICIONAL_PREGUNTA, INFO_ADICIONAL
) = range(10)

# Opciones por defecto para el lugar del deceso
LUGARES_COMUNES = ["Emergencia", "UCI", "Hospitalización", "Pabellón"]

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

async def iniciar_deceso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "*NOTIFICACIÓN DE DECESO*\n\nPor favor, escriba el *Nombre y Apellido* del paciente:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")
        
    return NOMBRE

async def pedir_cedula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nombre_paciente'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Cédula de Identidad* del paciente:", parse_mode="Markdown")
    return CEDULA

async def pedir_edad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cedula_paciente'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Edad* del paciente:", parse_mode="Markdown")
    return EDAD

async def pedir_lugar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['edad_paciente'] = update.message.text.strip()
    
    keyboard = [[InlineKeyboardButton(lugar, callback_data=f"lugar_{lugar}")] for lugar in LUGARES_COMUNES]
    keyboard.append([InlineKeyboardButton("Otro lugar (Escribir)", callback_data="lugar_otro")])
    
    await update.message.reply_text(
        "Seleccione o escriba el *Lugar del Deceso*:",
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
    await message.reply_text("*¿Ingresó o no a la morgue?*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MORGUE

async def procesar_morgue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    respuesta = query.data.replace("morgue_", "")
    
    if respuesta == "Sí":
        context.user_data['ingreso_morgue_flag'] = "Sí"
        await query.message.reply_text("Escriba la *hora de ingreso a la morgue* (ejemplo: 14:30 hrs):", parse_mode="Markdown")
        return HORA_MORGUE
    else:
        context.user_data['ingreso_morgue'] = "No"
        await query.message.reply_text("Escriba el *Número de Certificado* de defunción:", parse_mode="Markdown")
        return CERTIFICADO

async def recibir_hora_morgue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hora_str = update.message.text.strip()
    context.user_data['ingreso_morgue'] = f"Sí - {hora_str}"
    
    await update.message.reply_text("Escriba el *Número de Certificado* de defunción:", parse_mode="Markdown")
    return CERTIFICADO

async def pedir_solvencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['num_certificado'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Nombre de la persona que da la solvencia*:", parse_mode="Markdown")
    return SOLVENCIA

async def preguntar_adicional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['persona_solvencia'] = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton("Sí", callback_data="adic_si")],
        [InlineKeyboardButton("No", callback_data="adic_no")]
    ]
    await update.message.reply_text("*¿Desea añadir alguna información adicional al reporte?*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ADICIONAL_PREGUNTA

async def respuesta_adicional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "adic_si":
        await query.message.reply_text("Escriba la información adicional:")
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
        "*Notificación de Deceso*",
        f"{fecha_str}\n",
        f"*Nombre y Apellido:* {context.user_data['nombre_paciente']}",
        f"*Cédula de Identidad:* {context.user_data['cedula_paciente']}",
        f"*Edad:* {context.user_data['edad_paciente']}",
        f"*Lugar del Deceso:* {context.user_data['lugar_deceso']}",
        f"*Ingreso a la Morgue:* {context.user_data['ingreso_morgue']}",
        f"*Número de Certificado:* {context.user_data['num_certificado']}",
        f"*Persona que da la Solvencia:* {context.user_data['persona_solvencia']}"
    ]

    info_adic = context.user_data.get('info_adicional')
    if info_adic:
        lineas_reporte.append(f"*Información Adicional:* {info_adic}")

    texto_reporte = "\n".join(lineas_reporte)

    texto_encoded = urllib.parse.quote(texto_reporte)
    url_whatsapp = f"https://wa.me/?text={texto_encoded}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Compartir en WhatsApp", url=url_whatsapp)]
    ])

    await message_obj.reply_text(f"*REPORTE GENERADO:*\n\n{texto_reporte}", reply_markup=keyboard, parse_mode="Markdown")
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
        CEDULA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_edad)],
        EDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_lugar)],
        LUGAR: [
            CallbackQueryHandler(procesar_lugar),
            MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_lugar)
        ],
        MORGUE: [CallbackQueryHandler(procesar_morgue)],
        HORA_MORGUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_hora_morgue)],
        CERTIFICADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_solvencia)],
        SOLVENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, preguntar_adicional)],
        ADICIONAL_PREGUNTA: [CallbackQueryHandler(respuesta_adicional)],
        INFO_ADICIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_info_adicional)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
