from flask import Flask, request, abort
import os
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# 監聽所有來自 /callback 的 Post Request
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
        abort(400)
    return 'OK'

# 全局變數來保存用戶的區域選擇
user_region = {}

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text

    if user_input == "美食" or user_input == "景點":
        # 根據用戶之前選擇的區域進行下一步處理
        region = user_region.get(user_id)
        if region:
            query = f"台中市{region}{user_input}"
            google_maps_url = f"https://www.google.com/maps/search/{query}"
            reply_message = TextSendMessage(text=f"點擊以下鏈接查看結果: {google_maps_url}")
            line_bot_api.reply_message(event.reply_token, reply_message)
        else:
            reply_message = TextSendMessage(text="請先選擇您的所在區域")
            line_bot_api.reply_message(event.reply_token, reply_message)
    else:
        # 問使用者所在的區域
        reply_message = TemplateSendMessage(
            alt_text='請選擇區域',
            template=ButtonsTemplate(
                title='請選擇您的所在區域',
                text='請選擇您所在的台中市區域',
                actions=[
                    PostbackAction(label='南區', data='region=南區'),
                    PostbackAction(label='北區', data='region=北區'),
                    PostbackAction(label='東區', data='region=東區'),
                    PostbackAction(label='西區', data='region=西區')
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, reply_message)

@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data

    if data.startswith('region='):
        region = data.split('=')[1]
        user_id = event.source.user_id
        user_region[user_id] = region

        reply_message = TemplateSendMessage(
            alt_text='請選擇類別',
            template=ButtonsTemplate(
                title='請選擇類別',
                text='請選擇您要找的是美食還是景點',
                actions=[
                    MessageAction(label='美食', text='美食'),
                    MessageAction(label='景點', text='景點')
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, reply_message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
