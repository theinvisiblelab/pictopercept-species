import base64
import openai

api_key_location = "ssh_openai.txt"
openai.api_key = open(api_key_location).read().strip()

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Path to your image
image_path1 = "image1.jpg"
image_path2 = "image2.jpg"

# Getting the base64 string
base64_image1 = encode_image(image_path1)
base64_image2 = encode_image(image_path2)

response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "From the two images provided, choose the animal you would prefer to communicate with. Only return the name of the image you choose.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image1}",
                    },
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image2}",
                    },
                },
            ],
        }
    ],
    max_tokens=300,
)
print(response["choices"][0]["message"]["content"])