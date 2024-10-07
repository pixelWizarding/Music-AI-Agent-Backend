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
        "相手が最終的な結論に達した場合、それを認識し、会話をまとめて終了してください。"
        f"目的は、{purpose} について話し合うためのアポイントを設定することです。"
        "相手が必要な情報（例：日程や時間）を提供した場合、それを認識し、繰り返して尋ねることは避けてください。"
        "相手からの提案や回答を丁寧に確認し、正しい内容であれば了承して次に進むか、会話をまとめて終了してください。"
        "応答は簡潔で明確にし、繰り返しの質問や不必要な内容の話を避け、無駄に会話を長引かせないようにしてください。"
        "また、会話が結論に達した場合は、迅速に丁寧に会話を締めくくってください。"
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

def analyze_response(text: str):
    assert openai is not None, "OpenAI API not initialized"
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system", 
                "content": (
                    "Analyze the provided text in detail and extract the call result. "
                    "If you think that appointment secure, return the result in the format: '1'. "
                    "If not, return: '2'. Only provide the data in these two cases."
                )
            },
            {"role": "user", "content": text}
        ],
    )
    
    return response.choices[0].message.content