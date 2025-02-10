import os
import itertools
import openai
import pandas as pd
import base64
import time

# Set OpenAI API key
api_key_location = "ssh_openai.txt"
with open(api_key_location, "r") as f:
    openai.api_key = f.read().strip()

# Define dataset folder
dataset_folder = "CFD Sample"

# Collect all image file paths
image_files = []
for root, dirs, files in os.walk(dataset_folder):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):  # Supported image formats
            image_files.append(os.path.join(root, file))

print(f"Found {len(image_files)} image files.")

# Create all possible pairs of images
image_pairs = list(itertools.combinations(image_files, 2))
print(f"Generated {len(image_pairs)} image pairs.")

# Function to encode image to Base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Initialize a DataFrame to store results
results_df = pd.DataFrame(columns=["Image1", "Image2", "Chosen Image", "Reason", "Model Used"])

# Use GPT to compare image pairs
model_name = "gpt-4o-mini"  # Replace with your OpenAI model

for idx, (image1, image2) in enumerate(image_pairs):
    print(f"Processing pair {idx + 1}/{len(image_pairs)}: {image1} vs {image2}")

    # Encode images to Base64
    base64_image1 = encode_image(image1)
    base64_image2 = encode_image(image2)

    # Send API request
    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": f"You are given two images:\n1. {os.path.basename(image1)}\n2. {os.path.basename(image2)}\n\n"
                               f"Choose the one you would prefer to communicate with and explain why. "
                               f"Respond in this exact format:\n\n"
                               f"Chosen Image: [filename]\nReason: [explanation]\n\n"
                               f"Do NOT choose any image outside the given options."
                },
            ],
            max_tokens=200,
            temperature=0.7,
        )

        # Extract GPT's response
        response_text = response["choices"][0]["message"]["content"]
        print(f"Raw GPT Response: {response_text}")  # Debugging

        # Parse the response
        chosen_image = "Unknown"
        reason = "No valid reason provided"
        if "Chosen Image:" in response_text and "Reason:" in response_text:
            lines = response_text.split("\n")
            for line in lines:
                if line.startswith("Chosen Image:"):
                    chosen_filename = line.replace("Chosen Image:", "").strip()
                    if chosen_filename in [os.path.basename(image1), os.path.basename(image2)]:
                        chosen_image = chosen_filename
                elif line.startswith("Reason:"):
                    reason = line.replace("Reason:", "").strip()

        # Ensure the chosen file name is valid
        if chosen_image == "Unknown":
            print(f"Invalid GPT response. Retrying for pair: {image1} vs {image2}")
            chosen_image = os.path.basename(image1)  # Default to the first image
            reason = "Fallback: GPT did not provide a valid response."

        # Save the result
        results_df.loc[len(results_df)] = [image1, image2, chosen_image, reason, model_name]
        print(f"Result: Chosen Image = {chosen_image}, Reason = {reason}")

    except Exception as e:
        print(f"Error processing pair {image1} vs {image2}: {e}")
        results_df.loc[len(results_df)] = [image1, image2, "Error", f"API error: {e}", model_name]

    # Limit request frequency to avoid API rate limits
    time.sleep(1)

# Save results to a CSV file
output_csv = "GPT_CFD_choices.csv"
results_df.to_csv(output_csv, index=False)
print(f"All image pairs processed. Results saved to {output_csv}!")
