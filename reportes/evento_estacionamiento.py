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
    REPORTANTE, HORA_EVENTO, TIPO_EVENTO, LUGAR_EVENTO,
    MARCA_VEHICULO, MODELO_VEHICULO, PLACA_VEHICULO, COLOR_VEHICULO,
    PERSONAL_NOTIFICADO, ADICIONAL_PREGUNTA, INFO_ADICIONAL
) = range(11)

# Opciones predefinidas
TIPOS_EVENTO = [
    "Vehículo en condición insegura",
    "Colisión",
    "Movilización de vehículo",
    "Reclamo",
    "Revisión mecánica",
    "Vehículo remolcado"
]

LUGARES_ESTACIONAMIENTO = [
    "Estac. PB",
    "Estac. Sótano 1",
    "Estac. Sótano 2",
    "Estac. Sótano 3",
    "Estac. Sótano 4",
    "Estac. Sótano 5",
    "Estac. Terraza Piso 3"
]

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

async def iniciar_evento_estac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "*EVENTO EN ESTACIONAMIENTO*\n\nPor favor, escriba el *Nombre y Apellido* de la persona que realiza el reporte:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")
        
    return REPORTANTE

async def recibir_reportante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nombre_reportante'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Hora del evento* (ejemplo: 10:30 am):", parse_mode="Markdown")
    return HORA_EVENTO

async def recibir_hora_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hora_evento'] = update.message.text.strip()
    
    keyboard = [[InlineKeyboardButton(tipo, callback_data=f"tipo_{tipo}")] for tipo in TIPOS_EVENTO]
    keyboard.append([InlineKeyboardButton("Otro tipo (Escribir)", callback_data="tipo_otro")])
    
    await update.message.reply_text(
        "Seleccione o escriba el *Tipo de evento*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return TIPO_EVENTO

async def procesar_tipo_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "tipo_otro":
            await query.message.reply_text("Escriba el *Tipo de evento*:", parse_mode="Markdown")
            return TIPO_EVENTO
        else:
            context.user_data['tipo_evento'] = data.replace("tipo_", "")
            msg_obj = query.message
    else:
        context.user_data['tipo_evento'] = update.message.text.strip()
        msg_obj = update.message

    return await pedir_lugar_evento(msg_obj)

async def pedir_lugar_evento(message):
    keyboard = [[InlineKeyboardButton(lugar, callback_data=f"lugar_{lugar}")] for lugar in LUGARES_ESTACIONAMIENTO]
    keyboard.append([InlineKeyboardButton("Otro lugar (Escribir)", callback_data="lugar_otro")])
    
    await message.reply_text(
        "Seleccione o escriba el *Lugar del evento*:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return LUGAR_EVENTO

async def procesar_lugar_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "lugar_otro":
            await query.message.reply_text("Escriba el *Lugar del evento*:", parse_mode="Markdown")
            return LUGAR_EVENTO
        else:
            context.user_data['lugar_evento'] = data.replace("lugar_", "")
            msg_obj = query.message
    else:
        context.user_data['lugar_evento'] = update.message.text.strip()
        msg_obj = update.message

    await msg_obj.reply_text("Escriba la *Marca del vehículo*:", parse_mode="Markdown")
    return MARCA_VEHICULO

async def recibir_marca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['marca_vehiculo'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Modelo del vehículo*:", parse_mode="Markdown")
    return MODELO_VEHICULO

async def recibir_modelo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['modelo_vehiculo'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Placa del vehículo*:", parse_mode="Markdown")
    return PLACA_VEHICULO

async def recibir_placa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['placa_vehiculo'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Color del vehículo*:", parse_mode="Markdown")
    return COLOR_VEHICULO

async def recibir_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['color_vehiculo'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Nombre y Apellido del personal de estacionamiento* al que se le notificó:", parse_mode="Markdown")
    return PERSONAL_NOTIFICADO

async def recibir_personal_notificado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['personal_notificado'] = update.message.text.strip()

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
        "*Evento en Estacionamiento*",
        f"{fecha_str}\n",
        f"*Reportado por:* {context.user_data['nombre_reportante']}",
        f"*Hora del Evento:* {context.user_data['hora_evento']}",
        f"*Tipo de Evento:* {context.user_data['tipo_evento']}",
        f"*Lugar:* {context.user_data['lugar_evento']}",
        f"*Marca del Vehículo:* {context.user_data['marca_vehiculo']}",
        f"*Modelo del Vehículo:* {context.user_data['modelo_vehiculo']}",
        f"*Placa del Vehículo:* {context.user_data['placa_vehiculo']}",
        f"*Color del Vehículo:* {context.user_data['color_vehiculo']}",
        f"*Personal Notificado:* {context.user_data['personal_notificado']}"
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
    await update.message.reply_text("Reporte de Evento en Estacionamiento cancelado.")
    return ConversationHandler.END

# Exportación del Handler
evento_estacionamiento_handler = ConversationHandler(
    entry_points=[
        CommandHandler('evento_estacionamiento', iniciar_evento_estac),
        CallbackQueryHandler(iniciar_evento_estac, pattern='^iniciar_evento_estac$')
    ],
    states={
        REPORTANTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_reportante)],
        HORA_EVENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_hora_evento)],
        TIPO_EVENTO: [
            CallbackQueryHandler(procesar_tipo_evento),
            MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_tipo_evento)
        ],
        LUGAR_EVENTO: [
            CallbackQueryHandler(procesar_lugar_evento),
            MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_lugar_evento)
        ],
        MARCA_VEHICULO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_marca)],
        MODELO_VEHICULO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_modelo)],
        PLACA_VEHICULO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_placa)],
        COLOR_VEHICULO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_color)],
        PERSONAL_NOTIFICADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_personal_notificado)],
        ADICIONAL_PREGUNTA: [CallbackQueryHandler(respuesta_adicional)],
        INFO_ADICIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_info_adicional)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
