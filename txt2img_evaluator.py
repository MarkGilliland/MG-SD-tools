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
import time

url = "http://127.0.0.1:7860"

outputDir = Path('output')

def generateImage(payload):
    """
    Takes in a payload (prompt info) and returns a PIL.Image object of that image
    """
    payload = deepcopy(payload)
    if 'time' in payload.keys():#Time is a special argument I'm popping out here and replacing with steps, normalized to the speed of each algorithm
        t = payload.pop('time') - setupTime
        resolutionFactor = (payload['height']*payload['width']) / timePerStepResolution
        nSteps = round(t / (timePerStep[payload['sampler_index']] * resolutionFactor))
        if nSteps < 1:
            nSteps = 1
        payload['steps'] = nSteps
    if 'img_style' in payload.keys():#Appends strings like "trending on artstation" to the prompt
        style = payload.pop('img_style')
        payload['prompt'] = payload['prompt'] + ', ' + style

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

#special params are called out in generateImage
# These include:
# time (subtitutes 'steps')
# img_style (appends strings to the prompt)
imageParams = {
    'prompt': ['An astronaut exploring under the ocean'],
    'img_style': ['cinematic', 'space', 'wallpaper'],
    'restore_faces': [True, False],
    'negative_prompt': 'border, frame, poorly drawn, bad, fingers, black and white',
    'time': [5],
    'sampler_index': ['Heun', 'DPM++ SDE Karras'],
    'cfg_scale': [7],
    'seed': [5, 6],
    'height':512,
    'width':512
}
# Full sampler_index below: (except adaptive)
# 'sampler_index': ['Euler a', 'Euler', 
#                     'LMS', 'Heun', 
#                     'DDIM', 'PLMS',
#                     'DPM2', 'DPM2 a', 
#                     'DPM++ 2S a', 'DPM++ 2M', 
#                     'DPM++ SDE', 'DPM fast', 'LMS Karras', 
#                     'DPM2 Karras', 'DPM2 a Karras', 
#                     'DPM++ 2S a Karras', 'DPM++ 2M Karras',
#                     'DPM++ SDE Karras'
#                     ]

#seconds per step, ish, done on a test with 50 steps
timePerStep = {'Euler a': 0.084,
                'Euler': 0.08,
                'LMS': 0.08,
                'Heun': 0.162,
                'DDIM': 0.08,
                'PLMS': 0.082,
                'DPM2': 0.166,
                'DPM2 a': 0.166,
                'DPM++ 2S a': 0.164,
                'DPM++ 2M': 0.08,
                'DPM++ SDE': 0.17,
                'DPM fast': 0.08,
                'LMS Karras': 0.08,
                'DPM2 Karras': 0.162,
                'DPM2 a Karras': 0.162,
                'DPM++ 2S a Karras': 0.164,
                'DPM++ 2M Karras': 0.08,
                'DPM++ SDE Karras': 0.17}
setupTime = 0.4
timePerStepResolution = 512*512





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
timerStart = time.perf_counter()
batchStartTime = time.perf_counter()
def updateProgress(imgName):
    global iterCounter, timerStart
    ratioComplete = (iterCounter/nIter)
    print(f'{ratioComplete*100:0.1f}% Complete, working on {imgName}')
    

    # if iterCounter > 0:
    #     totalElapsedTime = time.perf_counter() - batchStartTime
    #     timeRemaining = (totalElapsedTime*ratioComplete)/(1-ratioComplete)
    #     hours, remainder = divmod(timeRemaining, 3600)
    #     minutes, seconds = divmod(remainder, 60)
    #     seconds = int(seconds)
    #     if hours > 0:
    #         print(f"Estimated Time Remaining: {hours}h{minutes:02d}m{seconds:02d}s")
    #     elif minutes > 0:
    #         print(f"Estimated Time Remaining: {minutes:02d}m{seconds:02d}s")
    #     else:
    #         print(f"Estimated Time Remaining: {seconds} seconds")

    iterCounter = iterCounter+1
    timerStart = time.perf_counter()



def printTimer(note="That"):
    global timerStart
    now = time.perf_counter()
    print(f"{note} took {now-timerStart:0.1f}s")


#Some image drawing stuff
captionHeightRatio = 0.05
catLabelRatio = 0.07
fontRatioOfHeight = 0.7
borderThickRatio = 0.03#how much of a border is added between images
captionFontName = 'resources/fonts/NotoMono-Regular.ttf'


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

