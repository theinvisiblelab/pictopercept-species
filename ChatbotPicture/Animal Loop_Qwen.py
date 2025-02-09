import os
import csv
import base64
import itertools
import pandas as pd
import dashscope

# Define DashScope model
model_name = "qwen2.5-vl-72b-instruct"

# Folder containing images
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
    """Convert an image to Base64 encoding."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Create an empty DataFrame to store results
results_df = pd.DataFrame(columns=["Image1", "Image2", "Chosen Image", "Reason", "Model Used"])

# Iterate through each pair and send them to DashScope for comparison
for image1, image2 in image_pairs:
    image_path1 = os.path.join(image_folder, image1)
    image_path2 = os.path.join(image_folder, image2)

    # Skip if any image does not exist
    if not os.path.exists(image_path1) or not os.path.exists(image_path2):
        print(f"⚠️ Skipping missing images: {image1}, {image2}")
        continue

    # Encode both images in Base64
    base64_image1 = encode_image(image_path1)
    base64_image2 = encode_image(image_path2)

    # Send the image pair to DashScope API
    try:
        response = dashscope.MultiModalConversation.call(
            api_key=dashscope.api_key,
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": [{"text": "You are a helpful assistant."}]
                },
                {
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{base64_image1}"},
                        {"image": f"data:image/jpeg;base64,{base64_image2}"},
                        {
                            "text": f"You are given two images: {image1} and {image2}. "
                                    f"Choose the animal you would prefer to communicate with from the two images. "
                                    f"Return the chosen filename of these two filenames exactly as it is and a reason for your choice, formatted as:\n\n"
                                    f"Chosen Image: [FILENAME]\nReason: [EXPLANATION]\n\n"
                                    f"Do NOT return any names outside of {image1} or {image2}."
                        }
                    ]
                }
            ]
        )

        # **Extract the text response
        content = response.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", [])
        response_text = next((item["text"] for item in content if "text" in item), None)

        # Parse response format: "Chosen Image: [filename]\nReason: [reason]"
        chosen_image = None
        reason = "No reason provided"
        lines = response_text.split("\n") if response_text else []

        for line in lines:
            if line.startswith("Chosen Image:"):
                chosen_filename = line.replace("Chosen Image:", "").strip()
                if chosen_filename in (image1, image2):  # Ensure only valid filenames
                    chosen_image = chosen_filename
            elif line.startswith("Reason:"):
                reason = line.replace("Reason:", "").strip()

        # If DashScope did not return a valid filename, use a fallback
        if chosen_image is None:
            chosen_image = image1  # Default to the first image
            reason = "DashScope did not return a valid filename, fallback to first image."

        # Store the result in DataFrame
        results_df.loc[len(results_df)] = [image1, image2, chosen_image, reason, model_name]

        print(f"{image1} vs {image2} -> Chosen: {chosen_image} (Reason: {reason})")

    except Exception as e:
        print(f"❌ Error processing {image1} vs {image2}: {e}")

# Save the results to a CSV file
output_csv = "Qwen_image_choices.csv"
results_df.to_csv(output_csv, index=False)

print(f"Results saved to {output_csv}!")
