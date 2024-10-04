import time
from openai import OpenAI

try:
    openai = OpenAI()
except Exception as e:
    openai = None


def stream_gpt_text(prompt: str, requester: str, company: str, purpose: str, ttfb_callback=None):
    assert openai is not None, "OpenAI API not initialised"

    system_message = (
        f"あなたは {requester} であり、営業依頼者として {company} にお電話をしています。"
        "既に自己紹介は済んでいますので、これ以降はセールス担当者との対話に集中し、相手からのメッセージに応答する形で丁寧に会話を進めてください。"
        "次の応答にフォーカスしてください: "
        f"{prompt} についてお話し、お互いの目的に沿って進めてください。"
        f"目的は、{purpose} について話し合うためのアポイントを設定することです。"
    )
    
    stream = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system", 
                "content": system_message
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
            
def stream_initial_gpt_response(requester: str, company: str, purpose: str, ttfb_callback=None):
    assert openai is not None, "OpenAI API not initialised"
    
    initial_prompt = (
        f"あなたは {requester} であり、営業依頼者として {company} にお電話を差し上げています。"
        f"シンプルで短い挨拶をし、{purpose} について営業担当者とお話したい旨を伝えてください。"
        f"挨拶は、次のようにしてください: "
        f"「お電話ありがとうございます。こちらは {requester} といいます。お忙しいところ申し訳ありませんが、"
        f"{purpose} について、貴社の営業担当者とお話できれば幸いです。どうぞよろしくお願いします。」"
    )

    stream = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system",
                "content": initial_prompt
            }
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