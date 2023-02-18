# MG-SD-tools
Mark Gilliland's Stable Diffusion Tools

## About
Stable Diffusion is a project (*NOT MINE*) that does some really cool image generation from just text prompts. 
I am not contributing to Stable Diffusion, but I am using it with these scripts. This is my "sandbox" for using Stable Diffusion.

## Scripts
### txt2img_evaluator.py
This is really useful for comparing the impact of different parameters on images generated. The script iterates over any arguments accepted by the WebUI API's txt2img function, such as ```prompt, steps, sampler_index```and more.

## Prerequisites (Windows)
1. Install Stable Diffusion via the [Automatic1111 WebUI Installer](https://github.com/AUTOMATIC1111/stable-diffusion-webui)  
  a. Get the checkpoing file from the official Stable Diffusion source.
  b. Change the command line arguments in webui-user.bat to contain "--api" (to allow access to the WebUI API)
  c. Run apiTest.py (in this repository, not the Automatic1111 repo) to verify you have the WebUI API set up properly
2. You will need the PIL library (for image processing)




