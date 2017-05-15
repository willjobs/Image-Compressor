##############################
# Script to compress images with TinyPNG
# API: https://tinypng.com/developers/reference/python
# inputs: 1) photos (after resizing with resize.py gimp plug-in), located by default in <src dir>/resized
#		  2) API key from TinyPNG. You can get an API key at https://tinypng.com/developers, which lets you run
#				up to 500 compressions/resizes per month.
# outputs: tinyPNG compressed jpg files in output folder
#
##############################
from __future__ import print_function # python 2 compatibility
import glob
import os
import tinify
import sys

def main(argv):
	in_path = sys.argv[1]
	out_path = sys.argv[2]
	try:
		tinify.key = sys.argv[3]
		tinify.validate
	except tinify.Error as e:
		print('Validation of API key failed.')

	if tinify.compression_count is not None and tinify.compresion_count >= 500:
		print('Cannot do any more compressions - already compressed 500 images!')
	else:
		count = 0
		files = glob.glob(in_path + '/*.jpg')
		total_origsize = 0
		total_finalsize = 0

		for file in files:
			for attempt in range(5):
				try:
					orig_size = os.stat(file).st_size/1024.
					total_origsize = total_origsize + orig_size
					out_file = out_path + '/' + os.path.basename(file)
					
					source = tinify.from_file(file)
					source = source.preserve("creation")
					source.to_file(out_file)
					
					final_size = os.stat(out_file).st_size/1024.
					total_finalsize = total_finalsize + final_size
					count = count + 1
					print('Compressed ' + os.path.basename(file) \
						+ ' (saved ' + str(round(orig_size-final_size,0)) + ' KB = ' + str(round((orig_size-final_size)*100.0/orig_size,1)) + '%)' \
						+ ' (file ' + str(count) + ' of ' + str(len(files)) + ')')
					
					break # out of attempt loop

				except tinify.AccountError as e:
					print("Compression limit reached! The error message is: %s" % e.message)
					raise e
				except tinify.ServerError:
					total_origsize = total_origsize - orig_size
			else:
				# no break encountered--failed all attempts
				raise Exception('ServerError kept happening')

		print('Finished! Compressed ' + str(count) + ' images. Saved ' + str(round(total_origsize-total_finalsize,0)) + ' KB = ' + str(round((total_origsize-total_finalsize)*100/total_origsize,1)) + '%')

if __name__ == "__main__":
	main(sys.argv[1:])