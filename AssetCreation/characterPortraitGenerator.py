import webuiapi
import uuid
from rembg import new_session, remove
from pathlib import Path
from keys import stableDiffusionUri

#TODO: store all assets in the cloud

class CharacterPortraitGenerator:

    def __init__(self) -> None:
        self.api = webuiapi.WebUIApi(baseurl=stableDiffusionUri)

        #Set the model to be used by stable diffusion
        self.options = {}
        self.options['sd_model_checkpoint'] = 'bluePencilXL_v300.safetensors [2e29ce9ae7]' 
        #self.options['sd_model_checkpoint'] = 'dreamshaper_8.safetensors [879db523c3]' 

        #Set the model to be used for removing the background of the image
        self.session = new_session("isnet-anime")
        #self.session = new_session("u2net_human_seg")

        self.sdresults = "./assets/portraits/sdresults"
        self.nobackground = "./assets/portraits/nobackground"
        Path(self.sdresults).mkdir(parents=True, exist_ok=True)
        Path(self.nobackground).mkdir(parents=True, exist_ok=True)

    def CreatePortrait(self, agent, description=None):

        self.api.set_options(self.options)

        #Build the prompt
        user_input = f'{agent.name} is a {agent.age} year old {agent.gender},"{agent.description}"'
        prompt = f"game icon,(head shot),(painterly),black background,{user_input},"

        if description is not None:
            if description.hair:
                prompt = prompt + (f'"Hair: {description.hair}",')
            if description.eyes:
                prompt = prompt + (f'"Eyes: {description.eyes}",')
            if description.clothing is not None:
                for clothing in description.clothing:
                    prompt = prompt + (f'"{clothing}",')
            if description.distinguishingFeatures is not None:
                for feature in description.distinguishingFeatures:
                    prompt = prompt + (f'"{feature}",')

        #create the character picture
        result = self.api.txt2img(prompt=prompt,
            negative_prompt="tiling,poorly drawn hands,poorly drawn feet,poorly drawn face,out of frame,extra limbs,disfigured,deformed,body out of frame,bad anatomy,watermark,signature,cut off,low contrast,underexposed,overexposed,bad art,beginner,amateur,distorted face,bloodshot eyes,blurry,out of focus,circular border,",
            cfg_scale=7,
            width=512,
            height=768,
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