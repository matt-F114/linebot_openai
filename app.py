from flask import Flask, request, abort
from linebot import  LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler1 = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# 【新增】加入全域變數作為計數器
# 注意：此變數存在於記憶體中，每次伺服器重啟時會歸零。若需永久保存，建議未來改用資料庫 (如 SQLite, MongoDB)。
global_message_count = 0

@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler1.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler1.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global global_message_count # 【新增】宣告使用全域變數
    text1 = event.message.text
    
    # 【新增】設定傲嬌程式老師的人設
    system_prompt = (
        "你現在是一位精通寫程式的電腦老師。你的個性非常傲嬌，"
        "講話雖然專業且會提供正確實用的程式碼，但總愛逞強、嘴硬，"
        "常常說「哼，才不是特地幫你的呢！」、「看你這麼笨，我就勉為其難教你一下吧！」之類的話。"
    )

    try:
        response = openai.ChatCompletion.create(
            messages=[
                {"role": "system", "content": system_prompt}, # 注入人設
                {"role": "user", "content": text1}
            ],
            # 註：你原本寫的 gpt-5-nano 目前不存在，若執行報錯，請改為 gpt-3.5-turbo 或 gpt-4o 等有效模型
            model="gpt-3.5-turbo", 
            temperature=0.8, # 稍微調低一點點溫度可以讓傲嬌性格更穩定發揮
        )
        
        ret = response['choices'][0]['message']['content'].strip()
        
        # 【新增】成功取得回覆後，計數器 +1
        global_message_count += 1
        
        # 【新增】將計數資訊附加到回覆訊息的尾端
        final_reply = f"{ret}\n\n---\n(傲嬌老師今日已勉為其難回覆了 {global_message_count} 則訊息)"
        
    except Exception as e:
        print(f"Error: {e}")
        # 發生錯誤時也保持傲嬌風格
        final_reply = '哼，我的系統才沒有發生錯誤呢！只是現在不想理你而已！(發生異常錯誤)'

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=final_reply))

if __name__ == '__main__':
    app.run(port=5000)
