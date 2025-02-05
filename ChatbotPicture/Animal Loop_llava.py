import os
import csv
import itertools
import pandas as pd
import ollama
import re

# Folder containing images
image_folder = "images_sample"

# Read CSV file to get all image names
csv_file = "images_name.csv"
with open(csv_file, "r") as file:
    reader = csv.reader(file)
    next(reader)  # Skip header
    image_files = [row[0].strip() for row in reader]  # Prevent extra spaces when reading

# Generate all unique image pairs
image_pairs = list(itertools.combinations(image_files, 2))

# Create a DataFrame to store results
results_df = pd.DataFrame(columns=["Image1", "Image2", "Chosen Image", "Reason", "Model Used"])

# Process each image pair
for image1, image2 in image_pairs:
    image_path1 = os.path.join(image_folder, image1)
    image_path2 = os.path.join(image_folder, image2)

    # Skip if any image is missing
    if not os.path.exists(image_path1) or not os.path.exists(image_path2):
        print(f"Skipping missing images: {image1}, {image2}")
        continue

    # Send to LLaVA
    prompt = (
        f"You are given two images: {image1} and {image2}. "
        f"Choose the animal you would prefer to communicate with from the two images. Return the chosen filename **exactly as written**, "
        f"without adding extra text, spaces, or new lines. "
        f"Return your choice **strictly in this format**:\n\n"
        f"**Chosen Image:** [FILENAME]\n**Reason:** [EXPLANATION]\n\n"
        f"Do NOT return any names outside of {image1} or {image2}."
    )

    response = ollama.chat(
        model="llava",
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [image_path1, image_path2]
        }]
    )

    # Extract response content
    response_text = response["message"]["content"]
    print(f"\n🔹 Response received:\n{response_text}\n")  # Debugging log

    # Default values
    chosen_image = None
    reason = "No reason provided"

    # **Improved Filename Extraction**
    lines = response_text.strip().split("\n")  # Split response into lines

    # Step 1: Look for explicit "Chosen Image:" format
    for line in lines:
        if "Chosen Image:" in line:
            chosen_filename = re.sub(r"[^\w.-]", "", line.replace("**Chosen Image:**", "").strip())
            break  # Stop after finding the first valid match

    # Step 2: If explicit "Chosen Image:" is missing, find any valid filename in response
    if not chosen_image:
        for line in lines:
            match = re.search(r"(\bNZP-\d+-\d+JC(?:-\d+)?\b)", line)
            if match:
                chosen_filename = match.group(1) + ".jpg" if "." not in match.group(1) else match.group(1)
                break  # Stop after finding the first match

    # Step 3: Extract the last "Reason:" line (if present)
    for line in lines:
        if "Reason:" in line:
            reason = line.split("Reason:")[-1].strip()

    # Step 4: Validate extracted filename
    valid_filenames = {image1, image2, image1.replace(".jpg", ""), image2.replace(".jpg", "")}
    if chosen_filename in valid_filenames:
        chosen_image = chosen_filename + ".jpg" if "." not in chosen_filename else chosen_filename
    else:
        print(f"❌ Invalid filename detected: '{chosen_filename}' -> No valid choice returned.")
        chosen_image = None
        reason = f"LLaVA did not return a valid filename. Response: {response_text}"

    # Store the result
    results_df.loc[len(results_df)] = [image1, image2, chosen_image, reason, "LLaVA"]
    print(f"{image1} vs {image2} -> Chosen: {chosen_image} (Reason: {reason})\n")

# Save results to CSV
results_df.to_csv("llava_image_choices.csv", index=False)
print("Results saved to 'llava_image_choices.csv'")
