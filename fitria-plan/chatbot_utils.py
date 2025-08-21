import openai
import os

# Set API key dari OpenRouter
openai.api_key = "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"
openai.api_base = "https://openrouter.ai/api/v1"

def brainstorm_content(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="openrouter/anthropic/claude-3.5-sonnet",  # atau pilih model lain
        messages=[
            {"role": "system", "content": "Kamu adalah asisten kreatif yang membantu membuat ide konten."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]
