import ollama

response = ollama.chat(
    model='llava',
    messages=[{
        'role': 'user',
        'content': 'From the two images provided, choose the animal you would prefer to communicate with. Only return the name of the image you choose.',
        'images': ['image1.jpg', 'image2.jpg']
    }]
)

print(response["message"]["content"])

