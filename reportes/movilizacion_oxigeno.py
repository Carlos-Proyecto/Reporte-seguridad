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
    TIPO_MOVIMIENTO, ORIGEN_DESTINO, PERSONA_TRASLADO,
    CANTIDAD_BOMBONAS, NUMERACION_BOMBONAS, SEGURIDAD_JAULA,
    ADICIONAL_PREGUNTA, INFO_ADICIONAL
) = range(8)

TIPOS_MOVIMIENTO = ["Entrada", "Salida", "Reemplazo"]

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

async def iniciar_oxigeno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(tipo, callback_data=f"mov_{tipo}")] for tipo in TIPOS_MOVIMIENTO]
    
    texto = "*MOVILIZACIÓN DE BOMBONAS DE OXÍGENO*\n\nSeleccione el *Tipo de Movimiento*:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    return TIPO_MOVIMIENTO

async def procesar_tipo_movimiento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    tipo = query.data.replace("mov_", "")
    context.user_data['tipo_movimiento'] = tipo

    # Adaptar la pregunta según el tipo de movimiento seleccionado
    if tipo == "Entrada":
        prompt = "Escriba el *Lugar de Origen* de las bombonas:"
    elif tipo == "Salida":
        prompt = "Escriba el *Lugar de Destino* de las bombonas:"
    else:  # Reemplazo
        prompt = "Escriba el *Origen y Destino / Área de Reemplazo* de las bombonas:"

    await query.message.reply_text(prompt, parse_mode="Markdown")
    return ORIGEN_DESTINO

async def recibir_origen_destino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['origen_destino'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Nombre y Apellido* de la persona que realiza el traslado:", parse_mode="Markdown")
    return PERSONA_TRASLADO

async def recibir_persona_traslado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['persona_traslado'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Cantidad de bombonas movilizadas*:", parse_mode="Markdown")
    return CANTIDAD_BOMBONAS

async def recibir_cantidad_bombonas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cantidad_bombonas'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Numeración / Seriales* de las bombonas movilizadas:", parse_mode="Markdown")
    return NUMERACION_BOMBONAS

async def recibir_numeracion_bombonas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['numeracion_bombonas'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Nombre y Apellido* del personal de seguridad que abre la jaula de oxígeno:", parse_mode="Markdown")
    return SEGURIDAD_JAULA

async def recibir_seguridad_jaula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['seguridad_jaula'] = update.message.text.strip()

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

    tipo_mov = context.user_data['tipo_movimiento']
    etiqueta_ub = "Origen" if tipo_mov == "Entrada" else ("Destino" if tipo_mov == "Salida" else "Origen / Destino")

    lineas_reporte = [
        f"{saludo}",
        "*Reporte de Servicio*",
        "*Movilización de Bombonas de Oxígeno*",
        f"{fecha_str}\n",
        f"*Tipo de Movimiento:* {tipo_mov}",
        f"*{etiqueta_ub}:* {context.user_data['origen_destino']}",
        f"*Persona que Traslada:* {context.user_data['persona_traslado']}",
        f"*Cantidad Movilizada:* {context.user_data['cantidad_bombonas']}",
        f"*Numeración / Seriales:* {context.user_data['numeracion_bombonas']}",
        f"*Seguridad (Apertura de Jaula):* {context.user_data['seguridad_jaula']}"
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
    await update.message.reply_text("Reporte de Movilización de Oxígeno cancelado.")
    return ConversationHandler.END

# Exportación del Handler
oxigeno_handler = ConversationHandler(
    entry_points=[
        CommandHandler('oxigeno', iniciar_oxigeno),
        CallbackQueryHandler(iniciar_oxigeno, pattern='^iniciar_oxigeno$')
    ],
    states={
        TIPO_MOVIMIENTO: [CallbackQueryHandler(procesar_tipo_movimiento)],
        ORIGEN_DESTINO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_origen_destino)],
        PERSONA_TRASLADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_persona_traslado)],
        CANTIDAD_BOMBONAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cantidad_bombonas)],
        NUMERACION_BOMBONAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_numeracion_bombonas)],
        SEGURIDAD_JAULA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_seguridad_jaula)],
        ADICIONAL_PREGUNTA: [CallbackQueryHandler(respuesta_adicional)],
        INFO_ADICIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_info_adicional)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
