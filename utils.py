from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Invia le istruzioni per la deviazione delle chiamate
def send_call_forwarding_instructions(bot, chat_id):
    message = "Per attivare il servizio di deviazione chiamate, inserisci uno di questi codici:"
    keyboard = InlineKeyboardMarkup()

    buttons = [
        InlineKeyboardButton("Deviazione chiamate quando occupato", callback_data='code_busy'),
        InlineKeyboardButton("Deviazione chiamate quando non rispondi", callback_data='code_no_answer'),
    ]

    keyboard.add(*buttons)
    bot.send_message(chat_id, message,)