def resizeFontForGivenWidth(text, widthNeeded, heightNeeded, maxFontSize, fontStr):
    """
    returns new text (might have some newlines)
    and a new font object (proper size)
    """
    newText = deepcopy(text)
    fontSize = maxFontSize
    fontObj = ImageFont.truetype(fontStr, fontSize)
    while True:
        fontObj.getlength(newText) > widthNeeded
        fontSize = fontSize - 1
        fontObj = ImageFont.truetype(fontStr, fontSize)
        (left, top, right, bottom) = fontObj.getbbox(newText)
        bboxH = bottom-top
        bboxW = right-left
        #if it fits, exit
        if bboxH <= heightNeeded and bboxW <= widthNeeded:
            break
        #if height is under half of required, add a newline
        if bboxH < heightNeeded*0.48 and newText.find('\n') == -1:
            midpointTxt = round(len(newText)/2)
            halfwaySpace = newText[midpointTxt:].find(' ') + midpointTxt
            if halfwaySpace != -1:
                newText = newText[:halfwaySpace] + '\n' + newText[halfwaySpace+1:]
                print("added space, new string is:")
                print(newText)
    return (newText, fontObj)

def captionImg(img, params, paramKeys):
    """
    Adds a block of text under the image
    """
    captionH = round(img.height * captionHeightRatio)
    
    nParams = len(paramKeys)

    a = Image.new('RGB', (img.width, img.height + captionH*nParams))
    a.paste(img, (0,0))
    b = ImageDraw.Draw(a)
    for i in range(nParams):
        paramName = list(paramKeys)[i]
        x = 0
        y = img.height + i*captionH
        paramStr = f' {paramName}: {params[paramName]}'
        paramStr, captionFont = resizeFontForGivenWidth(paramStr, widthNeeded=img.width, heightNeeded=captionH,
                                             maxFontSize=round(captionH*fontRatioOfHeight), 
                                             fontStr=captionFontName)
        b.text((x, y), paramStr, font=captionFont, fill=(255, 255, 255), anchor='la')
    return b._image
def stitchImages(imgs, paramName, paramVals):
    """
    Arranges images into a horizontal line or vertical line. Assumes they are all the same size
    
    Takes in imgs, an array of img objects
    Returns 1 image object

    adds some words at the top describing the parameter changed between photos
    """
    imgW = imgs[0].width
    imgH = imgs[0].height
    nImg = len(imgs)

    horizTiling = imgW < imgH#if true, tile Horizontally, otherwise Vertically

    if horizTiling:#if horizontal
        borderThick = int(imgW*borderThickRatio)
        catLabelHeight = round(catLabelRatio*imgH)
        mainImg = Image.new('RGB', ( (imgW+borderThick)*nImg, imgH+borderThick+catLabelHeight) )
        for i in range(nImg):
            img = imgs[i]
            x = int(borderThick/2) + ((imgW+borderThick)*i)
            y = int(borderThick/2) + catLabelHeight
            mainImg.paste(img, (x, y))

            #now, add labels
            mainImgDraw = ImageDraw.Draw(mainImg)#draw obj for labels, might be bad performance but oh well
            labelX = round(x + (imgW/2))
            labelY = catLabelHeight
            paramLabel = f'{paramName}:{paramVals[i]}'
            paramLabel, catLabelFont = resizeFontForGivenWidth(text=paramLabel, widthNeeded=imgW, heightNeeded=catLabelHeight,
                                            maxFontSize=round(catLabelHeight*fontRatioOfHeight), 
                                            fontStr=captionFontName)
            mainImgDraw.text((labelX, labelY), paramLabel,font=catLabelFont, fill=(255, 255, 255), anchor='md')

            mainImg = mainImgDraw._image#'write' the labels back onto the main image


    else:#if vertical
        borderThick = int(imgH*borderThickRatio)
        catLabelWidth = round(catLabelRatio*imgW)
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
        printTimer()
        captionedImg = captionImg(img, staticParams, paramKeys=dynImgParams.keys())
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
        return stitchImages(imgs=imgs, paramName=thisIterKey, paramVals=thisIterVal)

masterImg = iterOverImgParams(dynImgParams, staticImgParams)
masterImg = captionImg(masterImg, staticImgParams, paramKeys=staticImgParams.keys())
saveImage(masterImg, 'output')
masterImg.show()

# for p in prompts:
#     for s in steps:
#         payload = {
#             "prompt": p,
#             "steps": s
#         }

#         title = str(p) + str(s)
#         img = generateImage(payload)
#         saveImage(img, title)