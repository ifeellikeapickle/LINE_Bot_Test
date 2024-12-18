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
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

app = Flask(__name__)

# Load .env file
load_dotenv()

channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("CHANNEL_SECRET")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)


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
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

    if re.search(regex, event.message.text):
        custom_text = (
            # "請勿哈囉！\n"
            # "event.type = " + event.type + "\n"
            # "event.source.type = " + event.source.type + "\n"
            # "event.source.user_id = " + event.source.user_id + "\n"
            # "event.timestamp = " + event.timestamp + "\n"
            # "event.mode = " + event.mode + "\n"
            # "event.webhook_event_id = " + event.webhook_event_id + "\n"
            # "event.delivery_context.is_redelivery = " + event.delivery_context.is_redelivery + "\n"
            # "event.message.type = " + event.message.type + "\n"
            # "event.message.id = " + event.message.id + "\n"
            # "event.message.text = " + event.message.text + "\n"
            # "event.message.mention.mentionees = " + event.message.mention.mentionees + "\n"
            # "event.message.quote_token = " + event.message.quote_token + "\n"
            # "event.message.quoted_message_id = " + event.message.quoted_message_id + "\n"
            f"請勿哈囉！\n"
            f"event.type = {event.type}\n"
            f"event.source.type = {event.source.type}\n"
            f"event.source.user_id = {event.source.user_id}\n"
            f"event.timestamp = {event.timestamp}\n"
            f"event.mode = {event.mode}\n"
            f"event.webhook_event_id = {event.webhook_event_id}\n"
            f"event.delivery_context.is_redelivery = {event.delivery_context.is_redelivery}\n"
            f"event.message.type = {event.message.type}\n"
            f"event.message.id = {event.message.id}\n"
            f"event.message.text = {event.message.text}\n"
            f"event.message.mention.mentionees = {event.message.mention.mentionees}\n"
            f"event.message.quote_token = {event.message.quote_token}\n"
            f"event.message.quoted_message_id = {event.message.quoted_message_id}\n"
        )
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=custom_text)],
                notification_disabled=True
            )
        )
    else:
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.source.user_id)]
            )
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)