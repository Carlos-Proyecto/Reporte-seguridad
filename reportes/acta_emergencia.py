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
    INCIDENTE, CANTIDAD_PACIENTES, 
    NOMBRE_PACIENTE, CEDULA_PACIENTE, EDAD_PACIENTE, SEXO_PACIENTE,
    FECHA_HORA_INCIDENTE, UBICACION_INCIDENTE, DESCRIPCION_INCIDENTE,
    ADICIONAL_PREGUNTA, INFO_ADICIONAL
) = range(11)

INCIDENTES_COMUNES = ["Accidente de tránsito", "Riña", "Arma de Fuego", "Arma Blanca"]

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

async def iniciar_acta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Inicializar contenedor de pacientes
    context.user_data['pacientes'] = []
    context.user_data['paciente_actual'] = 0

    keyboard = [[InlineKeyboardButton(inc, callback_data=f"inc_{inc}")] for inc in INCIDENTES_COMUNES]
    keyboard.append([InlineKeyboardButton("Otro incidente (Escribir)", callback_data="inc_otro")])
    
    texto = "*ACTA DE EMERGENCIA*\n\nSeleccione o escriba el *Tipo de Incidente*:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    return INCIDENTE

async def procesar_incidente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "inc_otro":
            await query.message.reply_text("Escriba el *Tipo de Incidente*:", parse_mode="Markdown")
            return INCIDENTE
        else:
            context.user_data['tipo_incidente'] = data.replace("inc_", "")
            msg_obj = query.message
    else:
        context.user_data['tipo_incidente'] = update.message.text.strip()
        msg_obj = update.message

    await msg_obj.reply_text("Escriba la *Cantidad de Pacientes* que ingresan a la emergencia:", parse_mode="Markdown")
    return CANTIDAD_PACIENTES

async def recibir_cantidad_pacientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if not texto.isdigit() or int(texto) <= 0:
        await update.message.reply_text("Por favor, escriba un número válido mayor a 0:")
        return CANTIDAD_PACIENTES

    context.user_data['total_pacientes'] = int(texto)
    context.user_data['paciente_actual'] = 1
    
    cant = context.user_data['total_pacientes']
    prefijo = f" del Paciente 1" if cant > 1 else ""
    
    await update.message.reply_text(f"Escriba el *Nombre y Apellido*{prefijo}:", parse_mode="Markdown")
    return NOMBRE_PACIENTE

async def recibir_nombre_paciente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text.strip()
    actual = context.user_data['paciente_actual']
    cant = context.user_data['total_pacientes']
    
    # Crear estructura básica para este paciente
    context.user_data['temp_paciente'] = {'nombre': nombre}
    
    prefijo = f" del Paciente {actual}" if cant > 1 else ""
    await update.message.reply_text(f"Escriba la *Cédula de Identidad*{prefijo}:", parse_mode="Markdown")
    return CEDULA_PACIENTE

async def recibir_cedula_paciente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cedula = update.message.text.strip()
    context.user_data['temp_paciente']['cedula'] = cedula
    
    actual = context.user_data['paciente_actual']
    cant = context.user_data['total_pacientes']
    prefijo = f" del Paciente {actual}" if cant > 1 else ""
    
    await update.message.reply_text(f"Escriba la *Edad*{prefijo}:", parse_mode="Markdown")
    return EDAD_PACIENTE

