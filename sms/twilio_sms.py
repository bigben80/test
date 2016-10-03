from twilio.rest import TwilioRestClient

# To find these visit https://www.twilio.com/user/account
ACCOUNT_SID = "AC3a23436f2ab5f9a0615c50d136c9aad9"
AUTH_TOKEN = "d30b5a3d12b8b621a12edc0217dc5982"

client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

message = client.messages.create(
    body="This is a message sent from python client!",  # Message body, if any
    to="+46763359899",
    from_="+46769447309",
)
print message.sid
