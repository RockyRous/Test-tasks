import requests
import json
from PIL import Image, ImageTk
# GUI
import gradio as gr
from tkinter import Label, Entry, Button

from config import SD_API_KEY


class ImageApp:
    """ Image generate class """
    def __init__(self):
        self.API_KEY = SD_API_KEY
        self.url = "https://stablediffusionapi.com/api/v3/text2img"
        self.headers = {'Content-Type': 'application/json'}

    def set_prompt(self, prompt: str, negative_prompt: str | None = None) -> json:
        """
        return payload: json
        """
        payload = json.dumps({
          "key": self.API_KEY,
          "prompt": prompt,
          "negative_prompt": negative_prompt,
          "width": "512",
          "height": "512",
          "samples": "1",
          "num_inference_steps": "20",
          "seed": None,
          "guidance_scale": 7.5,
          "safety_checker": "yes",
          "multi_lingual": "no",
          "panorama": "no",
          "self_attention": "no",
          "upscale": "no",
          "embeddings_model": None,
          "webhook": None,
          "track_id": None
        })

        return payload

    @staticmethod
    def url_to_image(url: str) -> Image:
        """ Convert img url to PIL Image """
        img = Image.open(requests.get(url, stream=True).raw)
        return img

    @staticmethod
    def error_img() -> Image:
        """ Return error image """
        url = "https://atlas-content-cdn.pixelsquid.com/stock-images/error-language-w7GWrk8-600.jpg"
        image = Image.open(requests.get(url, stream=True).raw)
        return image

    def generate_image(self, prompt: str, negative_prompt: str | None = None):
        """
        Sending the Stable Diffusion prompt and negative_prompt, returns an image
        :param prompt: str
        :param negative_prompt: str or None
        :return: PIL Image or None (if error)
        """
        if prompt == '':
            print('ERROR: Prompt cannot be empty!')
            return self.error_img()

        data = self.set_prompt(prompt, negative_prompt)
        response = requests.request("POST", self.url, headers=self.headers, data=data)
        resp = response.json()

        try:
            url_img = f"{resp['output'][0]}"
        except KeyError:
            print(f"\nERROR: {resp['message']}\n")
            return self.error_img()

        image = self.url_to_image(url_img)

        return image


class GUI_gradio:
    """ Implementation of a web interface using gradio.app """
    def __init__(self):
        self.img_app = ImageApp()

    def launch_gui(self):
        def generate(prompt, negative_prompt):
            image = self.img_app.generate_image(prompt, negative_prompt)
            return image

        with gr.Blocks() as gui:
            inputs = [gr.Textbox(label='Prompt'), gr.Textbox(label='Negative prompt')]
            outputs = gr.Image()
            gen_btn = gr.Button("Generate")
            gen_btn.click(fn=generate, inputs=inputs, outputs=outputs, api_name="generate")

        gui.launch()


class GUI_tkinter:
    """ Alternative option on the desktop interface """
    def __init__(self, root):
        # Приложение генерации изображений
        self.img_app = ImageApp()

        self.root = root
        self.root.title("Stable Diffusion Image Generator")

        # Поле ввода prompt
        self.prompt_label = Label(root, text="Enter prompt:")
        self.prompt_entry = Entry(root, width=50)
        self.prompt_label.grid(row=0, column=0, padx=10, pady=10)
        self.prompt_entry.grid(row=0, column=1, padx=10, pady=10)

        # Поле ввода negative_prompt
        self.neg_prompt_label = Label(root, text="Enter negative prompt:")
        self.neg_prompt_entry = Entry(root, width=50)
        self.neg_prompt_label.grid(row=1, column=0, padx=10, pady=10)
        self.neg_prompt_entry.grid(row=1, column=1, padx=10, pady=10)

        # Кнопка генерации изображения
        self.generate_button = Button(root, text="Generate", command=self.generate_image)
        self.generate_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Отображение сгенерированного изображения
        self.image_label = Label(root)
        self.image_label.grid(row=3, column=0, columnspan=2, pady=10)

    def generate_image(self):
        prompt = self.prompt_entry.get()
        neg_prompt = self.neg_prompt_entry.get()

        # Генерация изображения с помощью Stable Diffusion
        image = self.img_app.generate_image(prompt, neg_prompt)

        # Отображение сгенерированного изображения в интерфейсе
        image.thumbnail((300, 300))
        photo = ImageTk.PhotoImage(image)
        self.image_label.config(image=photo)
        self.image_label.image = photo
