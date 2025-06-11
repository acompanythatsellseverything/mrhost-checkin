from twilio.rest import Client

account_sid = 'your_account_sid'
auth_token = 'your_auth_token'

client = Client(account_sid, auth_token)

from_whatsapp_number = 'whatsapp:+14155238886'
to_whatsapp_number = 'whatsapp:+YOUR_NUMBER'

message = client.messages.create(
    body='Hello from Python via Twilio WhatsApp API!',
    from_=from_whatsapp_number,
    to=to_whatsapp_number
)

print('Message sent! SID:', message.sid)