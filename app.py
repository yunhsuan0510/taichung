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

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text

    if user_input == "美食" or user_input == "景點":
        # 根據使用者選擇的區域和需求進行下一步處理
        region = event.source.user_id  # 使用者的ID來保存區域選擇
        query = f"{region}{user_input}"
        google_maps_url = f"https://www.google.com/maps/search/台中{query}"
        reply_message = TextSendMessage(text=f"點擊以下鏈接查看結果: {google_maps_url}")
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
        # 保存區域選擇到使用者ID (這裡應該是儲存在某個持久化存儲中)
        # 此處為簡化，直接使用變數保存，實際應用中需要考慮保存和檢索
        event.source.user_id = region

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
