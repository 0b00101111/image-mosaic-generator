# =============================================================================
#           2_process_covers.py - Tile Library Processor
# =============================================================================
# This script takes a folder of raw source images (e.g., downloaded album covers),
# processes each one into a standardized tile, analyzes its perceptual color,
# and saves the final library and its data file.
# =============================================================================

import cv2
import numpy as np
import glob
import os
import json

# --- 1. CONFIGURATION ---
SOURCE_DIR = "raw_album_covers"
OUTPUT_DIR = "processed_tiles_full_covers"
TILE_DATA_FILE = "tile_data_full_covers_lab.json"
TILE_SIZE = (128, 128) # Larger tile size to preserve detail of full covers

# --- 2. SETUP ---
print(f"Processing full covers from '{SOURCE_DIR}'...")
source_image_paths = glob.glob(f"{SOURCE_DIR}/*.jpg") + glob.glob(f"{SOURCE_DIR}/*.jpeg") + glob.glob(f"{SOURCE_DIR}/*.png")
os.makedirs(OUTPUT_DIR, exist_ok=True)
if not source_image_paths:
    print(f"Error: No source images found in '{SOURCE_DIR}'.")
    exit()

# --- 3. MAIN PROCESSING LOOP ---
tile_database = []
tile_count = 0
for i, image_path in enumerate(source_image_paths):
    print(f"\rProcessing image {i+1}/{len(source_image_paths)}...", end="")

    full_cover_image = cv2.imread(image_path)
    if full_cover_image is None: continue

    # Resize the entire image to our standard tile size
    final_tile = cv2.resize(full_cover_image, TILE_SIZE, interpolation=cv2.INTER_AREA)

    # Analyze its average color in LAB space
    avg_bgr_color = cv2.mean(final_tile)[:3]
    avg_bgr_pixel = np.uint8([[avg_bgr_color]])
    avg_lab_pixel = cv2.cvtColor(avg_bgr_pixel, cv2.COLOR_BGR2LAB)
    avg_lab_color = avg_lab_pixel[0][0].tolist()

    # Save the resized cover and its data
    filename = f"full_cover_{tile_count}.png"
    output_path = os.path.join(OUTPUT_DIR, filename)
    cv2.imwrite(output_path, final_tile)

    tile_database.append({
        'path': filename,
        'avg_color_lab': avg_lab_color
    })
    tile_count += 1

# --- 4. FINALIZE ---
print(f"\n\nProcessing complete. Generated {tile_count} full cover tiles.")
if tile_count > 0:
    with open(TILE_DATA_FILE, 'w') as f:
        json.dump(tile_database, f, indent=2)
    print(f"Tile data saved to '{TILE_DATA_FILE}'.")
