#Taken directly from https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
import json
import requests
import io
import base64
from PIL import Image, PngImagePlugin

from copy import deepcopy

from pathlib import Path

class img2imgBatchGen:
    def __init__(self, starterPayload, outputDirName="output/", url="http://127.0.0.1:7860"):
        self.url = url
        self.outputDir = Path(outputDirName)
        self.starterPayload = starterPayload
        #define defaults for the x/y/z script part
        self.xyzArgs = {}
        self.xyzDefaults = {'x_type':'seed',
                        'x_values':'1,2,3',
                        'y_type':'Nothing',
                        'y_values':"",
                        'z_type':'Nothing',
                        'z_values':"",
                        'draw_legend':True,
                        'include_lone_images':False,
                        'include_sub_grids':False,
                        'no_fixed_seeds':False,
                        'margin_size':0}
        self.xyzSweepTypes = ['nothing', 'seed', 'var. seed', 'var. strength', 'steps', 'cfg scale',
                         'prompt s/r', 'prompt order', 'sampler', 'checkpoint name', 
                         'sigma churn', 'sigma min', 'sigma max', 'sigma noise', 'eta',
                          'clip skip', 'denoising', 'cond. Image mask weight', 'vae', 'styles']

    def pil_to_base64(self, pil_image):
        """
        Encodes an img object to base 64, so it can be sent to the generator
        """
        with io.BytesIO() as stream:
            pil_image.save(stream, "PNG", pnginfo=None)
            base64_str = str(base64.b64encode(stream.getvalue()), "utf-8")
            return "data:image/png;base64," + base64_str

    def addXYZArgs(self, payload):
        """
        modifies the payload to add the args needed for the XYZ sweep
        """
        if 'script_name' in payload.keys() and payload['script_name'] == 'X/Y/Z plot':
            script_args = []
            for defaultKey in self.xyzDefaults.keys():
                #if a value was provided in xyzArgs, use it
                if defaultKey in self.xyzArgs.keys():
                    realArg = self.xyzArgs[defaultKey]
                else:#if the value was not specified in xyz Args, use default
                    realArg = self.xyzDefaults[defaultKey]
                #format each key just right
                if defaultKey in ['x_type', 'y_type', 'z_type']:
                    realArg = realArg.lower()
                    if realArg in self.xyzSweepTypes:
                        realArg = self.xyzSweepTypes.index(realArg)#Changes "nothing" to 0, "Seed" to 1, etc
                    else:
                        raise ValueError(f"Error: bad xyzArgs {defaultKey} = {realArg} but {realArg} is not in list {self.xyzSweepTypes} (note: always converted to lowercase for ease of use)")                
                script_args.append(realArg)

            payload['script_args'] = script_args
        return payload

    def generateImage(self, initImageNameAndPath, prompt, otherPayloadItems={}):
        """
        Takes in a initImageNameAndPath, prompt, otherPayloadItems, adds them to starterpayload, and generates the image
        """

        #remove init_image_name and replace with init_image (binary image data)
        payload = deepcopy(self.starterPayload)
        initImageName = Path(initImageNameAndPath).parts[-1].split('.')[0]
        title=initImageName
        if type(initImageNameAndPath) != type('string'):
            raise Exception(f"Argument payload['init_image_name'] not string, instead {type(initImageNameAndPath)}")
        with Image.open(initImageNameAndPath) as initImageObj:
            imgBytes = self.pil_to_base64(initImageObj)
            payload['init_images'] = [imgBytes]
        #add in the important items to the payload
        payload['prompt'] = prompt
        for key, val in otherPayloadItems.items():
            payload[key] = val

        payload = self.addXYZArgs(payload)

        #Send it
        response = requests.post(url=f'{self.url}/sdapi/v1/img2img', json=payload)
        #Get it back
        r = response.json()
        #it's possible to get multiple images, but usually it returns just 1
        for i in range(len(r['images'])):
            img_data = r['images'][i]
            image = Image.open(io.BytesIO(base64.b64decode(img_data.split(",",1)[0])))

            png_payload = {
                "image": "data:image/png;base64," + img_data
            }
            response2 = requests.post(url=f'{self.url}/sdapi/v1/png-info', json=png_payload)

            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text("parameters", response2.json().get("info"))
            image.save(self.outputDir / f'{title}_{i}.png', pnginfo=pnginfo)

if __name__ == "__main__":
    starterPayload = {"script_name": "X/Y/Z plot",
                    "steps": 5,
                    "width":500,
                    "height":380}
    xyzArgs = {'x_type':'Seed',
                'x_values':'1,2,3',
                'y_type':'Denoising',
                'y_values':'0.2, 0.5, 0.8',
                'z_type':'sampler',
                'z_values':'Heun, DPM++ SDE Karras'}
    myImg2Img = img2imgBatchGen(starterPayload=starterPayload)
    myImg2Img.xyzArgs = xyzArgs
    myImg2Img.generateImage(initImageNameAndPath="resources/strike.png", prompt="a sword being swung through the air on a red background")
    myImg2Img.generateImage(initImageNameAndPath="resources/body_slam.png", prompt="A fat man covered in pillows body-slamming into a ghostly man")
