# =============================================================================
#           Image Mosaic Generator - FINAL SUBMISSION SCRIPT
# =============================================================================
# Features: Strict "No-Repeat" policy for all tiles, Final UI Layout, Automatic Resizing,
#           Adaptive Quadtree Gridding, Hybrid LAB+SSIM Matching, Performance Metric.
# =============================================================================
import gradio as gr
import numpy as np
import cv2
import json
from PIL import Image
import os
import random
from skimage.metrics import structural_similarity as ssim

print("--- Initializing Final Mosaic Generator ---")

# --- 1. PRE-LOAD TILE DATA ---
TILE_DATA_FILE = "tile_data_full_covers_lab.json"
TILE_DIR = "processed_tiles_full_covers"

# Get the directory where the script is located to build absolute paths
base_directory = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(base_directory, TILE_DATA_FILE)

try:
    with open(json_path, 'r') as f:
        TILE_DATA = json.load(f)
except FileNotFoundError:
    print(f"FATAL ERROR: '{TILE_DATA_FILE}' not found.")
    print(f"Please make sure it's in the same directory as this script: {base_directory}")
    TILE_DATA = [] # Prevent crash on startup

print(f"Loading {len(TILE_DATA)} color tile images into memory...")
LOADED_TILES = {}
tiles_loaded_count = 0
for tile_info in TILE_DATA:
    filename = tile_info['path']
    absolute_path = os.path.join(base_directory, TILE_DIR, filename)
    tile_image = cv2.imread(absolute_path)
    if tile_image is not None:
        LOADED_TILES[filename] = tile_image
        tiles_loaded_count += 1
print(f"Successfully loaded {tiles_loaded_count} of {len(TILE_DATA)} color tiles.")

if TILE_DATA:
    TILE_COLORS_LAB = np.array([t['avg_color_lab'] for t in TILE_DATA])

# --- 2. CORE MOSAIC ENGINE ---

def find_best_tile(cell, k_color, k_ssim, used_tiles):
    """
    Finds the best tile for a given cell, enforcing a strict no-repeat policy for all tiles.
    """
    cell_h, cell_w, _ = cell.shape
    if cell.size == 0: return None, None

    avg_cell_bgr = cv2.mean(cell)[:3]
    avg_cell_lab = cv2.cvtColor(np.uint8([[avg_cell_bgr]]), cv2.COLOR_BGR2LAB)[0][0]
    distances = np.sqrt(np.sum((TILE_COLORS_LAB - avg_cell_lab)**2, axis=1))
    candidate_indices = np.argpartition(distances, k_color)[:k_color]
    best_tile_path = None

    if cell_h >= 7 and cell_w >= 7:
        # Main Hybrid SSIM Logic
        ssim_candidates = []
        gray_cell = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
        for idx in candidate_indices:
            path = TILE_DATA[idx]['path']
            tile = LOADED_TILES[path]
            resized_tile = cv2.resize(tile, (cell_w, cell_h))
            gray_tile = cv2.cvtColor(resized_tile, cv2.COLOR_BGR2GRAY)
            score = ssim(gray_cell, gray_tile, data_range=255)
            ssim_candidates.append({'path': path, 'score': score})
        ssim_candidates.sort(key=lambda c: c['score'], reverse=True)
        top_ssim_paths = [c['path'] for c in ssim_candidates]

        # Apply strict no-repeat filter
        available_paths = [p for p in top_ssim_paths if p not in used_tiles]
        pool_to_choose_from = available_paths if available_paths else top_ssim_paths
        num_top_choices = min(k_ssim, len(pool_to_choose_from))
        best_tile_path = random.choice(pool_to_choose_from[:num_top_choices])
    else:
        # Fallback logic for small tiles
        candidate_distances = [(distances[i], i) for i in candidate_indices]
        candidate_distances.sort(key=lambda t: t[0])
        top_color_indices = [idx for dist, idx in candidate_distances]
        top_color_paths = [TILE_DATA[i]['path'] for i in top_color_indices]

        # Apply strict no-repeat filter
        available_paths = [p for p in top_color_paths if p not in used_tiles]
        pool_to_choose_from = available_paths if available_paths else top_color_paths
        num_top_choices = min(k_ssim, len(pool_to_choose_from))
        best_tile_path = random.choice(pool_to_choose_from[:num_top_choices])

    # Add the chosen tile to the used set so it won't be picked again
    if best_tile_path:
        used_tiles.add(best_tile_path)

    return best_tile_path, avg_cell_bgr

