from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import paho.mqtt.client as mqtt
import logging

# 設置日誌級別為 DEBUG，可以輸出所有日誌訊息
logging.basicConfig(level=logging.DEBUG)

# 使用 logger 物件來進行日誌紀錄
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 設定 Line Bot 的 Channel Access Token 和 Channel Secret
CHANNEL_ACCESS_TOKEN = 'Xt+M0+Zmy5qApFNFOPdyEFiMGUEFzKJotAr1lqLMiEO/JciPn9QFcvhfJIavvo2h0gpQEfX9Fh+l3Us+WTjzQiQP/wAS47Vv0k+79Yb87FvZeMZnCeyPSl5g0uWVRbEFpmu+/7aUAUMOgCS1PUlJqgdB04t89/1O/w1cDnyilFU='
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler('6b58c64686c1ccfef156a6de588d2aac')

# # MQTT 設定
MQTT_BROKER = "mqtt://mqtt-dashboard.com"
MQTT_TOPIC = "TestMQTT_microbit"

# 連接到 MQTT 服務器時將執行的回調函數
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # 訂閱可以在 on_connet 中設置，如果連接丟失
    # 或重連會重新訂閱
    client.subscribe(MQTT_TOPIC)

# 定義 MQTT 訂閱處理函數
def on_message(client, userdata, message):
    mqtt_message = message.payload.decode('utf-8')
    user_id = 'U0cde5459f527d6da0736b2a0181426d1'  # 請替換成您的 Line 使用者 ID
    send_mqtttoline(mqtt_message)  # 发送消息到Line

# 发送消息到Line
def send_mqtttoline(message):
    try:
        line_bot_api.push_message('U0cde5459f527d6da0736b2a0181426d1', TextSendMessage(text=message))
    except Exception as e:
        print("Failed to send message to Line:", e)

# 創建 MQTT 客戶端
mqtt_client = mqtt.Client()
  # 或者使用 MQTTv5


# 設置連接後的回調函數
mqtt_client.on_connect = on_connect

# 設置 MQTT 訂閱處理函數
mqtt_client.on_message = on_message

# 連接到 MQTT 代理
mqtt_client.connect(MQTT_BROKER)

# 訂閱 MQTT 主題
mqtt_client.subscribe(MQTT_TOPIC)

# 開始循環處理訊息
mqtt_client.loop_forever()

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
    user_message = event.message.text
    reply_token = event.reply_token
    user_id = event.source.user_id
    logger.info(user_id)

    send_line_message(user_id)

    if '房東' in user_message:
        push_line_bot_message('房東電話:0921836335', reply_token)
    elif any(keyword in user_message for keyword in ['熱水器', '水管', '冷氣', '抽風扇', '冰箱']):
        push_line_bot_message('水電宅修(林育成)電話:02 2621 2095', reply_token)
    elif any(keyword in user_message for keyword in ['網路', '電視']):
        push_line_bot_message('台灣大寬平客服:02 4066 5357', reply_token)
    elif any(keyword in user_message for keyword in ['包裹', '掛號', '信件']):
        push_line_bot_message('請至一樓找管理室洽詢~', reply_token)
    elif any(keyword in user_message for keyword in ['id']):
        push_line_bot_message(user_id, reply_token)
    elif '開燈' in user_message:
        send_mqtt_command_to_broker('on')
        push_line_bot_message('已開', reply_token)
    elif '關燈' in user_message:
        send_mqtt_command_to_broker('off')
        push_line_bot_message('已關', reply_token)
    elif '圖片' in user_message:
        bucket_name = 'test0221'
        image_name = 'images.jpg'
        image_url = get_image_url(bucket_name, image_name)
        reply_image(reply_token, image_url)
    else:
        push_line_bot_message('很抱歉我無法解決您的問題，您可以連絡房東:0921836335', reply_token)

    return 'OK'

def push_line_bot_message(message, reply_token):
    line_payload = {
        'replyToken': reply_token,
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }

    line_options = {
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + CHANNEL_ACCESS_TOKEN
        },
        'json': line_payload
    }

    requests.post('https://api.line.me/v2/bot/message/reply', **line_options)

def send_line_message(user_id):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + CHANNEL_ACCESS_TOKEN
    }
    message = {
        'to': user_id,
        'messages': [
            {
                'type': 'text',
                'text': '這是一條主動發送的消息。'
            }
        ]
    }

    options = {
        'headers': headers,
        'json': message
    }

    requests.post(url, **options)

def send_mqtt_command_to_broker(mqtt_command):
    url = 'https://coffee-lbm2dvajia-de.a.run.app'
    line_options = {
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + CHANNEL_ACCESS_TOKEN
        },
        'json': {'command': mqtt_command}
    }

    try:
        response = requests.post(url, **line_options)
        print('MQTT Command sent:', response.json())
    except Exception as e:
        print('Error sending MQTT command:', e)


def send_line(payload):
    url = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + CHANNEL_ACCESS_TOKEN
    }

    options = {
        'method': 'post',
        'headers': headers,
        'json': payload
    }

    requests.post(url, **options)

def reply_image(reply_token, image_url):
    payload = {
        'replyToken': reply_token,
        'messages': [
            {
                'type': 'image',
                'originalContentUrl': image_url,
                'previewImageUrl': image_url
            }
        ]
    }

    send_line(payload)

def get_image_url(bucket_name, image_name):
    return f'https://storage.googleapis.com/{bucket_name}/{image_name}'




if __name__ == "__main__":
    app.run()


