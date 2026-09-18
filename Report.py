import os
import logging
from datetime import datetime
import urllib.parse
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()

# Configuración de logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Estados de la conversación
CAJAS, GESTION_PAGO, SEGURIDAD, POLICIA, NOVEDADES = range(5)

# Datos persistentes en memoria (listas Maestras de personal y cajas)
LISTA_CAJAS = ["Gestión de Pago", "Cardio Pulmonar", "Farmacia", "Emergencia", "Laboratorio S2", "Hemodinamia"]
PERSONAL_PAGO = ["Luis Rodríguez", "María Delgado", "Pedro Gómez"]
PERSONAL_SEGURIDAD = ["Carlos Mendoza", "Juan Pérez", "Ana Martínez"]

DÍAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def obtener_saludo_y_fecha():
    ahora = datetime.now()
    hora = ahora.hour
    if 5 <= hora < 12:
        saludo = "Buenos días."
    elif 12 <= hora < 19:
        saludo = "Buenas tardes."
    else:
        saludo = "Buenas noches."
    
    dia_nombre = DÍAS[ahora.weekday()]
    mes_nombre = MESES[ahora.month - 1]
    fecha_str = f"{dia_nombre}, {ahora.day} de {mes_nombre}"
    return saludo, fecha_str

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cajas_sel'] = []
    keyboard = []
    for caja in LISTA_CAJAS:
        keyboard.append([InlineKeyboardButton(f"⬜ {caja}", callback_data=f"caja_{caja}")])
    keyboard.append([InlineKeyboardButton("➡️ Continuar", callback_data="cajas_done")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🏦 *TRASLADO DE VALORES*\nSeleccione las cajas de origen:", reply_markup=reply_markup, parse_mode="Markdown")
    return CAJAS

async def seleccionar_cajas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("caja_"):
        caja = data.replace("caja_", "")
        cajas_sel = context.user_data.get('cajas_sel', [])
        if caja in cajas_sel:
            cajas_sel.remove(caja)
        else:
            cajas_sel.append(caja)
        context.user_data['cajas_sel'] = cajas_sel

        keyboard = []
        for c in LISTA_CAJAS:
            marcado = "✅" if c in cajas_sel else "⬜"
            keyboard.append([InlineKeyboardButton(f"{marcado} {c}", callback_data=f"caja_{c}")])
        keyboard.append([InlineKeyboardButton("➡️ Continuar", callback_data="cajas_done")])
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return CAJAS

    elif data == "cajas_done":
        if not context.user_data.get('cajas_sel'):
            await query.answer("Debe seleccionar al menos una caja.", show_alert=True)
            return CAJAS

        keyboard = [[InlineKeyboardButton(p, callback_data=f"pago_{p}")] for p in PERSONAL_PAGO]
        keyboard.append([InlineKeyboardButton("➕ Agregar nuevo personal", callback_data="pago_nuevo")])
        await query.message.reply_text("👤 *Personal de Gestión de Pago:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return GESTION_PAGO

async def pedir_gestion_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "pago_nuevo":
        context.user_data['esperando_nuevo'] = 'pago'
        await query.message.reply_text("Escriba el Nombre y Apellido del nuevo personal de Gestión de Pago:")
        return GESTION_PAGO
    else:
        context.user_data['personal_pago'] = data.replace("pago_", "")
        return await mostrar_menu_seguridad(query.message)

async def guardar_nuevo_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nuevo_nombre = update.message.text.strip()
    tipo = context.user_data.get('esperando_nuevo')

    if tipo == 'pago':
        PERSONAL_PAGO.append(nuevo_nombre)
        context.user_data['personal_pago'] = nuevo_nombre
        return await mostrar_menu_seguridad(update.message)
    elif tipo == 'seguridad':
        PERSONAL_SEGURIDAD.append(nuevo_nombre)
        context.user_data['personal_seguridad'] = nuevo_nombre
        return await pedir_policia(update.message)

async def mostrar_menu_seguridad(message):
    keyboard = [[InlineKeyboardButton(s, callback_data=f"seg_{s}")] for s in PERSONAL_SEGURIDAD]
    keyboard.append([InlineKeyboardButton("➕ Agregar nuevo oficial", callback_data="seg_nuevo")])
    await message.reply_text("🛡️ *Personal de Seguridad Integral:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return SEGURIDAD

async def pedir_seguridad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "seg_nuevo":
        context.user_data['esperando_nuevo'] = 'seguridad'
        await query.message.reply_text("Escriba el Nombre y Apellido del nuevo oficial de Seguridad:")
        return SEGURIDAD
    else:
        context.user_data['personal_seguridad'] = data.replace("seg_", "")
        return await pedir_policia_query(query)

async def pedir_policia_query(query):
    keyboard = [
        [InlineKeyboardButton("Sí, con presencia policial", callback_data="policia_Sí")],
        [InlineKeyboardButton("No, solo personal interno", callback_data="policia_No")]
    ]
    await query.message.reply_text("🚓 *¿Contó con la presencia de la Policía en la clínica?*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return POLICIA

async def pedir_policia(message):
    keyboard = [
        [InlineKeyboardButton("Sí, con presencia policial", callback_data="policia_Sí")],
        [InlineKeyboardButton("No, solo personal interno", callback_data="policia_No")]
    ]
    await message.reply_text("🚓 *¿Contó con la presencia de la Policía en la clínica?*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return POLICIA

async def pedir_novedades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['policia'] = query.data.replace("policia_", "")

    keyboard = [
        [InlineKeyboardButton("Sin novedades / Procedimiento exitoso", callback_data="nov_Sin novedades")],
        [InlineKeyboardButton("Registrar Novedad", callback_data="nov_registrar")]
    ]
    await query.message.reply_text("📝 *¿Ocurrió alguna novedad durante el acompañamiento?*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return NOVEDADES

async def generar_reporte_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    cajas_str = ", ".join(context.user_data['cajas_sel'])

    # Formato final del reporte
    texto_reporte = (
        f"{saludo}\n\n"
        f"🏦 *TRASLADO DE VALORES*\n"
        f"📅 *{fecha_str}*\n\n"
        f"📍 *Cajas Procesadas:* {cajas_str}\n"
        f"👤 *Personal de Gestión de Pago:* {context.user_data['personal_pago']}\n"
        f"🛡️ *Personal de Seguridad Integral:* {context.user_data['personal_seguridad']}\n"
        f"🚓 *Presencia Policial en Clínica:* {context.user_data['policia']}\n"
        f"📝 *Novedades:* {novedades}"
    )

    # Generación de la URL de WhatsApp (Deep Link)
    texto_para_whatsapp = texto_reporte.replace('*', '')
    texto_encoded = urllib.parse.quote(texto_para_whatsapp)
    url_whatsapp = f"https://wa.me/?text={texto_encoded}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 Compartir en WhatsApp", url=url_whatsapp)]
    ])

    await msg_obj.reply_text(f"📋 *REPORTE GENERADO:*\n\n{texto_reporte}", reply_markup=keyboard, parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Reporte cancelado.")
    return ConversationHandler.END

if __name__ == '__main__':
    # Obtiene el Token desde las variables de entorno
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TOKEN:
        raise ValueError("Error: La variable de entorno TELEGRAM_TOKEN no está configurada.")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('reporte', start)],
        states={
            CAJAS: [CallbackQueryHandler(seleccionar_cajas)],
            GESTION_PAGO: [
                CallbackQueryHandler(pedir_gestion_pago),
                MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_nuevo_nombre)
            ],
            SEGURIDAD: [
                CallbackQueryHandler(pedir_seguridad),
                MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_nuevo_nombre)
            ],
            POLICIA: [CallbackQueryHandler(pedir_novedades)],
            NOVEDADES: [
                CallbackQueryHandler(generar_reporte_final),
                MessageHandler(filters.TEXT & ~filters.COMMAND, generar_reporte_final)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    print("Bot @ReportPcmBot en marcha...")
    app.run_polling()
