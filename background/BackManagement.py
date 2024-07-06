import chainlit as cl
from openai import AsyncOpenAI
from config import AUTH_KEY,Address
from typing import Dict, Optional

@cl.oauth_callback
def oauth_callback(
  provider_id: str,
  token: str,
  raw_user_data: Dict[str, str],
  default_user: cl.User,
) -> Optional[cl.User]:
  return default_user


client = AsyncOpenAI(api_key=AUTH_KEY, base_url=f"{Address}/v1")

settings = {
    "model": "suno-v3",
}

@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="suno-v3",
            markdown_description="Suno-v3 can be generate 2~3 min music.",
            icon="https://picsum.photos/200",
        ),
        cl.ChatProfile(
            name="suno-v3.5",
            markdown_description="Suno-v3 can be generate 3~5 min music.",
            icon="https://picsum.photos/250",
        ),
    ]

@cl.on_chat_start
async def start_chat():
    chat_profile = cl.user_session.get("chat_profile")
    await cl.Message(
        content=f"starting chat using the {chat_profile} chat profile"
    ).send()

    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": "You are a helpful assistant."}],
    )
    settings = {
        "model" : f"{chat_profile}"
    }
    print(settings)

@cl.on_message
async def main(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()

if __name__ == "__main__":
    cl.run()
