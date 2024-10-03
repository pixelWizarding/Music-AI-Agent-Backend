import time
from openai import OpenAI

try:
    openai = OpenAI()
except Exception as e:
    openai = None

def stream_gpt_text(prompt, ttfb_callback=None):
    assert openai is not None, "OpenAI API not initialised"
    
    stream = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system", 
                "content": "あなたはABC株式会社田中であり、営業の依頼者として電話をかける役割を担っています。日本語で敬語を使って、相手企業のオペレータが電話に出たときは電話の目的を丁寧にお伝えください。相手の都合を確認しながら、目的に沿ってアポイントを確実に設定することを目指してください。必ず電話でのリアルタイム会話であることを意識し、文章ではなく自然な対話の流れで話を進めてください。"
            },
            {"role": "user", "content": prompt}
        ],
        stream=True,
    )
    
    is_first_chunk = True
    start_time = int(time.time() * 1000)
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end='') 
            if is_first_chunk:
                is_first_chunk = False
                if ttfb_callback:
                    end_time = int(time.time() * 1000)
                    ttfb_callback(end_time - start_time)
            
            yield chunk.choices[0].delta.content
    