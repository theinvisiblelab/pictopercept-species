import os
import base64
import itertools
import pandas as pd
import dashscope

# Define DashScope model
model_name = "qwen2.5-vl-72b-instruct"

# Define folder containing images
image_folder = "CFD Sample"

# Function to encode an image to Base64
def encode_image(image_path):
    """Convert an image to Base64 encoding."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Collect all image file paths from the `CFD Sample` folder and its subdirectories
image_files = []
for root, _, files in os.walk(image_folder):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):  # Supported formats
            image_files.append(os.path.join(root, file))  # Store full paths

print(f"Found {len(image_files)} images in '{image_folder}'.")

# Generate all possible unique image pairs (excluding self-pairing)
image_pairs = list(itertools.combinations(image_files, 2))
print(f"Generated {len(image_pairs)} image pairs.")

# Create an empty DataFrame to store results
results_df = pd.DataFrame(columns=["Image1", "Image2", "Chosen Image", "Reason", "Model Used"])

# Iterate through each pair and send them to DashScope for comparison
for image1, image2 in image_pairs:
    # Encode both images in Base64
    base64_image1 = encode_image(image1)
    base64_image2 = encode_image(image2)

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
                            "text": f"You are given two images: {os.path.basename(image1)} and {os.path.basename(image2)}. "
                                    f"Choose the person you would prefer to communicate with from the two images. "
                                    f"Return the chosen filename exactly as it is and provide a reason, formatted as:\n\n"
                                    f"**Chosen Image:** [FILENAME]\n**Reason:** [EXPLANATION]\n\n"
                                    f"Do NOT return any names outside of {os.path.basename(image1)} or {os.path.basename(image2)}."
                        }
                    ]
                }
            ]
        )

        # **Extract the text response**
        content = response.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", [])
        response_text = next((item["text"] for item in content if "text" in item), None)

        # **Parse response format**
        chosen_image = None
        reason = "No reason provided"
        lines = response_text.split("\n") if response_text else []

        for line in lines:
            if line.startswith("**Chosen Image:**"):
                chosen_filename = line.replace("**Chosen Image:**", "").strip()
                if chosen_filename in {os.path.basename(image1), os.path.basename(image2)}:
                    chosen_image = chosen_filename
            elif line.startswith("**Reason:**"):
                reason = line.replace("**Reason:**", "").strip()

        # **Fallback Handling**
        if chosen_image is None:
            chosen_image = os.path.basename(image1)  # Default to the first image
            reason = "DashScope did not return a valid filename, fallback to first image."

        # Store the result in DataFrame
        results_df.loc[len(results_df)] = [os.path.basename(image1), os.path.basename(image2), chosen_image, reason, model_name]

        print(f"{os.path.basename(image1)} vs {os.path.basename(image2)} -> Chosen: {chosen_image} (Reason: {reason})")

    except Exception as e:
        print(f"❌ Error processing {os.path.basename(image1)} vs {os.path.basename(image2)}: {e}")

# Save the results to a CSV file
output_csv = "Qwen_CFD_choices.csv"
results_df.to_csv(output_csv, index=False)

print(f"Results saved to {output_csv}!")
