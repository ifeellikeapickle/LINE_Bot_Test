from flask import Flask, request, abort, jsonify
from dotenv import load_dotenv
import os
import re

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    ReplyMessageRequest,
    StickerMessage,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    UnsendEvent,
    StickerMessageContent,
    TextMessageContent
)

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

app = Flask(__name__)

# LINE Message API
load_dotenv()
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("CHANNEL_SECRET")
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# Fetch the service account key JSON file contents
cred = credentials.Certificate("serviceAccountKey_Test.json")

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://line-bot-test-4ae14-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

# As an admin, the app has access to read and write all data, regradless of Security Rules
messages_ref = db.reference("messages")

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@app.route("/get", methods=['GET'])
def get():
    # Retrieve query parameters
    param1 = request.args.get('param1', default='default_value')

    # Create a response
    response = {
        'message': 'GET method received!',
        'param1': param1
    }
    return jsonify(response)

keyword = "哈囉"
allowed_chars = r".*"
pattern = allowed_chars.join(keyword)
regex = rf"{pattern}"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
    if re.search(regex, event.message.text):
        custom_text = (
            f"還敢哈囉啊！\n"
            # f"event.type = {event.type}\n"
            # f"event.source.type = {event.source.type}\n"
            # f"event.source.user_id = {event.source.user_id}\n"
            # f"event.timestamp = {event.timestamp}\n"
            # f"event.mode = {event.mode}\n"
            # f"event.webhook_event_id = {event.webhook_event_id}\n"
            # f"event.delivery_context.is_redelivery = {event.delivery_context.is_redelivery}\n"
            # f"event.message.type = {event.message.type}\n"
            # f"event.message.id = {event.message.id}\n"
            # f"event.message.text = {event.message.text}\n"
            # f"event.message.mention.mentionees = {event.message.mention.mentionees}\n"
            # f"event.message.quote_token = {event.message.quote_token}\n"
            # f"event.message.quoted_message_id = {event.message.quoted_message_id}\n"
        )
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=custom_text)],
                notification_disabled=True
            )
        )
    else:
        while messages_ref.get() == None:
            messages_ref.push({
                "order": 5,
                "user_id": "UID",
                "message_id": "MID",
                "message_text": "Message Text"
            })
        if len(messages_ref.get()) >= 5:
            order = 5 - len(messages_ref.get())
            
            messages_ref.push({
                "order": order,
                "user_id": event.source.user_id,
                "message_id": event.message.id,
                "message_text": event.message.text
            })
            
            # Variable oldest_message is a dictionary
            oldest_message = messages_ref.order_by_key().limit_to_first(1).get()
            for key in oldest_message:
                messages_ref.child(key).delete()
        else:
            order = 5 - len(messages_ref.get())
            
            messages_ref.push({
                "order": order,
                "user_id": event.source.user_id,
                "message_id": event.message.id,
                "message_text": event.message.text
            })
            
@handler.add(MessageEvent, message=StickerMessageContent)
def handle_sticker_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
    line_bot_api.reply_message_with_http_info(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[StickerMessage(
                packageId="8515",
                stickerId="16581242"
            )],
            notification_disabled=True
        )
    )
    
@handler.add(UnsendEvent)
def handle_unsend(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
    all_messages = messages_ref.get()
    for key in all_messages:
        if messages_ref.child(key).child('message_id').get() == event.unsend.message_id:
            line_bot_api.push_message_with_http_info(
                PushMessageRequest(
                    to=event.source.group_id,
                    messages=[TextMessage(
                        text=f"你是不是想要說：「{messages_ref.child(key).child('message_text').get()}」"
                    )]
                )
            )
        else:
            pass
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)