import webuiapi
import uuid
from rembg import new_session, remove
from pathlib import Path
from keys import stableDiffusionUri

class BuildingExteriorGenerator:

    def __init__(self) -> None:
        self.api = webuiapi.WebUIApi(baseurl=stableDiffusionUri)

        #Set the model to be used by stable diffusion
        self.options = {}
        self.options['sd_model_checkpoint'] = "fantasyWorld_v10.safetensors [524882ba22]"

        #Set the model to be used for removing the background of the image
        self.session = new_session("u2net")

        self.sdresults = "./assets/buildingExterior/sdresults"
        self.nobackground = "./assets/buildingExterior/nobackground"
        self.resized = "./assets/buildingExterior/resized"
        Path(self.sdresults).mkdir(parents=True, exist_ok=True)
        Path(self.nobackground).mkdir(parents=True, exist_ok=True)
        Path(self.resized).mkdir(parents=True, exist_ok=True)

    def CreateLocation(self, location, scenario):

        self.api.set_options(self.options)

        #Build the prompt
        user_input = f'{location.name} in {scenario.name},in the year {scenario.currentDateTime.year}'
        prompt = f"(((isometric))),(Isometric_Setting),(building exterior),((black background)),<lora:Stylized_Setting_SDXL:2>,bright colors,{user_input}"

        #create the character picture
        result = self.api.txt2img(prompt=prompt,
            negative_prompt="text,word,monochrome,cropped,low quality,normal quality,soft line,username,(watermark),(signature),blurry,soft,sketch,ugly,logo,pixelated,lowres,out of frame,cut off,blurry,foggy,reflection",
            cfg_scale=7,
            width=768,
            height=512,
            steps=40,
            save_images=True)
        
        #save the image to the sdresults folder
        filename = f"{uuid.uuid4()}.png"
        sdfilename = f"{self.sdresults}/{filename}"
        result.image.save(sdfilename, "PNG")

        #remove the background
        output_image = remove(result.image, session=self.session)

        #save the image to the nobackground folder
        nbfilename = f"{self.nobackground}/{filename}"
        output_image.save(nbfilename, "PNG")

        #resize the image
        width, height = output_image.size
        newSize = (width // 2, height // 2)
        resized_image = output_image.resize(newSize)

        #save to the resized folder
        resizedFilename = f"{self.resized}/{filename}"
        resized_image.save(resizedFilename, "PNG")

        return nbfilename, resizedFilename