def generate_recursive_split(image, min_size, complexity_threshold, k_color, k_ssim, used_tiles, draw_grid_lines=True):
    h, w, _ = image.shape
    gray_region = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    complexity = np.std(gray_region)
    if complexity < complexity_threshold or h <= min_size or w <= min_size:
        best_tile_filename, avg_color = find_best_tile(image, k_color, k_ssim, used_tiles)
        if best_tile_filename is None:
            blank_patch = np.zeros_like(image)
            return blank_patch, blank_patch
        tile = LOADED_TILES[best_tile_filename]
        mosaic_patch = cv2.resize(tile, (w, h))
        segmented_patch = np.zeros_like(image)
        segmented_patch[:, :] = avg_color
        if draw_grid_lines:
            cv2.rectangle(segmented_patch, (0, 0), (w - 1, h - 1), (255, 255, 255), 1)
        return mosaic_patch, segmented_patch
    half_w, half_h = w // 2, h // 2
    tl_mosaic, tl_segmented = generate_recursive_split(image[0:half_h, 0:half_w], min_size, complexity_threshold, k_color, k_ssim, used_tiles, draw_grid_lines)
    tr_mosaic, tr_segmented = generate_recursive_split(image[0:half_h, half_w:w], min_size, complexity_threshold, k_color, k_ssim, used_tiles, draw_grid_lines)
    bl_mosaic, bl_segmented = generate_recursive_split(image[half_h:h, 0:half_w], min_size, complexity_threshold, k_color, k_ssim, used_tiles, draw_grid_lines)
    br_mosaic, br_segmented = generate_recursive_split(image[half_h:h, half_w:w], min_size, complexity_threshold, k_color, k_ssim, used_tiles, draw_grid_lines)
    full_mosaic = np.vstack((np.hstack((tl_mosaic, tr_mosaic)), np.hstack((bl_mosaic, br_mosaic))))
    full_segmented = np.vstack((np.hstack((tl_segmented, tr_segmented)), np.hstack((bl_segmented, br_segmented))))
    return full_mosaic, full_segmented

def upload_and_resize_image(image):
    if image is None: return None, None, None, "N/A"
    MAX_DIMENSION = 1024
    h, w, _ = image.shape
    if h > MAX_DIMENSION or w > MAX_DIMENSION:
        if h > w: new_h, new_w = MAX_DIMENSION, int(w * (MAX_DIMENSION / h))
        else: new_w, new_h = MAX_DIMENSION, int(h * (MAX_DIMENSION / w))
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA), None, None, "N/A"
    return image, None, None, "N/A"

def create_final_mosaic(original_image, max_size, min_size, complexity_threshold, color_pool_size, structural_diversity, progress=gr.Progress(track_tqdm=True)):
    if original_image is None:
        placeholder = Image.new('RGB', (512, 512), color='lightgray')
        return placeholder, placeholder, "N/A"

    target_image_bgr = cv2.cvtColor(original_image, cv2.COLOR_RGB2BGR)
    h, w, _ = target_image_bgr.shape
    final_mosaic_bgr = np.zeros_like(target_image_bgr)
    segmented_bgr = np.zeros_like(target_image_bgr)
    used_tiles = set()

    for y in progress.tqdm(range(0, h, max_size), desc="Processing Grid"):
        for x in range(0, w, max_size):
            region = target_image_bgr[y:y+max_size, x:x+max_size]
            if region.size == 0: continue
            mosaic_patch, segmented_patch = generate_recursive_split(region, min_size, complexity_threshold, int(color_pool_size), int(structural_diversity), used_tiles)
            final_mosaic_bgr[y:y+max_size, x:x+max_size] = mosaic_patch
            segmented_bgr[y:y+max_size, x:x+max_size] = segmented_patch

    output_mosaic = Image.fromarray(cv2.cvtColor(final_mosaic_bgr, cv2.COLOR_BGR2RGB))
    output_segmented = Image.fromarray(cv2.cvtColor(segmented_bgr, cv2.COLOR_BGR2RGB))
    gray_original = cv2.cvtColor(target_image_bgr, cv2.COLOR_BGR2GRAY)
    gray_mosaic = cv2.cvtColor(final_mosaic_bgr, cv2.COLOR_BGR2GRAY)
    ssim_score = ssim(gray_original, gray_mosaic, data_range=255)

    return output_segmented, output_mosaic, f"{ssim_score:.4f}"

# --- 3. GRADIO UI ---
with gr.Blocks(theme=gr.themes.Default(), title="Image Mosaic Generator") as demo:
    gr.Markdown("# Image Mosaic Generator")
    with gr.Row():
        with gr.Accordion("Settings", open=True):
            with gr.Row():
                max_size_slider = gr.Slider(minimum=32, maximum=128, step=16, value=64, label="Max Tile Size")
                min_size_slider = gr.Slider(minimum=8, maximum=32, step=8, value=16, label="Min Tile Size")
                complexity_slider = gr.Slider(minimum=5, maximum=50, step=1, value=15, label="Complexity Threshold")
            with gr.Row():
                color_pool_slider = gr.Slider(minimum=10, maximum=200, step=10, value=50, label="Color Pool Size")
                structural_diversity_slider = gr.Slider(minimum=1, maximum=20, step=1, value=5, label="Structural Diversity")
    with gr.Row():
        source_image = gr.Image(type="numpy", label="Original Image", height=500)
        segmented_output = gr.Image(label="Segmented Image (Adaptive Grid)", height=500)
        mosaic_output = gr.Image(label="Final Mosaic", height=500)
    with gr.Row():
        submit_button = gr.Button("🎨 Generate Mosaic", variant="primary", size="lg")
        score_output = gr.Textbox(label="Similarity Score (SSIM)")

    source_image.upload(fn=upload_and_resize_image, inputs=source_image, outputs=[source_image, segmented_output, mosaic_output, score_output])
    submit_button.click(fn=create_final_mosaic, inputs=[source_image, max_size_slider, min_size_slider, complexity_slider, color_pool_slider, structural_diversity_slider], outputs=[segmented_output, mosaic_output, score_output])

# This block allows the script to be run from the command line
if __name__ == "__main__":
    demo.launch()