async def recibir_edad_paciente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    edad = update.message.text.strip()
    context.user_data['temp_paciente']['edad'] = edad
    
    actual = context.user_data['paciente_actual']
    cant = context.user_data['total_pacientes']
    prefijo = f" del Paciente {actual}" if cant > 1 else ""
    
    keyboard = [
        [InlineKeyboardButton("Masculino", callback_data="sexo_Masculino")],
        [InlineKeyboardButton("Femenino", callback_data="sexo_Femenino")]
    ]
    
    await update.message.reply_text(
        f"Seleccione el *Sexo*{prefijo}:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SEXO_PACIENTE

async def recibir_sexo_paciente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    sexo = query.data.replace("sexo_", "")
    context.user_data['temp_paciente']['sexo'] = sexo
    
    # Guardar paciente en la lista
    context.user_data['pacientes'].append(context.user_data['temp_paciente'])
    
    actual = context.user_data['paciente_actual']
    total = context.user_data['total_pacientes']
    
    if actual < total:
        # Siguiente paciente
        context.user_data['paciente_actual'] += 1
        siguiente = context.user_data['paciente_actual']
        await query.message.reply_text(f"Escriba el *Nombre y Apellido* del Paciente {siguiente}:", parse_mode="Markdown")
        return NOMBRE_PACIENTE
    else:
        # Pasamos a las preguntas generales del incidente
        await query.message.reply_text("Escriba la *Fecha y Hora del Incidente* (ejemplo: Hoy a las 15:30 hrs):", parse_mode="Markdown")
        return FECHA_HORA_INCIDENTE

async def recibir_fecha_hora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fecha_hora_incidente'] = update.message.text.strip()
    await update.message.reply_text("Escriba la *Ubicación del Incidente*:", parse_mode="Markdown")
    return UBICACION_INCIDENTE

async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ubicacion_incidente'] = update.message.text.strip()
    await update.message.reply_text("Escriba una *Breve Descripción de lo Sucedido*:", parse_mode="Markdown")
    return DESCRIPCION_INCIDENTE

async def recibir_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['descripcion_incidente'] = update.message.text.strip()
    
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
        "*Acta de Emergencia*",
        f"{fecha_str}\n",
        f"*Tipo de Incidente:* {context.user_data['tipo_incidente']}",
        f"*Cantidad de Pacientes:* {context.user_data['total_pacientes']}\n"
    ]

    # Formatear la lista de pacientes
    pacientes = context.user_data['pacientes']
    for idx, p in enumerate(pacientes, 1):
        if len(pacientes) > 1:
            lineas_reporte.append(f"*Paciente {idx}:*")
        lineas_reporte.append(f"*Nombre y Apellido:* {p['nombre']}")
        lineas_reporte.append(f"*Cédula de Identidad:* {p['cedula']}")
        lineas_reporte.append(f"*Edad:* {p['edad']}")
        lineas_reporte.append(f"*Sexo:* {p['sexo']}\n")

    lineas_reporte.extend([
        f"*Fecha y Hora del Incidente:* {context.user_data['fecha_hora_incidente']}",
        f"*Ubicación del Incidente:* {context.user_data['ubicacion_incidente']}",
        f"*Descripción:* {context.user_data['descripcion_incidente']}"
    ])

    info_adic = context.user_data.get('info_adicional')
    if info_adic:
        lineas_reporte.append(f"*Información Adicional:* {info_adic}")

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
    await update.message.reply_text("Acta de Emergencia cancelada.")
    return ConversationHandler.END

# Exportación del Handler
acta_handler = ConversationHandler(
    entry_points=[
        CommandHandler('acta', iniciar_acta),
        CallbackQueryHandler(iniciar_acta, pattern='^iniciar_acta$')
    ],
    states={
        INCIDENTE: [
            CallbackQueryHandler(procesar_incidente),
            MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_incidente)
        ],
        CANTIDAD_PACIENTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cantidad_pacientes)],
        NOMBRE_PACIENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre_paciente)],
        CEDULA_PACIENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cedula_paciente)],
        EDAD_PACIENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_edad_paciente)],
        SEXO_PACIENTE: [CallbackQueryHandler(recibir_sexo_paciente)],
        FECHA_HORA_INCIDENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fecha_hora)],
        UBICACION_INCIDENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ubicacion)],
        DESCRIPCION_INCIDENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_descripcion)],
        ADICIONAL_PREGUNTA: [CallbackQueryHandler(respuesta_adicional)],
        INFO_ADICIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_info_adicional)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
