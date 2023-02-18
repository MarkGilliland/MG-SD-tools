"""
Mark Gilliland, Feb 2023

This code opens sweeps over a lot of parameters for txt2img and annotates the images produced
"""
import json
import requests
import io
import base64
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin #https://pillow.readthedocs.io/en/stable/reference/Image.html
from pathlib import Path
from copy import deepcopy

url = "http://127.0.0.1:7860"

outputDir = Path('output')

def generateImage(payload):
    """
    Takes in a payload (prompt info) and returns a PIL.Image object of that image
    """
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)

    r = response.json()

    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

        #PNG Info stuff removed for now
        # png_payload = {
        #     "image": "data:image/png;base64," + i
        # }
        # response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

        # pnginfo = PngImagePlugin.PngInfo()
        # pnginfo.add_text("parameters", response2.json().get("info"))
        # print(pnginfo)

        return image

def saveImage(imgToSave, title):
    """
    saves the image in the appropriate directory (outputDir, declared as global) with the given title
    """
    pngFilename = Path(f'{title}.png')
    imgToSave.save(outputDir / pngFilename)


imageParams = {
    'prompt': ['A really cool airplane flying over a city, realistic'],
    'steps': [20],
    'sampler_index': ['Euler a', 'Euler', 
                        'LMS', 'Heun', 
                        'DDIM', 'PLMS',
                        'DPM2', 'DPM2 a', 
                        'DPM++ 2S a', 'DPM++ 2M', 
                        'DPM++ SDE', 'DPM fast', 
                        'DPM adaptive', 'LMS Karras', 
                        'DPM2 Karras', 'DPM2 a Karras', 
                        'DPM++ 2S a Karras', 'DPM++ 2M Karras',
                        'DPM++ SDE Karras'
                        ],
    'seed': [1, 2, 3],
    'height':512,
    'width':512
}

#Sort into dynamic (changing) and static (unchanging) imageParams
dynImgParams = {}
staticImgParams = {}

for key, val in imageParams.items():
    if type(val) == type(["list"]):
        if len(val) > 1:
            #if a dynamic param
            dynImgParams[key] = val
        elif len(val) == 1:
            #if a list with just 1 val, so a static param
            staticImgParams[key] = val[0]
    else:
        #if just a value, so a static param
        staticImgParams[key] = val

print("dynParams")
print(dynImgParams)
print("staticParams")
print(staticImgParams)

#find the total number of iterations
nIter = 1
for param, vals in dynImgParams.items():
    nIter = nIter*len(vals)
#Global for progress bar tracking
iterCounter = 0

def updateProgress(imgName):
    global iterCounter
    print(f'{(iterCounter/nIter)*100:0.1f}% Complete, working on {imgName}')
    iterCounter = iterCounter+1


#Some image drawing stuff
captionH = 40
captionFont = ImageFont.truetype('resources/Arial.ttf', 20)
borderThickRatio = 0.01#how much of a border is added between images


def getImageName(params):
    """
    Provides a consistent way to name an image so it  can be looked up by stitchImages
    """
    name = ''
    # for key in params.keys():
    #     if key not in dynImgParams:
    #         print("Warning: param {key} was used as a dynamic parameter but should be static")
    for paramName in dynImgParams.keys():
        val = params[paramName]
        name = name + f'{paramName}={val} '
    name = name.strip()
    return name

def captionImg(img, name):
    """
    Adds a block of text under the image
    """
    
    a = Image.new('RGB', (img.width, img.height + captionH))
    a.paste(img, (0,0))
    b = ImageDraw.Draw(a)
    b.text((0, img.height), name, font=captionFont, fill=(255, 255, 255))
    return b._image

def stitchImages(imgs):
    """
    Arranges images into a horizontal line or vertical line. Assumes they are all the same size
    
    Takes in imgs, an array of img objects
    Returns 1 image object
    """
    imgW = imgs[0].width
    imgH = imgs[0].height
    nImg = len(imgs)

    horizTiling = imgW < imgH#if true, tile Horizontally, otherwise Vertically

    if horizTiling:#if horizontal
        borderThick = int(imgW*borderThickRatio)
        mainImg = Image.new('RGB', ( (imgW+borderThick)*nImg, imgH+borderThick) )
        for i in range(nImg):
            img = imgs[i]
            x = int(borderThick/2) + ((imgW+borderThick)*i)
            y = int(borderThick/2)
            mainImg.paste(img, (x, y))

    else:#if vertical
        borderThick = int(imgH*borderThickRatio)
        mainImg = Image.new('RGB', ( imgW+borderThick, (imgH+borderThick)*nImg ) )
        for i in range(nImg):
            img = imgs[i]
            x = int(borderThick/2)
            y = int(borderThick/2) + ((imgH+borderThick)*i)
            mainImg.paste(img, (x, y))

    return mainImg



def iterOverImgParams(dynParams, staticParams):
    """
    Iterate over all image parameters given. This is done recursively to allow for 
    an arbitrary amount of arguments
    """

    if dynParams == None or dynParams == {}:
        #base case, no params are dynamic all are static
        name = getImageName(staticParams)
        updateProgress(name)
        img = generateImage(payload=staticParams)
        captionedImg = captionImg(img, name)
        return captionedImg

    else:
        thisIterDynParams = deepcopy(dynParams)
        thisIterKey = list(thisIterDynParams.keys())[0]
        thisIterVal = thisIterDynParams.pop(thisIterKey)#removes the iterm from dynParams

        imgs = []
        for val in thisIterVal:
            newStaticParams = deepcopy(staticParams)
            newStaticParams[thisIterKey] = val
            img = iterOverImgParams(dynParams=thisIterDynParams, staticParams=newStaticParams)
            imgs.append(img)
        return stitchImages(imgs)

masterImg = iterOverImgParams(dynImgParams, staticImgParams)
saveImage(masterImg, 'output')

# for p in prompts:
#     for s in steps:
#         payload = {
#             "prompt": p,
#             "steps": s
#         }

#         title = str(p) + str(s)
#         img = generateImage(payload)
#         saveImage(img, title)