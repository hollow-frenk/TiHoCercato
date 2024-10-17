import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import db
import google_contacts
import utils

# Inizializza il bot
bot = telebot.TeleBot('YOUR_TELEGRAM_BOT_API_TOKEN')


# Comando /start: salva il nome dell'utente e chiede il numero di telefono
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Ciao! Come ti chiami?")
    bot.register_next_step_handler(message, save_user_name)


def save_user_name(message):
    chat_id = message.chat.id
    name = message.text
    db.save_user_name(chat_id, name)
    bot.send_message(chat_id, f"Grazie {name}! Ora condividi il tuo numero di telefono.")

    # Mostra il pulsante per condividere il numero di telefono come InlineKeyboardButton
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text="Condividi il tuo numero", callback_data='share_contact')
    keyboard.add(button)
    bot.send_message(chat_id, "Premi il pulsante qui sotto per condividere il tuo numero", reply_markup=keyboard)


# Gestione della callback quando l'utente clicca sul bottone per condividere il contatto
@bot.callback_query_handler(func=lambda call: call.data == 'share_contact')
def handle_share_contact(call):
    chat_id = call.message.chat.id

    # Mostra il pulsante nativo per condividere il numero di telefono tramite KeyboardButton
    keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    contact_button = telebot.types.KeyboardButton(text="Condividi il tuo numero", request_contact=True)
    keyboard.add(contact_button)

    bot.send_message(chat_id, "Condividi il tuo numero toccando il pulsante", reply_markup=keyboard)


# Salva il numero di telefono dopo che l'utente lo condivide
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id
    phone_number = message.contact.phone_number
    db.save_user_phone(chat_id, phone_number)
    bot.send_message(chat_id, "Grazie! Ora configura la deviazione delle chiamate.")
    utils.send_call_forwarding_instructions(bot, chat_id)


# Notifica di chiamata persa o segreteria
def notify_missed_call(user_id, caller_number, voicemail_url=None):
    user_data = db.get_user_data(user_id)
    contact_name = google_contacts.get_contact_name(user_id, caller_number)

    if contact_name:
        msg = f"Ciao {user_data['name']}, hai ricevuto una chiamata da {contact_name}."
    else:
        msg = f"Ciao {user_data['name']}, hai ricevuto una chiamata da {caller_number}."

    if voicemail_url:
        msg += " Un messaggio in segreteria è stato lasciato."
        db.save_voicemail(user_id, voicemail_url)

    bot.send_message(user_id, msg)


# Gestione eliminazione di un messaggio vocale
@bot.message_handler(content_types=['voice'])
def handle_voice_message_deletion(message):
    if message.chat.type == 'private':
        db.delete_voicemail(message.voice.file_id)
        bot.send_message(message.chat.id, "Messaggio vocale eliminato.")