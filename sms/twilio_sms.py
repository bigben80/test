#!/usr/bin/env python
import argparse
from twilio.rest import TwilioRestClient

# To find these visit https://www.twilio.com/user/account
ACCOUNT_SID = "AC3a23436f2ab5f9a0615c50d136c9aad9"
AUTH_TOKEN = "d30b5a3d12b8b621a12edc0217dc5982"
FROM_SERVICE_NUMBER = "+46769447309"

def main(target_mobile, message_body):


    client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

    message = client.messages.create(
        body=message_body,  # Message body, if any
        to=target_mobile,
        from_=FROM_SERVICE_NUMBER,
    )
    print message.sid


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Send SMS message to specified mobile number')
    parser.add_argument(
        'target_mobile',
        help='the mobile number you want send SMS to')
    parser.add_argument(
        'message_body',
        help='the SMS message body')
    args = parser.parse_args()

    main(args.target_mobile, args.message_body)

