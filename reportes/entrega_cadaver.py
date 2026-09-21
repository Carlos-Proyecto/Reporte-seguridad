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
    NOMBRE, CEDULA, EDAD, SEXO, LUGAR_FALLECIMIENTO, CAUSA_DECESO,
    FECHA_HORA_DECESO, HORA_INGRESO_MORGUE, HORA_SALIDA_MORGUE,
    TIPO_RETIRA, NOMBRE_ENTIDAD, RESPONSABLE_RETIRA,
    PERSONA_SOLVENCIA, NUM_ACTA, PERSONA_ENTREGA,
    ADICIONAL_PREGUNTA, INFO_ADICIONAL
) = range(17)

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

async def iniciar_entrega(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "*ENTREGA DE CADÁVER*\n\nPor favor, escriba el *Nombre y Apellido* del paciente:"
    
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

async def pedir_sexo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['edad_paciente'] = update.message.text.strip()
    
    keyboard = [
        [InlineKeyboardButton("Masculino", callback_data="sexo_Masculino")],
        [InlineKeyboardButton("Femenino", callback_data="sexo_Femenino")]
    ]
    await update.message.reply_text("Seleccione el *Sexo* del paciente:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return SEXO

async def pedir_lugar_fallecimiento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['sexo_paciente'] = query.data.replace("sexo_", "")

    keyboard = [[InlineKeyboardButton(lugar, callback_data=f"lugar_{lugar}")] for lugar in LUGARES_COMUNES]
    keyboard.append([InlineKeyboardButton("Otro lugar (Escribir)", callback_data="lugar_otro")])
    
    await query.message.reply_text("Seleccione o escriba el *Lugar de la clínica donde falleció*:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return LUGAR_FALLECIMIENTO

async def procesar_lugar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "lugar_otro":
            await query.message.reply_text("Escriba el *Lugar de la clínica donde falleció*:", parse_mode="Markdown")
            return LUGAR_FALLECIMIENTO
        else:
            context.user_data['lugar_fallecimiento'] = data.replace("lugar_", "")
            msg_obj = query.message
    else:
        context.user_data['lugar_fallecimiento'] = update.message.text.strip()
        msg_obj = update.message

    await msg_obj.reply_text("Escriba la *Causa del Deceso*:", parse_mode="Markdown")
    return CAUSA_DECESO

async def pedir_fecha_hora_deceso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['causa_deceso'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Fecha y Hora del Deceso* (ejemplo: 20/09 a las 14:30 hrs):", parse_mode="Markdown")
    return FECHA_HORA_DECESO

async def pedir_hora_ingreso_morgue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fecha_hora_deceso'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Hora de ingreso a la morgue* (ejemplo: 15:00 hrs):", parse_mode="Markdown")
    return HORA_INGRESO_MORGUE

async def pedir_hora_salida_morgue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hora_ingreso_morgue'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Hora de salida de la morgue* (ejemplo: 17:30 hrs):", parse_mode="Markdown")
    return HORA_SALIDA_MORGUE

async def pedir_tipo_retira(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hora_salida_morgue'] = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton("Funeraria", callback_data="retira_Funeraria")],
        [InlineKeyboardButton("Organismo del Estado", callback_data="retira_Organismo del Estado")]
    ]
    await update.message.reply_text("*¿Quién retira el cadáver?*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return TIPO_RETIRA

async def pedir_nombre_entidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tipo = query.data.replace("retira_", "")
    context.user_data['tipo_retira'] = tipo

    if tipo == "Funeraria":
        prompt = "Escriba el *Nombre de la Funeraria*:"
    else:
        prompt = "Escriba el *Nombre del Organismo del Estado*:"

    await query.message.reply_text(prompt, parse_mode="Markdown")
    return NOMBRE_ENTIDAD

async def pedir_responsable_retira(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nombre_entidad'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Nombre y Apellido del responsable de retirar el cadáver*:", parse_mode="Markdown")
    return RESPONSABLE_RETIRA

async def pedir_solvencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['responsable_retira'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Nombre y Apellido de la persona que da la solvencia*:", parse_mode="Markdown")
    return PERSONA_SOLVENCIA

async def pedir_num_acta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['persona_solvencia'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Número de Acta de defunción*:", parse_mode="Markdown")
    return NUM_ACTA

async def pedir_persona_entrega(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['num_acta'] = update.message.text.strip()
    await update.message.reply_text("Escriba el *Nombre y Apellido de la persona que entrega el cadáver*:", parse_mode="Markdown")
    return PERSONA_ENTREGA

async def preguntar_adicional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['persona_entrega'] = update.message.text.strip()

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
        "*Entrega de Cadáver*",
        f"{fecha_str}\n",
        f"*Nombre y Apellido:* {context.user_data['nombre_paciente']}",
        f"*Cédula de Identidad:* {context.user_data['cedula_paciente']}",
        f"*Edad:* {context.user_data['edad_paciente']}",
        f"*Sexo:* {context.user_data['sexo_paciente']}",
        f"*Lugar de Fallecimiento:* {context.user_data['lugar_fallecimiento']}",
        f"*Causa del Deceso:* {context.user_data['causa_deceso']}",
        f"*Fecha y Hora del Deceso:* {context.user_data['fecha_hora_deceso']}",
        f"*Hora de Ingreso a Morgue:* {context.user_data['hora_ingreso_morgue']}",
        f"*Hora de Salida de Morgue:* {context.user_data['hora_salida_morgue']}",
        f"*Retirado por:* {context.user_data['tipo_retira']}",
        f"*Nombre de la Entidad:* {context.user_data['nombre_entidad']}",
        f"*Responsable que Retira:* {context.user_data['responsable_retira']}",
        f"*Persona que da Solvencia:* {context.user_data['persona_solvencia']}",
        f"*Número de Acta de Defunción:* {context.user_data['num_acta']}\n"
    ]

    # Construcción de la nota de cierre formal
    persona_entrega = context.user_data['persona_entrega']
    info_adic = context.user_data.get('info_adicional')

    if info_adic:
        nota_cierre = f"*{persona_entrega}* procedió con la entrega del cadáver siguiendo los procedimientos establecidos por la gerencia de seguridad, reportando además que {info_adic.lower()}"
    else:
        nota_cierre = f"*{persona_entrega}* procedió con la entrega del cadáver siguiendo los procedimientos establecidos por la gerencia de seguridad, sin novedad alguna."

    lineas_reporte.append(f"*Observaciones del Servicio:*\n{nota_cierre}")

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
    await update.message.reply_text("Entrega de Cadáver cancelada.")
    return ConversationHandler.END

# Exportación del Handler
entrega_cadaver_handler = ConversationHandler(
    entry_points=[
        CommandHandler('entrega_cadaver', iniciar_entrega),
        CallbackQueryHandler(iniciar_entrega, pattern='^iniciar_entrega$')
    ],
    states={
        NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_cedula)],
        CEDULA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_edad)],
        EDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_sexo)],
        SEXO: [CallbackQueryHandler(pedir_lugar_fallecimiento)],
        LUGAR_FALLECIMIENTO: [
            CallbackQueryHandler(procesar_lugar),
            MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_lugar)
        ],
        CAUSA_DECESO: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_fecha_hora_deceso)],
        FECHA_HORA_DECESO: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_hora_ingreso_morgue)],
        HORA_INGRESO_MORGUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_hora_salida_morgue)],
        HORA_SALIDA_MORGUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_tipo_retira)],
        TIPO_RETIRA: [CallbackQueryHandler(pedir_nombre_entidad)],
        NOMBRE_ENTIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_responsable_retira)],
        RESPONSABLE_RETIRA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_solvencia)],
        PERSONA_SOLVENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_num_acta)],
        NUM_ACTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_persona_entrega)],
        PERSONA_ENTREGA: [MessageHandler(filters.TEXT & ~filters.COMMAND, preguntar_adicional)],
        ADICIONAL_PREGUNTA: [CallbackQueryHandler(respuesta_adicional)],
        INFO_ADICIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_info_adicional)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
