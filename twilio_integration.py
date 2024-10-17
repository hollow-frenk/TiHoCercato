from twilio.rest import Client
import db
import bot_handlers

# Twilio credenziali
account_sid = 'YOUR_TWILIO_SID'
auth_token = 'YOUR_TWILIO_AUTH_TOKEN'
client = Client(account_sid, auth_token)

# Gestione chiamate reindirizzate
def handle_incoming_call(call_data):
    call_sid = call_data['CallSid']
    from_number = call_data['From']
    to_number = call_data['To']
    call_status = call_data['CallStatus']

    # Trova l'utente che ha registrato il numero Twilio
    user_id = db.find_user_by_phone(to_number)

    # Se la chiamata è terminata e non c'è risposta, invia una notifica di chiamata persa
    if call_status == "completed":
        bot_handlers.notify_missed_call(user_id, from_number)

    # Se la chiamata è una segreteria, salva il messaggio vocale
    if 'RecordingUrl' in call_data:
        voicemail_url = call_data['RecordingUrl']
        bot_handlers.notify_missed_call(user_id, from_number, voicemail_url)