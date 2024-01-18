import webuiapi
import uuid
from pathlib import Path
from keys import stableDiffusionUri

class BackgroundGenerator:

    def __init__(self) -> None:
        self.api = webuiapi.WebUIApi(baseurl=stableDiffusionUri)

        #Set the model to be used by stable diffusion
        self.options = {}
        self.options['sd_model_checkpoint'] = "fantasyWorld_v10.safetensors [524882ba22]"

        self.sdresults = "./assets/background/sdresults"
        Path(self.sdresults).mkdir(parents=True, exist_ok=True)

    def CreateScenarioBackground(self, scenario):

        self.api.set_options(self.options)

        #Build the prompt
        user_input = f"({scenario.seed}), {scenario.name} in the year {scenario.currentDateTime.year}"
        prompt = f"(landscape), ((nature)), (isometric), Isometric_Setting, <lora:Stylized_Setting_SDXL:1>, {user_input}"

        #create the character picture
        result = self.api.txt2img(prompt=prompt,
            negative_prompt="1girl, text, cropped, word, low quality, normal quality, soft line username, (watermark), (signature), blurry, soft, curved line, sketch, ugly, logo, pixelated, lowres, buildings, (building),",
            cfg_scale=7,
            width=2048,
            height=1024,
            steps=40,
            save_images=True)
        
        #save the image to the sdresults folder
        filename = f"{uuid.uuid4()}.png"
        sdfilename = f"{self.sdresults}/{filename}"
        result.image.save(sdfilename, "PNG")

        return sdfilename