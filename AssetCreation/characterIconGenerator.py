import webuiapi
import uuid
from rembg import new_session, remove
from pathlib import Path
from keys import stableDiffusionUri

class CharacterIconGenerator:

    def __init__(self) -> None:
        self.api = webuiapi.WebUIApi(baseurl=stableDiffusionUri)

        #Set the model to be used by stable diffusion
        self.options = {}
        self.options['sd_model_checkpoint'] = 'bluePencilXL_v300.safetensors [2e29ce9ae7]' 

        #Set the model to be used for removing the background of the image
        self.session = new_session("isnet-anime")

        self.sdresults = "./assets/charactericon/sdresults"
        self.nobackground = "./assets/charactericon/nobackground"
        Path(self.sdresults).mkdir(parents=True, exist_ok=True)
        Path(self.nobackground).mkdir(parents=True, exist_ok=True)

    def CreateIcon(self, agent):

        self.api.set_options(self.options)

        #Build the prompt
        user_input = f'{agent.name} is a {agent.age} year old {agent.gender}, "{agent.description}"'
        prompt = f" <lora:q-v1:2>, ((painterly)), chibi, full body, black background,{user_input}"

        #create the character picture
        result = self.api.txt2img(prompt=prompt,
            negative_prompt="tiling,out of frame,extra limbs,body out of frame,watermark,signature,cut off,low contrast,underexposed,overexposed,bad art,beginner,amateur,bloodshot eyes,blurry,out of focus,circular border,",
            cfg_scale=5,
            width=512,
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

        return nbfilename