# Stable Diffusion Image Generator

This application generates images using Stable Diffusion API and provides both a web-based interface with gradio.app and a desktop interface using tkinter.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/StableDiffusionImageGenerator.git
cd StableDiffusionImageGenerator
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your API key:

   - Open `config.py` and replace `YOUR_API_KEY` with your actual Stable Diffusion API key.

## Usage

### Web Interface (Gradio)

1. Run the application using `main.py`:

```bash
python main.py
```

2. Access the web interface by opening the provided URL in your browser.

3. Enter a prompt and, optionally, a negative prompt.

4. Click the "Generate" button to generate an image.

### Desktop Interface (Tkinter)

1. Run the application using `main.py`:

```bash
python main.py
```

2. Enter a prompt and, optionally, a negative prompt in the Tkinter window.

3. Click the "Generate" button to generate an image.

## Additional Information

- The `app.py` file contains the main logic for image generation and the two GUI implementations.
- The `config.py` file holds the API key configuration.
- Dependencies are listed in `requirements.txt`.
- Make sure to comply with the Stable Diffusion API usage terms and conditions.
