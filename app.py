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
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    UnsendEvent,
    TextMessageContent
)

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file credentials.json.
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = "1jXOboYVudQq55lvhNRlwp0RuGnY05SPYUHza4tGWXJc"
RANGE_NAME = "Sheet1!A2:C"

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

def get_values():
    
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    try:
        service = build("sheets", "v4", credentials=creds)

        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=SPREADSHEET_ID,
                 range=RANGE_NAME)
            .execute()
        )
        rows = result.get("values", [])
        return {
            "row_count": len(rows),
            "cell_value": rows[len(rows)-1][2]
        }
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def append_values(values):

    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    try:
        service = build("sheets", "v4", credentials=creds)

        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        print(f"{(result.get('updates').get('updatedCells'))} cells appended.")
        return result

    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

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
        append_values([[event.source.user_id, event.message.id, event.message.text]])
        result = get_values()
        append_values([[event.source.user_id, event.message.id, f"{result["row_count"]} rows and the message is {result["cell_value"]}"]])
        
@handler.add(UnsendEvent)
def handle_unsend(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
    if event.type == "unsend":
        append_values([[event.source.user_id, event.unsend.message_id, "Unsend Event"]])
        line_bot_api.push_message_with_http_info(
            PushMessageRequest(
                to=event.source.group_id,
                messages=[TextMessage(text="還敢收回啊？")]
            )
        )
        
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)