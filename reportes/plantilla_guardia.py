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
    TIPO_GUARDIA,
    CANT_TITULARES, NOMBRES_TITULARES,
    CANT_ESPECIALES, NOMBRES_ESPECIALES,
    TIENE_LIBRES, CANT_LIBRES, NOMBRES_LIBRES,
    TIENE_AUSENTES, CANT_AUSENTES, NOMBRES_AUSENTES,
    TIENE_VACACIONES, CANT_VACACIONES, NOMBRES_VACACIONES,
    COORD_JDML, POS_TRANSPORTE_JDML, POS_PROVEEDORES_JDML, POS_QUINTA_JDML, POS_PISO2_JDML, POS_CTRL_PCM_JDML, POS_CTRL_CORTIJOS_JDML,
    POS_PISO4_CSP, POS_EMERGENCIA_CSP, POS_REVISION_CSP, POS_SOTANO5_CSP,
    NOVEDADES
) = range(26)

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

# --- INICIO Y TIPO DE GUARDIA ---

async def iniciar_plantilla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_obj = update.message if update.message else update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    # Limpiar datos previos
    context.user_data['titulares'] = []
    context.user_data['especiales'] = []
    context.user_data['libres'] = []
    context.user_data['ausentes'] = []
    context.user_data['vacaciones'] = []

    keyboard = [
        [InlineKeyboardButton("☀️ Diurna", callback_data="guardia_Diurna")],
        [InlineKeyboardButton("🌙 Nocturna", callback_data="guardia_Nocturna")]
    ]
    await msg_obj.reply_text(
        "*REPORTE DE PLANTILLA*\n\nSeleccione el tipo de guardia:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return TIPO_GUARDIA

async def seleccionar_tipo_guardia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tipo = query.data.replace("guardia_", "")
    context.user_data['tipo_guardia'] = tipo

    await query.message.reply_text(
        f"🛡️ *Seguridad Interna PCM* ({tipo})\n"
        "Indique la *cantidad de Operadores Titulares* presentes en la guardia (en números):",
        parse_mode="Markdown"
    )
    return CANT_TITULARES

# --- 1. SEGURIDAD INTERNA PCM ---

async def recibir_cant_titulares(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if not texto.isdigit():
        await update.message.reply_text("Por favor, ingrese un número válido:")
        return CANT_TITULARES
    
    cant = int(texto)
    context.user_data['cant_titulares'] = cant
    if cant == 0:
        return await pedir_cant_especiales(update)
    
    context.user_data['idx_titular'] = 1
    await update.message.reply_text("Escriba el Nombre y Apellido del *Titular 1*:", parse_mode="Markdown")
    return NOMBRES_TITULARES

async def recibir_nombre_titular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text.strip()
    context.user_data['titulares'].append(nombre)
    idx = context.user_data['idx_titular'] + 1
    
    if idx <= context.user_data['cant_titulares']:
        context.user_data['idx_titular'] = idx
        await update.message.reply_text(f"Escriba el Nombre y Apellido del *Titular {idx}*:", parse_mode="Markdown")
        return NOMBRES_TITULARES
    else:
        return await pedir_cant_especiales(update)

async def pedir_cant_especiales(update: Update):
    msg_obj = update.message if update.message else update.callback_query.message
    await msg_obj.reply_text("Indique la *cantidad de personal en Guardias Especiales* (en números):", parse_mode="Markdown")
    return CANT_ESPECIALES

async def recibir_cant_especiales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if not texto.isdigit():
        await update.message.reply_text("Por favor, ingrese un número válido:")
        return CANT_ESPECIALES
    
    cant = int(texto)
    context.user_data['cant_especiales'] = cant
    if cant == 0:
        return await preguntar_libres(update)
    
    context.user_data['idx_especial'] = 1
    await update.message.reply_text("Escriba el Nombre y Apellido de la *Guardia Especial 1*:", parse_mode="Markdown")
    return NOMBRES_ESPECIALES

async def recibir_nombre_especial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text.strip()
    context.user_data['especiales'].append(nombre)
    idx = context.user_data['idx_especial'] + 1
    
    if idx <= context.user_data['cant_especiales']:
        context.user_data['idx_especial'] = idx
        await update.message.reply_text(f"Escriba el Nombre y Apellido de la *Guardia Especial {idx}*:", parse_mode="Markdown")
        return NOMBRES_ESPECIALES
    else:
        return await preguntar_libres(update)

# --- LIBRES ---

async def preguntar_libres(update: Update):
    msg_obj = update.message if update.message else update.callback_query.message
    keyboard = [
        [InlineKeyboardButton("Sí", callback_data="libres_si")],
        [InlineKeyboardButton("No", callback_data="libres_no")]
    ]
    await msg_obj.reply_text("¿Hay *personal Libre*?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return TIENE_LIBRES

async def respuesta_tiene_libres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "libres_si":
        await query.message.reply_text("Indique la *cantidad de personal Libre* (en números):", parse_mode="Markdown")
        return CANT_LIBRES
    else:
        return await preguntar_ausentes(query.message)

async def recibir_cant_libres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if not texto.isdigit() or int(texto) <= 0:
        await update.message.reply_text("Por favor, ingrese un número mayor a 0:")
        return CANT_LIBRES
    
    context.user_data['cant_libres'] = int(texto)
    context.user_data['idx_libre'] = 1
    await update.message.reply_text("Escriba el Nombre y Apellido del *Personal Libre 1*:", parse_mode="Markdown")
    return NOMBRES_LIBRES

async def recibir_nombre_libre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text.strip()
    context.user_data['libres'].append(nombre)
    idx = context.user_data['idx_libre'] + 1
    
    if idx <= context.user_data['cant_libres']:
        context.user_data['idx_libre'] = idx
        await update.message.reply_text(f"Escriba el Nombre y Apellido del *Personal Libre {idx}*:", parse_mode="Markdown")
        return NOMBRES_LIBRES
    else:
        return await preguntar_ausentes(update.message)

# --- AUSENTES ---

async def preguntar_ausentes(message):
    keyboard = [
        [InlineKeyboardButton("Sí", callback_data="aus_si")],
        [InlineKeyboardButton("No", callback_data="aus_no")]
    ]
    await message.reply_text("¿Hay *personal Ausente*?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return TIENE_AUSENTES

async def respuesta_tiene_ausentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "aus_si":
        await query.message.reply_text("Indique la *cantidad de personal Ausente* (en números):", parse_mode="Markdown")
        return CANT_AUSENTES
    else:
        return await preguntar_vacaciones(query.message)

async def recibir_cant_ausentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if not texto.isdigit() or int(texto) <= 0:
        await update.message.reply_text("Por favor, ingrese un número mayor a 0:")
        return CANT_AUSENTES
    
    context.user_data['cant_ausentes'] = int(texto)
    context.user_data['idx_ausente'] = 1
    await update.message.reply_text("Escriba el Nombre y Apellido del *Personal Ausente 1*:", parse_mode="Markdown")
    return NOMBRES_AUSENTES

async def recibir_nombre_ausente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text.strip()
    context.user_data['ausentes'].append(nombre)
    idx = context.user_data['idx_ausente'] + 1
    
    if idx <= context.user_data['cant_ausentes']:
        context.user_data['idx_ausente'] = idx
        await update.message.reply_text(f"Escriba el Nombre y Apellido del *Personal Ausente {idx}*:", parse_mode="Markdown")
        return NOMBRES_AUSENTES
    else:
        return await preguntar_vacaciones(update.message)

# --- VACACIONES ---

async def preguntar_vacaciones(message):
    keyboard = [
        [InlineKeyboardButton("Sí", callback_data="vac_si")],
        [InlineKeyboardButton("No", callback_data="vac_no")]
    ]
    await message.reply_text("¿Hay *personal de Vacaciones*?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return TIENE_VACACIONES

async def respuesta_tiene_vacaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "vac_si":
        await query.message.reply_text("Indique la *cantidad de personal de Vacaciones* (en números):", parse_mode="Markdown")
        return CANT_VACACIONES
    else:
        return await pedir_coord_jdml(query.message)

async def recibir_cant_vacaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if not texto.isdigit() or int(texto) <= 0:
        await update.message.reply_text("Por favor, ingrese un número mayor a 0:")
        return CANT_VACACIONES
    
    context.user_data['cant_vacaciones'] = int(texto)
    context.user_data['idx_vacacion'] = 1
    await update.message.reply_text("Escriba el Nombre y Apellido del *Personal de Vacaciones 1*:", parse_mode="Markdown")
    return NOMBRES_VACACIONES

async def recibir_nombre_vacacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text.strip()
    context.user_data['vacaciones'].append(nombre)
    idx = context.user_data['idx_vacacion'] + 1
    
    if idx <= context.user_data['cant_vacaciones']:
        context.user_data['idx_vacacion'] = idx
        await update.message.reply_text(f"Escriba el Nombre y Apellido del *Personal de Vacaciones {idx}*:", parse_mode="Markdown")
        return NOMBRES_VACACIONES
    else:
        return await pedir_coord_jdml(update.message)

# --- 2. EMPRESA JDML ---

async def pedir_coord_jdml(message):
    await message.reply_text("🛡️ *EMPRESA JDML*\n\nEscriba el Nombre y Apellido del *Coordinador*:", parse_mode="Markdown")
    return COORD_JDML

async def recibir_coord_jdml(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['coord_jdml'] = update.message.text.strip()
    await update.message.reply_text("Escriba el Nombre y Apellido en *Transporte*:", parse_mode="Markdown")
    return POS_TRANSPORTE_JDML

async def recibir_transporte_jdml(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['transporte_jdml'] = update.message.text.strip()
    
    # Si es guardia Diurna, pedimos Proveedores; si es Nocturna, pasamos directo a Quinta Fides
    if context.user_data.get('tipo_guardia') == "Diurna":
        await update.message.reply_text("Escriba el Nombre y Apellido en *Proveedores*:", parse_mode="Markdown")
        return POS_PROVEEDORES_JDML
    else:
        await update.message.reply_text("Escriba el Nombre y Apellido en *Quinta Fides*:", parse_mode="Markdown")
        return POS_QUINTA_JDML

async def recibir_proveedores_jdml(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['proveedores_jdml'] = update.message.text.strip()
    await update.message.reply_text("Escriba el Nombre y Apellido en *Quinta Fides*:", parse_mode="Markdown")
    return POS_QUINTA_JDML

async def recibir_quinta_jdml(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['quinta_jdml'] = update.message.text.strip()
    
    # Si es Diurna, continuamos con las posiciones diurnas restantes de JDML
    if context.user_data.get('tipo_guardia') == "Diurna":
        await update.message.reply_text("Escriba el Nombre y Apellido en *Piso 2*:", parse_mode="Markdown")
        return POS_PISO2_JDML
    else:
        # Si es Nocturna, pasamos a CSP 24/7 (Revisión)
        await update.message.reply_text("🛡️ *EMPRESA CSP 24/7*\n\nEscriba el Nombre y Apellido en *Revisión*:", parse_mode="Markdown")
        return POS_REVISION_CSP

async def recibir_piso2_jdml(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['piso2_jdml'] = update.message.text.strip()
    await update.message.reply_text("Escriba el Nombre y Apellido en *Controlador PCM*:", parse_mode="Markdown")
    return POS_CTRL_PCM_JDML

async def recibir_ctrl_pcm_jdml(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ctrl_pcm_jdml'] = update.message.text.strip()
    await update.message.reply_text("Escriba el Nombre y Apellido en *Controlador Los Cortijos*:", parse_mode="Markdown")
    return POS_CTRL_CORTIJOS_JDML

# --- 3. EMPRESA CSP 24/7 ---

async def recibir_ctrl_cortijos_jdml(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ctrl_cortijos_jdml'] = update.message.text.strip()
    
    # Para guardia Diurna, CSP inicia en Piso 4
    await update.message.reply_text("🛡️ *EMPRESA CSP 24/7*\n\nEscriba el Nombre y Apellido en *Piso 4*:", parse_mode="Markdown")
    return POS_PISO4_CSP

async def recibir_piso4_csp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['piso4_csp'] = update.message.text.strip()
    await update.message.reply_text("Escriba el Nombre y Apellido en *Emergencia*:", parse_mode="Markdown")
    return POS_EMERGENCIA_CSP

async def recibir_emergencia_csp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['emergencia_csp'] = update.message.text.strip()
    await update.message.reply_text("Escriba el Nombre y Apellido en *Revisión*:", parse_mode="Markdown")
    return POS_REVISION_CSP

async def recibir_revision_csp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['revision_csp'] = update.message.text.strip()
    await update.message.reply_text("Escriba el Nombre y Apellido en *Sótano 5*:", parse_mode="Markdown")
    return POS_SOTANO5_CSP

# --- NOVEDADES Y REPORTE FINAL ---

async def pedir_novedades_plantilla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['sotano5_csp'] = update.message.text.strip()
    
    keyboard = [
        [InlineKeyboardButton("Sin novedades en la recepción", callback_data="nov_Sin novedades en la recepción de la guardia.")],
        [InlineKeyboardButton("Registrar Novedad", callback_data="nov_registrar")]
    ]
    await update.message.reply_text("*¿Existe alguna novedad en el momento de la recepción de la guardia?*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return NOVEDADES

async def generar_reporte_plantilla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "nov_registrar":
            await query.message.reply_text("Escriba los detalles de la novedad:")
            return NOVEDADES
        novedades = query.data.replace("nov_", "")
        msg_obj = query.message
    else:
        novedades = update.message.text.strip()
        msg_obj = update.message

    saludo, fecha_str = obtener_saludo_y_fecha()
    tipo_guardia = context.user_data.get('tipo_guardia', 'Diurna')

    def fmt_lista(lista):
        return "\n".join([f"- {nombre}" for nombre in lista])

    # Bloques PCM
    pcm_bloques = []

    titulares = context.user_data.get('titulares', [])
    if titulares:
        pcm_bloques.append(f"*Operadores Titulares Presentes:*\n{fmt_lista(titulares)}")
    else:
        pcm_bloques.append("*Operadores Titulares Presentes:*\n- Ninguno")

    especiales = context.user_data.get('especiales', [])
    if especiales:
        pcm_bloques.append(f"*Guardias Especiales:*\n{fmt_lista(especiales)}")

    libres = context.user_data.get('libres', [])
    if libres:
        pcm_bloques.append(f"*Personal Libre:*\n{fmt_lista(libres)}")

    ausentes = context.user_data.get('ausentes', [])
    if ausentes:
        pcm_bloques.append(f"*Personal Ausente:*\n{fmt_lista(ausentes)}")

    vacaciones = context.user_data.get('vacaciones', [])
    if vacaciones:
        pcm_bloques.append(f"*Personal de Vacaciones:*\n{fmt_lista(vacaciones)}")

    pcm_seccion = "\n\n".join(pcm_bloques)

    # Construir JDML según tipo de guardia (Nombres al lado de la posición)
    if tipo_guardia == "Diurna":
        jdml_seccion = (
            f"🛡️ *EMPRESA JDML*\n"
            f"*Coordinador:* {context.user_data.get('coord_jdml')}\n"
            f"*Transporte:* {context.user_data.get('transporte_jdml')}\n"
            f"*Proveedores:* {context.user_data.get('proveedores_jdml')}\n"
            f"*Quinta Fides:* {context.user_data.get('quinta_jdml')}\n"
            f"*Piso 2:* {context.user_data.get('piso2_jdml')}\n"
            f"*Controlador PCM:* {context.user_data.get('ctrl_pcm_jdml')}\n"
            f"*Controlador Los Cortijos:* {context.user_data.get('ctrl_cortijos_jdml')}"
        )
    else:
        jdml_seccion = (
            f"🛡️ *EMPRESA JDML*\n"
            f"*Coordinador:* {context.user_data.get('coord_jdml')}\n"
            f"*Transporte:* {context.user_data.get('transporte_jdml')}\n"
            f"*Quinta Fides:* {context.user_data.get('quinta_jdml')}"
        )

    # Construir CSP 24/7 según tipo de guardia (Nombres al lado de la posición)
    if tipo_guardia == "Diurna":
        csp_seccion = (
            f"🛡️ *EMPRESA CSP 24/7*\n"
            f"*Piso 4:* {context.user_data.get('piso4_csp')}\n"
            f"*Emergencia:* {context.user_data.get('emergencia_csp')}\n"
            f"*Revisión:* {context.user_data.get('revision_csp')}\n"
            f"*Sótano 5:* {context.user_data.get('sotano5_csp')}"
        )
    else:
        csp_seccion = (
            f"🛡️ *EMPRESA CSP 24/7*\n"
            f"*Revisión:* {context.user_data.get('revision_csp')}\n"
            f"*Sótano 5:* {context.user_data.get('sotano5_csp')}"
        )

    texto_reporte = (
        f"{saludo}\n"
        f"*Reporte de Servicio*\n"
        f"*Plantilla de Guardia {tipo_guardia}*\n"
        f"{fecha_str}\n\n"
        f"🛡️ *SEGURIDAD INTERNA PCM*\n"
        f"{pcm_seccion}\n\n"
        f"{jdml_seccion}\n\n"
        f"{csp_seccion}\n\n"
        f"*Novedades en Recepción:*\n{novedades}"
    )

    texto_encoded = urllib.parse.quote(texto_reporte)
    url_whatsapp = f"https://wa.me/?text={texto_encoded}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Compartir en WhatsApp", url=url_whatsapp)],
        [InlineKeyboardButton("Nuevo Reporte", callback_data="volver_menu")]
    ])

    await msg_obj.reply_text(f"📋 *REPORTE GENERADO:*\n\n{texto_reporte}", reply_markup=keyboard, parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Reporte de Plantilla cancelado.")
    return ConversationHandler.END

# Exportación del Handler
plantilla_handler = ConversationHandler(
    entry_points=[
        CommandHandler('plantilla', iniciar_plantilla),
        CallbackQueryHandler(iniciar_plantilla, pattern='^iniciar_plantilla$')
    ],
    states={
        TIPO_GUARDIA: [CallbackQueryHandler(seleccionar_tipo_guardia)],
        CANT_TITULARES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cant_titulares)],
        NOMBRES_TITULARES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre_titular)],
        CANT_ESPECIALES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cant_especiales)],
        NOMBRES_ESPECIALES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre_especial)],
        TIENE_LIBRES: [CallbackQueryHandler(respuesta_tiene_libres)],
        CANT_LIBRES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cant_libres)],
        NOMBRES_LIBRES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre_libre)],
        TIENE_AUSENTES: [CallbackQueryHandler(respuesta_tiene_ausentes)],
        CANT_AUSENTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cant_ausentes)],
        NOMBRES_AUSENTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre_ausente)],
        TIENE_VACACIONES: [CallbackQueryHandler(respuesta_tiene_vacaciones)],
        CANT_VACACIONES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cant_vacaciones)],
        NOMBRES_VACACIONES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre_vacacion)],
        COORD_JDML: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_coord_jdml)],
        POS_TRANSPORTE_JDML: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_transporte_jdml)],
        POS_PROVEEDORES_JDML: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_proveedores_jdml)],
        POS_QUINTA_JDML: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_quinta_jdml)],
        POS_PISO2_JDML: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_piso2_jdml)],
        POS_CTRL_PCM_JDML: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ctrl_pcm_jdml)],
        POS_CTRL_CORTIJOS_JDML: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ctrl_cortijos_jdml)],
        POS_PISO4_CSP: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_piso4_csp)],
        POS_EMERGENCIA_CSP: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_emergencia_csp)],
        POS_REVISION_CSP: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_revision_csp)],
        POS_SOTANO5_CSP: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_novedades_plantilla)],
        NOVEDADES: [
            CallbackQueryHandler(generar_reporte_plantilla),
            MessageHandler(filters.TEXT & ~filters.COMMAND, generar_reporte_plantilla)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
