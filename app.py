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
    TextMessage,
    StickerMessage,
    ImageMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    UnsendEvent,
    TextMessageContent,
    StickerMessageContent,
    ImageMessageContent
)

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

MAX_MESSAGE_LENGTH = 5

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
            f"event.type = {event.type}\n"
            f"event.source.type = {event.source.type}\n"
            # f"event.source.user_id = {event.source.user_id}\n"
            # f"event.timestamp = {event.timestamp}\n"
            # f"event.mode = {event.mode}\n"
            # f"event.webhook_event_id = {event.webhook_event_id}\n"
            # f"event.delivery_context.is_redelivery = {event.delivery_context.is_redelivery}\n"
            f"event.message.type = {event.message.type}\n"
            # f"event.message.id = {event.message.id}\n"
            f"event.message.text = {event.message.text}\n"
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
    elif "標記" in event.message.text:
        mentionees_list = event.message.mention.mentionees
        for mentionee in mentionees_list:
            if mentionee.type == "all":
                pass
            elif mentionee.type == "user":
                if mentionee.user_id == "Ua385cbcb21b1c8e5b462b05e17984751":
                    line_bot_api.reply_message_with_http_info(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text="YES")],
                            notification_disabled=True
                        )
                    )
                    break
                else:
                    pass
            else:
                pass
    elif "無人" in event.message.text:
        if event.message.mention is None:
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="No one is tagged.")],
                    notification_disabled=True
                )
            )
    else:
        # Push the first default message to the database
        while messages_ref.get() is None:
            messages_ref.push({
                "order": 0,
                "user_id": "UID",
                "message_id": "MID",
                "message_text": "Message Text"
            })
            
        # Variable latest_message is a dictionary
        latest_message = messages_ref.order_by_key().limit_to_last(1).get()
        for key in latest_message:
            order = messages_ref.child(key).child("order").get() - 1
        
        # Push the current message to the database
        messages_ref.push({
            "order": order,
            "user_id": event.source.user_id,
            "message_id": event.message.id,
            "message_text": event.message.text
        })
        
        # Delete the oldest message in the database
        if len(messages_ref.get()) > MAX_MESSAGE_LENGTH:
            # Variable oldest_message is a dictionary
            oldest_message = messages_ref.order_by_key().limit_to_first(1).get()
            for key in oldest_message:
                messages_ref.child(key).delete()

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
    
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
    line_bot_api.reply_message_with_http_info(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(
                text=f"{event.message.content_provider.type}, {event.message.content_provider.original_content_url}, {event.message.content_provider.preview_image_url}, {event.message.image_set.id}, {event.message.image_set.index}, {event.message.image_set.total}"
            )],
            notification_disabled=True
        )
    )

@handler.add(UnsendEvent)
def handle_unsend(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
    ordered_messages = messages_ref.order_by_child("order").get()
    for key in ordered_messages:
        if messages_ref.child(key).child("message_id").get() == event.unsend.message_id:
            unsend_message = messages_ref.child(key).child("message_text").get()
            line_bot_api.push_message_with_http_info(
                PushMessageRequest(
                    to=event.source.group_id,
                    messages=[TextMessage(
                        text=f"你是不是想要說：「{unsend_message}」"
                    )]
                )
            )
        else:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)