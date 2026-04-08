from groq import Groq

client = Groq(api_key="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")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "What is diabetes?"}]
)

print(response.choices[0].message.content)