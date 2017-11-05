##############################
# Python module to resize and compress (using TinyPNG) all images in a directory.
# TinyPNG API: https://tinypng.com/developers/reference/python
# You can get a TinyPNG API key at https://tinypng.com/developers, which lets you run up to
#	500 compressions/resizes per month.
##############################

import glob
import os
import sys
from PIL import Image, ExifTags  # Python Image Library, does the resizing
import errno  # used to check exception error number
import tinify  # accesses TinyPNG API

# check specified path exists; if it doesn't, create it
# function taken from http://stackoverflow.com/a/5032238
def make_sure_path_exists(path):
	try:
		os.makedirs(path)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

def resize(file, out_dir='', suffix='_small', max_dim=None, max_dim_units='px', new_res=None):
	"""Resize image using Pillow, specifically using LANCZOS, "a high-quality downsampling filter"
	(from Pillow docs: http://pillow.readthedocs.io/en/3.0.x/reference/Image.html)

	Parameters
	----------
	file : string
		name of input file to resize
	out_dir : string
		(optional) directory in which to store the output file. Default = directory of input file.
	suffix : string
		(optional) suffix to add to the output file name
	max_dim : integer
		(optional) maximum dimension on a side. If None, set to 1200 pixels
	new_res : float
		(optional) new resolution, in pixels. If None, do not change resolution

	Returns
	-------
	dict
		Contains the following keys:
			success : bool
				indicates whether operation was successful
			message : string
				if success = False, reason for failure
				if success = True, message like 'Resize complete! (saved ## KB = ##%)'
			result : string
				full path of the resulting file
			saved : float
				space savings in KB
	"""

	if not os.path.isfile(file):
		return {'success':False, 'message':'File does not exist', 'result':'', 'saved':0}

	if out_dir == '':
		# use the same path as the input file
		out_dir = os.path.split(os.path.abspath(file))[0]
	else:
		make_sure_path_exists(out_dir)

	try:
		int(max_dim)
	except:
		max_dim = 1200

	max_dim_units = max_dim_units.lower() if max_dim_units in ['px','in','cm'] else 'px'

	try:
		int(new_res)
	except:
		new_res = None


	# out_dir + filename (without extension) + suffix + extension
	out_file = out_dir + '/' \
				+ os.path.splitext(os.path.basename(file))[0] + suffix + os.path.splitext(file)[1]


	orig_size = os.stat(file).st_size/1024.
	max_dim = int(max_dim)

	im = Image.open(file)
	w, h = im.size

	if w > h:
		im = im.resize((int(max_dim), int((float(max_dim)/w)*h)), Image.LANCZOS)
	else:
		im = im.resize((int((float(max_dim)/h)*w), int(max_dim)), Image.LANCZOS)

	# note: new file has no EXIF tags
	im.save(out_file)

	final_size = os.stat(out_file).st_size/1024.

	return {'success':True,
			'message':'Resize complete! (saved ' + str(round(orig_size - final_size, 0)) + ' KB = '\
						+ str(round((orig_size - final_size) * 100.0 / orig_size, 1)) + '%)',
			'result': out_file,
			'saved': orig_size - final_size}


def compress(api_key, file, out_dir='', suffix='_tiny' ):
	"""Compress image using TinyPNG.

	Parameters
	----------
	api_key : string
		API key from TinyPNG. From https://tinypng.com/developers (available: up to 500 compressions/resizes per month)
	file : string
		name of input file to resize
	out_dir : string
		(optional) directory in which to store the output file. Default = directory of input file.
	suffix : string
		(optional) suffix to add to the output file name

	Returns
	-------
	dict
		Contains the following keys:
			success : bool
				indicates whether operation was successful
			message : string
				if success = False, reason for failure
				if success = True, message like 'Compression complete! (saved ## KB = ##%)'
			result : string
				full path of the resulting file
			saved : float
				space savings in KB

	"""

	if not os.path.isfile(file):
		return {'success':False, 'message':'File does not exist', 'result':'', 'saved':0}

	if out_dir == '':
		# use the same path as the input file
		out_dir = os.path.split(os.path.abspath(file))[0]
	else:
		make_sure_path_exists(out_dir)

	# out_dir + filename (without extension) + suffix + extension
	out_file = out_dir + '/' \
				+ os.path.splitext(os.path.basename(file))[0] + suffix + os.path.splitext(file)[1]

	orig_size = os.stat(file).st_size/1024.


	tinify.key = api_key

	for attempt in range(5):
		try:
			source = tinify.from_file(file)
			source.to_file(out_file) # runs the compression
			break # out of attempt loop

		except tinify.AccountError as e:
			return {'success':False, \
					'message':"Compression limit reached! The error message is: %s" % e.message, \
					'result':'',
					'saved':0}

		except Exception as e:
			return {'success':False, \
					'message':"Unexpected error. The error message is: %s" % e.message, \
					'result':'',
					'saved':0}
	else:
		# failed all attempts (no break encountered)
		return {'success':False, \
				'message':'Encountered ServerError five times. Aborted compression.', \
				'result':'',
				'saved':0}

	final_size = os.stat(out_file).st_size/1024.

	return {'success':True,
			'message':'Compression complete! (saved ' + str(round(orig_size - final_size, 0)) + ' KB = '\
						+ str(round((orig_size - final_size) * 100.0 / orig_size, 1)) + '%)',
			'result':out_file,
			'saved': orig_size - final_size}