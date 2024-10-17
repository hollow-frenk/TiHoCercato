from flask import Flask, request
import telebot
import twilio_integration
import bot_handlers

app = Flask(__name__)

# Inizializza il bot con il token
bot = telebot.TeleBot('YOUR_TELEGRAM_BOT_API_TOKEN')

# Definisci la route per il webhook di Telegram
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

# Definisci la route per le notifiche Twilio
@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    call_data = request.form
    twilio_integration.handle_incoming_call(call_data)
    return 'OK', 200

# Avvio del server Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)