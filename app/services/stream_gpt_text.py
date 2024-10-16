import time
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()


try:
    openai = OpenAI()
    openai.api_key = os.getenv("OPENAI_API_KEY")
except Exception as e:
    openai = None
    print(f"Error initializing OpenAI: {e}")

def stream_gpt_text(prompt: str, requester: str, company: str, purpose: str, ttfb_callback=None, last_responses: list = None):
    """
    Streams GPT-4 response based on the prompt and the last responses from the receiver.
    Adjusts the system message based on the receiver's responses to keep the conversation natural.
    """
    
    assert openai is not None, "OpenAI API not initialized"

    # If last_responses are provided, add them to the system message for context
    if last_responses:
        conversation_history = '\n'.join([f"相手: {response}" for response in last_responses])
        history_context = f"以下は相手からの返答です:\n{conversation_history}\n\n"
    else:
        history_context = ""

    # System message with receiver's responses as context
    system_message = (
        f"{history_context}"
        f"あなたは {requester} であり、営業依頼者として {company} にお電話をしています。"
        "既に自己紹介は済んでいますので、これ以降はセールス担当者との対話に集中し、相手からのメッセージに応答する形で丁寧に会話を進めてください。"
        "次の応答にフォーカスしてください: "
        f"{prompt} についてお話し、お互いの目的に沿って進めてください。"
        "相手が最終的な結論に達した場合、それを認識し、会話をまとめて終了してください。"
        f"目的は、{purpose} について話し合うためのアポイントを設定することです。"
        "相手が必要な情報（例：日程や時間）を提供した場合、それを認識し、繰り返して尋ねることは避けてください。"
        "もし相手がすでに具体的な日程やその他の必要な情報を提供した場合、丁寧に会話を締めくくってください。"
        "質問を続ける必要がない場合、次に進むか、会話を終了してください。"
        "応答は簡潔で、正しい情報に基づいて対応してください。"
        "会話はシンプルかつ短く、60文字以内で返答してください。"
    )

    # Create a stream response from GPT-4
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
        max_tokens=80  # Limit the response length for brevity
    )

    # Handle time-to-first-byte and streaming response
    is_first_chunk = True
    start_time = int(time.time() * 2000)
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
        f"シンプルで短い挨拶をしてください。{purpose} について簡潔にお話したい旨を伝え、"
        f"以下のように挨拶してください: "
        f"「こちらは {requester} と申します。{purpose} についてお話ししたいと思います。よろしくお願いします。」"
        "挨拶は50文字以内で簡潔にしてください。"
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
        max_tokens=70
    )
    
    is_first_chunk = True
    start_time = int(time.time() * 2000)
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