##############################
# GIMP script to compress all images in a directory
# inputs: jpg files located at C:/Users/Will/Desktop/Photos/*.jpg
# output: new jpg files in same directory as above, with same filenames plus a suffix of _small, 
#			resized to have 1200px as the max dimension (either width or height). 
##############################
import glob
import os
import sys
files = glob.glob('C:/Users/Will/Desktop/Photos/*.jpg')
for idx, file in enumerate(files):
	image = pdb.gimp_file_load(file, '?')
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
	pdb.gimp_file_save(new_image, layer, os.path.abspath(file).split('.')[0] + '_small.jpg', '?')
	pdb.gimp_image_delete(new_image)