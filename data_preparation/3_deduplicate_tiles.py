# =============================================================================
#           Tile Library De-duplicator
# =============================================================================
# This script cleans the final tile library by finding and removing any
# images that are visually identical, even if they have different filenames.
# It uses image hashing to create a unique "fingerprint" for each tile.
# =============================================================================

import cv2
import os
import imagehash
from PIL import Image

# --- Configuration ---
TILE_DIR = "processed_tiles_full_covers"
TILE_DATA_FILE = "tile_data_full_covers_lab.json"

print("Starting tile de-duplication process...")

# Check if the required library is installed
try:
    import imagehash
except ImportError:
    print("\n'imagehash' library not found.")
    print("Please install it by running: pip install imagehash")
    exit()

if not os.path.exists(TILE_DIR):
    print(f"FATAL ERROR: Tile directory '{TILE_DIR}' not found.")
    exit()

# --- Main De-duplication Logic ---
# Keep track of the hashes of images we've already seen
seen_hashes = set()
# Keep track of the full paths of files to be removed
files_to_remove = []
# Keep track of the filenames to remove from the JSON
paths_to_remove_from_json = set()

# First pass: identify all duplicate files
print(f"Scanning {len(os.listdir(TILE_DIR))} tiles for duplicates...")
for filename in os.listdir(TILE_DIR):
    if not filename.endswith(".png"):
        continue

    file_path = os.path.join(TILE_DIR, filename)

    try:
        # Open the image and calculate its perceptual hash
        img = Image.open(file_path)
        hash_value = imagehash.phash(img)

        # If we have seen this hash before, it's a duplicate
        if hash_value in seen_hashes:
            files_to_remove.append(file_path)
            # We store the relative path for the JSON update
            paths_to_remove_from_json.add(filename)
        else:
            # If it's the first time, add its hash to our set
            seen_hashes.add(hash_value)

    except Exception as e:
        print(f"  Warning: Could not process {filename}. Error: {e}")

# Second pass: remove the identified duplicate files
print(f"\nFound {len(files_to_remove)} duplicate images. Removing them...")
for file_path in files_to_remove:
    try:
        os.remove(file_path)
    except OSError as e:
        print(f"  Error removing file {file_path}: {e}")

# Third pass: update the JSON data file to remove references to the deleted files
print(f"Updating '{TILE_DATA_FILE}' to remove duplicate entries...")
if os.path.exists(TILE_DATA_FILE):
    import json
    with open(TILE_DATA_FILE, 'r') as f:
        tile_data = json.load(f)

    # Create a new list containing only the non-duplicate entries
    cleaned_tile_data = [
        entry for entry in tile_data if entry['path'] not in paths_to_remove_from_json
    ]

    # Save the cleaned data back to the file
    with open(TILE_DATA_FILE, 'w') as f:
        json.dump(cleaned_tile_data, f, indent=2)

print("\nDe-duplication complete.")
print(f"Your tile library now contains {len(seen_hashes)} unique images.")
