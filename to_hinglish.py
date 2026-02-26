import json
import anthropic

client = anthropic.Anthropic()

with open("/Users/ankitgupta/Downloads/audio_timestamps.json") as f:
    words = json.load(f)

raw_words = " ".join(w["word"] for w in words)

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": f"""The following is a list of Hindi words in ITRANS/phonetic encoding.
Convert them into natural Hinglish — Hindi written in Roman script the way people casually type it (like WhatsApp messages).
Keep English words (like 'positive', 'negative', 'financial', 'lock', 'unexpected') as-is in English.
Output only the final readable Hinglish sentence/paragraph, nothing else.

Words: {raw_words}"""
        }
    ]
)

print(message.content[0].text)
