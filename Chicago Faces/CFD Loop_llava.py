import os
import itertools
import pandas as pd
import ollama
import re

# Define the folder containing images
image_folder = "CFD Sample"

# Collect all image files from the folder and subfolders
image_files = []
for root, _, files in os.walk(image_folder):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):  # Supported image formats
            image_files.append(os.path.join(root, file))  # Full paths

print(f"Found {len(image_files)} images.")

# Generate all unique image pairs
image_pairs = list(itertools.combinations(image_files, 2))
print(f"Generated {len(image_pairs)} image pairs.")

# Create a DataFrame to store results
results_df = pd.DataFrame(columns=["Image1", "Image2", "Chosen Image", "Reason", "Model Used"])

# Process each image pair
for image1, image2 in image_pairs:
    # Send to LLaVA
    prompt = (
        f"You are given two images: {os.path.basename(image1)} and {os.path.basename(image2)}. "
        f"Choose the person you would prefer to communicate with from the two images. "
        f"Return the filename exactly as written, with no extra characters.\n\n"
        f"Format your response strictly as:\n"
        f"**Chosen Image:** [FILENAME]\n**Reason:** [EXPLANATION]\n\n"
        f"Do NOT return any names outside of {os.path.basename(image1)} or {os.path.basename(image2)}."
    )

    response = ollama.chat(
        model="llava",
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [image1, image2]  # Pass the full paths
        }]
    )

    # Extract response content
    response_text = response["message"]["content"]
    print(f"\nResponse received:\n{response_text}\n")  # Debugging log

    # Default values
    chosen_image = None
    reason = "No reason provided"

    # Ensure valid filenames (strip extensions for comparison)
    valid_filenames = {
        os.path.basename(image1),
        os.path.basename(image2),
        os.path.basename(image1).replace(".jpg", ""),
        os.path.basename(image2).replace(".jpg", ""),
    }

    # Step 1: Look for explicit "Chosen Image:" format
    chosen_image_match = re.search(r"\*\*Chosen Image:\*\*\s*(\S+)", response_text)
    if chosen_image_match:
        chosen_image = chosen_image_match.group(1).strip()

    # Step 2: If missing, extract any filename in the response
    if not chosen_image:
        filename_match = re.search(r"CFD-AF-\d{3}-\d{3}-N(?:\.jpg)?", response_text)  # Match with or without .jpg
        if filename_match:
            chosen_image = filename_match.group(0)
            if ".jpg" not in chosen_image:
                chosen_image += ".jpg"  # Append .jpg if missing

    # Step 3: Ensure extracted filename matches one of the input filenames
    if chosen_image.replace(".jpg", "") in valid_filenames:
        # Ensure final output has ".jpg"
        if ".jpg" not in chosen_image:
            chosen_image += ".jpg"
    else:
        print(f"❌ Invalid filename detected: '{chosen_image}' -> No valid choice returned.")
        chosen_image = None
        reason = f"LLaVA response did not include a valid filename. Raw Response: {response_text}"

    # Extract and validate reason
    reason_match = re.search(r"\*\*Reason:\*\*\s*(.+)", response_text)
    if reason_match:
        reason = reason_match.group(1).strip()

    # Store the result
    results_df.loc[len(results_df)] = [os.path.basename(image1), os.path.basename(image2), chosen_image, reason, "LLaVA"]
    print(f"{os.path.basename(image1)} vs {os.path.basename(image2)} -> Chosen: {chosen_image} (Reason: {reason})\n")

# Save results to CSV
results_df.to_csv("llava_image_choices.csv", index=False)
print("Results saved to 'llava_image_choices.csv'")
