import webuiapi
import uuid
from rembg import new_session, remove
from pathlib import Path
from keys import stableDiffusionUri

class BuildingInteriorGenerator:

    def __init__(self) -> None:
        self.api = webuiapi.WebUIApi(baseurl=stableDiffusionUri)

        #Set the model to be used by stable diffusion
        self.options = {}
        self.options['sd_model_checkpoint'] = "fantasyWorld_v10.safetensors [524882ba22]"

        #Set the model to be used for removing the background of the image
        self.session = new_session("u2net")

        self.sdresults = "assets/buildingInterior/sdresults"
        self.nobackground = "assets/buildingInterior/nobackground"
        self.resized = "assets/buildingInterior/resized"
        Path(self.sdresults).mkdir(parents=True, exist_ok=True)
        Path(self.nobackground).mkdir(parents=True, exist_ok=True)
        Path(self.resized).mkdir(parents=True, exist_ok=True)

    def CreateLocation(self, location, scenario):

        self.api.set_options(self.options)

        #Build the prompt
        user_input = f'inside the {location.name} in {scenario.name},in the year {scenario.currentDateTime.year},"{location.description}"'
        prompt = f"(building interior),inside,interior,<lora:howlbgsv3:1>,bright colors,{user_input}"

        #create the character picture
        result = self.api.txt2img(prompt=prompt,
            negative_prompt="text,word,monochrome,cropped,low quality,normal quality,soft line,username,(watermark),(signature),blurry,soft,sketch,ugly,logo,pixelated,lowres,out of frame,cut off,blurry,foggy,reflection,outside,exterior,building exterior",
            cfg_scale=7,
            width=1024,
            height=512,
            steps=40,
            #hr_scale=2,
            #hr_upscaler="Latent",
            save_images=True)
        
        #save the image to the sdresults folder
        filename = f"{uuid.uuid4()}.png"
        sdfilename = f"{self.sdresults}/{filename}"
        result.image.save(sdfilename, "PNG")

        #resize the image
        width, height = result.image.size
        newSize = (int(width * 2), int(height * 2))
        resized_image = result.image.resize(newSize)

        #save to the resized folder
        resizedFilename = f"{self.resized}/{filename}"
        resized_image.save(resizedFilename, "PNG")

        return sdfilename, resizedFilename