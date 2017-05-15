##############################
# GIMP script to compress all images in a directory
# inputs: jpg files located in folder
# output: new jpg files in folder/out, 
#			resized to have 1200px as the max dimension (either width or height). 
##############################
import os
import sys
from gimpfu import *

def resize(folder):
	for file in os.listdir(folder):
		if not (file.lower().endswith(('.jpeg', '.jpg'))):
			continue
		path = folder + "\\" + file
		image = pdb.gimp_file_load(path, '?')
		# increase resolution to 100dpi and change max dimension to 1200px
		w = image.width
		h = image.height
		if w > h:
			pdb.gimp_image_scale(image, 1200, (1200.0/w)*h)
		else:
			pdb.gimp_image_scale(image, (1200.0/h)*w, 1200)
		pdb.gimp_image_set_resolution(image, 100, 100)
		# save image (most efficient way: first copy, merge down, save, delete the reference in memory to the duplicate)
		new_image = pdb.gimp_image_duplicate(image)
		layer = pdb.gimp_image_merge_visible_layers(new_image, CLIP_TO_IMAGE)
		pdb.gimp_file_save(new_image, layer, folder + '\\resized\\' + file, '?')
		pdb.gimp_image_delete(new_image)

register(
	"python_fu_resize",
	"resize",
	"",
	"",
	"",
	"",
	"<Toolbox>/MyScripts/resize",
	"*",
	[
		(PF_DIRNAME, "folder", "Input directory", "")
	],
	[],
	resize)

main()