##############################
# Python script to resize and compress (using TinyPNG) all images in 
#	a directory.
# TinyPNG API: https://tinypng.com/developers/reference/python
# You can get a TinyPNG API key at https://tinypng.com/developers, which 
#	lets you run up to 500 compressions/resizes per month.

# inputs: jpg files selected by user
# outputs: new jpg files in output directory as specified by user, with suffix "_small", resized to
#	have 1200px as the max dimension (either width or height), compressed 
#	with TinyPNG.
##############################

import glob
import os
import sys
from PIL import Image, ExifTags  # Python Image Library, does the resizing
import errno  # used to check exception error number 
import tinify  # accesses TinyPNG API
import pyexiv2  # to restore EXIF tags after PIL strips them

tinify.key = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

# function taken from http://stackoverflow.com/a/5032238
def make_sure_path_exists(path):
	try:
		os.makedirs(path)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise


# function used to restore the EXIF tags destroyed by PIL
def restore_EXIF_tags(orig_file, final_file):
	if not os.path.isfile(orig_file) or not os.path.isfile(final_file):
		return
		
	f1 = pyexiv2.ImageMetadata(orig_file)
	f1.read()
	f2 = pyexiv2.metadata.ImageMetadata(final_file)
	f2.read() # yes, we need to read the contents of the destination EXIF tags before overwriting
	f2.modified = True
	f2.writable = os.access(final_file, os.W_OK)

	for exif_tag in f1.exif_keys:
		try:
			f2[exif_tag] = f1[exif_tag].value
			f2.write()
		except pyexiv2.exif.ExifValueError:
			pass

def resize_and_compress(files, out_dir):
	make_sure_path_exists(out_dir)

	out_files = []

	# keep track of disk space savings
	total_size_preresize = total_size_postresize = total_size_postcompress = 0

	####################################
	# resize with PIL (default: max dimension of 1200px--either width or height)
	####################################
	for idx, file in enumerate(files):

		print 'Resizing "' + os.path.basename(file) + '" (' + str(idx+1) + ' of ' \
			+ str(len(files)) + ')... ',

		orig_size = os.stat(file).st_size/1024.
		total_size_preresize = total_size_preresize + orig_size

		im = Image.open(file)

		# resize using LANCZOS, "a high-quality downsampling filter" 
		#	(from Pillow docs: http://pillow.readthedocs.io/en/3.0.x/reference/Image.html)
		w, h = im.size
		
		if w > h:
			im = im.resize((1200, int((1200.0/w)*h)), Image.LANCZOS)
		else:
			im = im.resize((int((1200.0/h)*w), 1200), Image.LANCZOS)


		# (out_dir + filename (without extension) + "_small" + extension)
		out_file = out_dir + '/' + os.path.splitext(os.path.basename(file))[0] + '_small' \
					+ os.path.splitext(file)[1]
		out_files.append(out_file)
		im.save(out_file)

		final_size = os.stat(out_file).st_size/1024.
		total_size_postresize = total_size_postresize + final_size

		print 'Done! (resizing saved ' + str(round(orig_size - final_size,0)) + ' KB = ' \
				+ str(round((orig_size - final_size) * 100.0 / orig_size, 1)) + '%)'

	print 'Finished! Altogether, resizing saved ' + str(round(total_size_preresize - total_size_postresize, 0)) + ' KB = ' \
		+ str(round((total_size_preresize - total_size_postresize) * 100 / total_size_preresize, 1)) + '%'

	####################################
	# compress with tinyPNG
	####################################

	if tinify.compression_count >= 500:
		print 'Cannot do any more compressions - already compressed 500 images!'
	else:
		
		# NOTE: we're now using the output from the resizing step as the input to this step
		for idx, file in enumerate(out_files):
			for attempt in range(5):
				try:
					print 'Compressing "' + os.path.basename(file) + '" (' + str(idx+1) + ' of ' + str(len(files)) + ')... ',

					orig_size = os.stat(file).st_size/1024.
					
					source = tinify.from_file(file)
					
					# if the PIL-resized files kept the EXIF date taken, we could use this code
					#	to keep it during compression
					# source = source.preserve("creation")

					source.to_file(file)

					# restore EXIF tags (destroyed by PIL)
					restore_EXIF_tags(orig_file = files[idx],
									final_file = file)

					
					final_size = os.stat(file).st_size/1024.
					total_size_postcompress = total_size_postcompress + final_size
					
					print 'Done! (saved ' + str(round(orig_size-final_size,0)) + ' KB = ' + str(round((orig_size-final_size)*100.0/orig_size,1)) + '%)'
					
					break # out of attempt loop

				except tinify.AccountError, e:
					print "Compression limit reached! The error message is: %s" % e.message
					raise e

			else:
				# no break encountered--failed all attempts
				raise Exception('ServerError kept happening')

		print 'Finished! Compression saved ' + str(round(total_size_postresize - total_size_postcompress,0)) + ' KB = ' \
				+ str(round((total_size_postresize - total_size_postcompress) * 100 / total_size_postresize, 1)) + '%'

		print 'Resizing and compressing together saved ' + str(round(total_size_preresize - total_size_postcompress,0)) + ' KB = ' \
				+ str(round((total_size_preresize - total_size_postcompress) * 100 / total_size_preresize, 1)) + '%'

		return True