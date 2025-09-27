title: Image Mosaic Generator emoji: 🎨 colorFrom: blue-400 colorTo: purple-500 sdk: gradio sdk_version: "4.31.0" app_file: app.py pinned: false

# **Interactive Image Mosaic Generator**

This project is an advanced, interactive application that reconstructs any target image into a beautiful mosaic using a diverse library of image tiles. It was developed as a submission for the CS5330 course.

The application features a sophisticated algorithm that goes beyond simple color matching, using an adaptive grid and a hybrid structural similarity metric to create highly detailed and artistic results. The user interface is built with Gradio, allowing for real-time interaction and visualization of the entire mosaic generation process.


## **Key Technical Features**

This project showcases a number of advanced computer vision and software development techniques:

* **Adaptive Quadtree Gridding:** Instead of a simple, fixed grid, the application intelligently divides the target image into a non-uniform grid. It uses large tiles for simple, low-detail areas and recursively subdivides complex, high-detail areas to use smaller tiles, preserving detail where it matters most.
* **Hybrid Tile Matching Algorithm:** Tile selection is a two-step process for maximum accuracy:
  1. **Perceptual Color Filtering:** It first finds a pool of candidate tiles by matching the average color of an image region in the perceptually uniform **CIE LAB color space**.
  2. **Structural Similarity (SSIM) Ranking:** From that color-matched pool, it selects the best tile by finding the one with the highest **Structural Similarity Index (SSIM)**, ensuring that textures, lines, and shapes are also matched.
* **Diverse Tile Sourcing via Spotify API:** The tile library was created by programmatically downloading thousands of unique album covers using the Spotify Web API, providing an incredibly rich and diverse palette of colors and styles.
* **Interactive Gradio Interface:** The user-friendly web interface allows users to upload their own images, tune all the core algorithm parameters in real-time, and visualize the entire process: the original image, the calculated adaptive grid, and the final mosaic.
* **Quantitative Performance Metric:** The application calculates and displays the final SSIM score between the original image and the generated mosaic, providing a quantitative measure of the reconstruction's success.

## **Project Structure**

The repository is organized into the main application and the data preparation scripts.

/
├── app.py                     \# The final Gradio application
├── requirements.txt           \# The libraries needed to run the app
│
├── data\_preparation/
│   ├── 1\_download\_covers.py    \# Script to download album covers via Spotify API
│   └── 2\_process\_covers.py     \# Script to process raw covers into a tile library
│
├── processed\_tiles\_full\_covers/  \# Folder containing the final processed image tiles
└── tile\_data\_full\_covers\_lab.json \# Data file with color analysis for each tile

## **How to Run the Project Locally**

### **Step 1: Clone the Repository**

Clone this repository to your local machine:

git clone \<your-repo-url\>
cd \<your-repo-name\>

### **Step 2: Install Dependencies**

It is recommended to use a virtual environment. Install all the necessary libraries from the requirements.txt file.

pip install \-r requirements.txt

### **Step 3: Create the Tile Library (First-Time Setup)**

The main application (app.py) requires a pre-processed library of tile images. The scripts to generate this are in the data\_preparation/ directory.

A. Download Raw Images:
The 1\_download\_covers.py script uses the Spotify API. To run it securely without exposing your credentials, set them as environment variables in your terminal first.

* **On macOS / Linux:**
  export SPOTIPY\_CLIENT\_ID='Your\_Client\_ID\_Here'
  export SPOTIPY\_CLIENT\_SECRET='Your\_Client\_Secret\_Here'
  python data\_preparation/1\_download\_covers.py

* **On Windows (Command Prompt):**
  set SPOTIPY\_CLIENT\_ID="Your\_Client\_ID\_Here"
  set SPOTIPY\_CLIENT\_SECRET="Your\_Client\_Secret\_Here"
  python data\_preparation\\1\_download\_covers.py

This will create a raw\_album\_covers/ folder filled with thousands of images.

B. Process Images into Tiles:
Once the raw images are downloaded, run the processing script:
python data\_preparation/2\_process\_covers.py

This will create the processed\_tiles\_full\_covers/ folder and the tile\_data\_full\_covers\_lab.json file in your root project directory.

### **Step 4: Run the Main Application**

With the tile library in place, you can now run the main Gradio application:

python app.py

Open your web browser and navigate to the local URL provided in the terminal (usually http://127.0.0.1:7860).