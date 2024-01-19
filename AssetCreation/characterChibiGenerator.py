import webuiapi
import uuid
from rembg import new_session, remove
from pathlib import Path
from keys import stableDiffusionUri

class CharacterChibiGenerator:

    def __init__(self) -> None:
        self.api = webuiapi.WebUIApi(baseurl=stableDiffusionUri)

        #Set the model to be used by stable diffusion
        self.options = {}
        self.options['sd_model_checkpoint'] = 'AnythingV5Ink_ink.safetensors [a1535d0a42]' 

        #Set the model to be used for removing the background of the image
        self.session = new_session("isnet-anime")

        self.sdresults = "./assets/characterchibi/sdresults"
        self.nobackground = "./assets/characterchibi/nobackground"
        self.resized = "./assets/characterchibi/resized"
        Path(self.sdresults).mkdir(parents=True, exist_ok=True)
        Path(self.nobackground).mkdir(parents=True, exist_ok=True)
        Path(self.resized).mkdir(parents=True, exist_ok=True)

    def CreateChibi(self, agent, description=None):

        self.api.set_options(self.options)

        #Build the prompt
        user_input = f'{agent.name} is a {agent.age} year old {agent.gender},"{agent.description}"'
        prompt = f"(one person),<lora:Chibi_emote_party:1>,chibi emote,(chibi style),icon,head,(head shot),(black background),{user_input}"

        if description is not None:
            if description.hair:
                prompt = prompt + (f'"Hair: {description.hair}",')
            if description.eyes:
                prompt = prompt + (f'"Eyes: {description.eyes}",')
            #if description.clothing is not None:
            #    for clothing in description.clothing:
            #        prompt = prompt + (f'"{clothing}",')
            #if description.distinguishingFeatures is not None:
            #    for feature in description.distinguishingFeatures:
            #        prompt = prompt + (f'"{feature}",')

        #create the character picture
        result = self.api.txt2img(prompt=prompt,
            negative_prompt="cat ears,full body,2 people,(neck),(body),arms,hands,watermark,signature,cut off,low contrast,underexposed,overexposed,bad art,beginner,amateur,bloodshot eyes,blurry,out of focus,circular border,",
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

        #resize the image
        width, height = output_image.size
        newSize = (width // 4, height // 4)
        resized_image = output_image.resize(newSize)

        #save to the resized folder
        resizedFilename = f"{self.resized}/{filename}"
        resized_image.save(resizedFilename, "PNG")

        return nbfilename, resizedFilename