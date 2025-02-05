import os
import csv
import base64
import openai
import itertools
import pandas as pd

# Read OpenAI API key from a text file
api_key_location = "ssh_openai.txt"
openai.api_key = open(api_key_location).read().strip()

# Define OpenAI model to use
model_name = "gpt-4o-mini"

# Folder containing the images
image_folder = "images_sample"

# Read CSV file to get all image names
csv_file = "images_name.csv"
with open(csv_file, "r") as file:
    reader = csv.reader(file)
    next(reader)  # Skip header
    image_files = [row[0] for row in reader]

# Generate all possible unique image pairs (excluding self-pairing)
image_pairs = list(itertools.combinations(image_files, 2))


# Function to encode an image to Base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Create an empty DataFrame to store results
results_df = pd.DataFrame(columns=["Image1", "Image2", "Chosen Image", "Reason", "Model Used"])

# Iterate through each pair and send them to GPT for comparison
for image1, image2 in image_pairs:
    image_path1 = os.path.join(image_folder, image1)
    image_path2 = os.path.join(image_folder, image2)

    # Skip if any image does not exist
    if not os.path.exists(image_path1) or not os.path.exists(image_path2):
        print(f"Skipping missing images: {image1}, {image2}")
        continue

    # Encode both images in Base64
    base64_image1 = encode_image(image_path1)
    base64_image2 = encode_image(image_path2)

    # Send the image pair to OpenAI API
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"You are given two images: {image1} and {image2}. "
                                f"Choose the animal you would prefer to communicate with from the two images."
                                f"Return the chosen filename of these two filenames exactly as it is and a reason for your choice, formatted as:\n\n"
                                f"Chosen Image: [FILENAME]\nReason: [EXPLANATION]\n\n"
                                f"Do NOT return any names outside of {image1} or {image2}."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image1}"},
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image2}"},
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    # Extract response content
    response_text = response["choices"][0]["message"]["content"]

    # Parse response format: "Chosen Image: [filename]\nReason: [reason]"
    lines = response_text.split("\n")

    # Default values
    chosen_image = None
    reason = "No reason provided"

    # Ensure correct filename selection
    for line in lines:
        if line.startswith("Chosen Image:"):
            chosen_filename = line.replace("Chosen Image:", "").strip()
            if chosen_filename in (image1, image2):  # Ensure only valid filenames
                chosen_image = chosen_filename
        elif line.startswith("Reason:"):
            reason = line.replace("Reason:", "").strip()

    # If GPT failed to return a valid filename, choose randomly as fallback
    if chosen_image is None:
        chosen_image = image1  # Default to the first image
        reason = "GPT did not return a valid filename, fallback to first image."

    # Store the result in DataFrame
    results_df.loc[len(results_df)] = [image1, image2, chosen_image, reason, model_name]

    print(f"{image1} vs {image2} -> Chosen: {chosen_image} (Reason: {reason})")

# Save the results to a CSV file
output_csv = "gpt_image_choices.csv"
results_df.to_csv(output_csv, index=False)

print(f"All image pairs have been processed. Results saved in {output_csv}!")