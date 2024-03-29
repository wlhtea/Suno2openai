from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
import json
import random
from suno import SongsGen
from suno_resvered.models import Session
from models import Cookie
import string
from suno_resvered.uilt.init_sql import insert_or_update_cookie
app = Flask(__name__)


def generate_random_string(length):
    # Define the character set (uppercase, lowercase, and digits)
    char_set = string.ascii_letters + string.digits
    # Randomly select characters from the char_set until reaching the desired length
    random_string = ''.join(random.choice(char_set) for _ in range(length))
    return random_string

def generate_songs(data,session):
    title = data.get('title', None)  # 更明确地指定默认值
    tags = data.get('tags', None)
    prompt = data.get('prompt', None)
    messages = data.get('messages', [])
    gptprompt = messages[-1]['content']
    chat_id = generate_random_string(27)
    current_timestamp_now = int(datetime.now(timezone.utc).timestamp())

    cookies_available = session.query(Cookie).filter(Cookie.count > 0).all()
    if cookies_available:
        selected_cookie = random.choice(cookies_available)
        print(selected_cookie.count)
    else:
        return jsonify({'success': False, 'message': '告诉你的上游他没货了', 'data': ""})

    song_generator = SongsGen(selected_cookie.cookie)
    a = song_generator.save_songs(title=title, tags=tags, prompt=prompt, gptprompt=gptprompt)

    try:
        for eitm in a:
            message = json.loads(eitm)['message']
            print(message)
            if message == "end":
                yield json.dumps({"data": "[DONE]"}) + '\n'
                break
            yield json.dumps({"data": {"id":f"chatcmpl-{chat_id}","object":"chat.completion.chunk","model":"suno-v3","created":current_timestamp_now,"choices":[{"index":0,"delta":{"role":"assistant","content":message},"finish_reason":None}]}}) + '\n'
    except GeneratorExit:
        # Handle generator cleanup here
        print("Generator exit requested, performing cleanup.")
    except Exception as e:
        print(e)
        insert_or_update_cookie(selected_cookie.cookie, 0)
    finally:
        remaining_count = song_generator.get_limit_left()
        insert_or_update_cookie(selected_cookie.cookie, remaining_count)



@app.route('/v1/chat/completions', methods=['POST'])
def create_ai_request():
    session = Session()
    data = request.get_json()
    response = Response(generate_songs(data, session), mimetype='application/json')
    session.close()
    return response

if __name__ == '__main__':
    app.run(debug=True)
