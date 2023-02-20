#Taken directly from https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
import json
import requests
import io
import base64
from PIL import Image, PngImagePlugin

url = "http://127.0.0.1:7860"
outputDir = "output/"
payload = {
    "init_image_name":"resources/strike.png",
    "prompt": "a sword being swung through the air on a red background",
    "steps": 5
}



def pil_to_base64(pil_image):
    """
    Encodes an img object to base 64, so it can be sent to the generator
    """
    with io.BytesIO() as stream:
        pil_image.save(stream, "PNG", pnginfo=None)
        base64_str = str(base64.b64encode(stream.getvalue()), "utf-8")
        return "data:image/png;base64," + base64_str


#remove init_image_name and replace with init_image (binary image data)
initImageName = payload.pop('init_image_name')
if type(initImageName) != type('string'):
    raise Exception(f"Argument payload['init_image_name'] not string, instead {type(initImageName)}")
with Image.open(initImageName) as initImageObj:
    imgBytes = pil_to_base64(initImageObj)
    payload['init_images'] = [imgBytes]

#Send it
response = requests.post(url=f'{url}/sdapi/v1/img2img', json=payload)
#Get it back
r = response.json()
#it's possible to get multiple images, but usually it returns just 1
for img_data in r['images']:
    image = Image.open(io.BytesIO(base64.b64decode(img_data.split(",",1)[0])))

    png_payload = {
        "image": "data:image/png;base64," + img_data
    }
    response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("parameters", response2.json().get("info"))
    image.save('output.png', pnginfo=pnginfo)