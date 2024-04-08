from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 設定 Line Bot 的 Channel Access Token 和 Channel Secret
line_bot_api = LineBotApi('Xt+M0+Zmy5qApFNFOPdyEFiMGUEFzKJotAr1lqLMiEO/JciPn9QFcvhfJIavvo2h0gpQEfX9Fh+l3Us+WTjzQiQP/wAS47Vv0k+79Yb87FvZeMZnCeyPSl5g0uWVRbEFpmu+/7aUAUMOgCS1PUlJqgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('6b58c64686c1ccfef156a6de588d2aac')

# 定義 Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 處理收到的文字消息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    reply_text = f"你說了：{text}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run()
