from __future__ import print_function
import os
import sys
import json
import logging
try:
	from Tkinter import *
	import tkFileDialog as filedialog
	import tkMessageBox as messagebox
	import ttk
except ImportError:
	from tkinter import *
	import tkinter.filedialog as filedialog
	import tkinter.messagebox as messagebox
	import tkinter.ttk as ttk
import piexif
import image_compressor


class ImageCompressor:
	def __init__(self, root=None):
		try:
			logging.basicConfig(filename='log.txt',
							format='%(asctime)s (%(levelname)s): %(message)s',
							level=logging.WARNING)
			logging.captureWarnings(True)
			self.logger = logging.getLogger(__name__)

			if root is not None:
				root.title('Image Compressor')

				self.selected_files = []
				self.file_opt = {'initialdir': '', 'filetypes': [('JPEGs and PNGs', '*.jpeg;*.jpg;*.png;')]}

				root.bind_all('<Control-q>', self.exit)

				self.make_GUI(root)

				# read in settings, if available
				try:
					with open('settings.json', 'r') as f:
						settings = json.load(f)

					self.api_key_var.set(settings['api_key'])
					self.out_dir_var.set(settings['output_folder'])
					self.file_opt['initialdir'] = settings['input_folder']
				except IOError:
					self.api_key_var.set('')
					self.out_dir_var.set('')
					self.file_opt['initialdir'] = ''

		except Exception as e:
			logging.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))
			sys.exit(0)

	def save_settings(self, new_settings={}):
		try:
			try:
				with open('settings.json', 'r') as f:
					settings = json.load(f)
			except IOError:
				settings = {}

			for key, val in new_settings.items():
				settings[key] = val

			with open('settings.json', 'w') as f:
				json.dump(settings, f)

		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def int_validate(self, S):
		return S == '' or S.isdigit()

	def make_GUI(self, root):
		try:
			self.top_frame = Frame(root)
			self.top_frame.pack(side="top", fill="x", expand=True)
			self.middle_frame = Frame(root)
			self.middle_frame.pack(side="top", fill="both", expand=True)
			self.bottom_frame = Frame(root)
			self.bottom_frame.pack(side="bottom", fill="x", expand=False)

			self.heading_lbl = ttk.Label(self.top_frame, text="Image Compressor")
			self.heading_lbl.config(font=("Verdana", 20))
			self.heading_lbl.pack(side="top")

			self.top_left_frame = Frame(self.top_frame)
			self.top_left_frame.pack(side="left", fill="y", expand=False)
			self.top_right_frame = Frame(self.top_frame)
			self.top_right_frame.pack(side="left", fill="both", expand=True)

			############################################################
			# top 1/3
			############################################################

			self.compress_var = BooleanVar()
			self.compress_var.set(True)
			self.compress_chk = ttk.Checkbutton(self.top_left_frame, text="compress?",
												variable=self.compress_var, command=self.toggle_compress,
												onvalue=True, offvalue=False)
			self.compress_chk.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

			self.resize_var = BooleanVar()
			self.resize_var.set(True)
			self.resize_chk = ttk.Checkbutton(self.top_left_frame, text="resize?",
												variable=self.resize_var, command=self.toggle_resize,
												onvalue=True, offvalue=False)
			self.resize_chk.grid(row=1, column=0, sticky="nw", padx=5, pady=5)

			self.api_key_lbl = ttk.Label(self.top_right_frame, text='TinyPNG API key')
			self.api_key_lbl.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

			self.api_key_var = StringVar()
			self.api_key_txt = Entry(self.top_right_frame, width=40, textvariable=self.api_key_var)
			self.api_key_txt.grid(row=0, column=1, columnspan=2, sticky="nw", padx=5, pady=5)

			self.dim_lbl = ttk.Label(self.top_right_frame, text="Max dimension")
			self.dim_lbl.grid(row=1, column=0, sticky="nw", padx=5, pady=5)

			intcmd = (self.top_right_frame.register(self.int_validate), '%S')

			self.dim_var = StringVar()
			self.dim_txt = ttk.Entry(self.top_right_frame, width=10, textvariable=self.dim_var,
									validate='key', validatecommand=intcmd)
			self.dim_txt.grid(row=1, column=1, sticky="nw", padx=5, pady=5)

			self.dim_units_var = StringVar()
			self.dim_units_var.set('px')
			self.dim_units_combo = ttk.Combobox(self.top_right_frame, textvariable=self.dim_units_var, width=4)
			self.dim_units_combo['values'] = ('px', 'in', 'cm')
			self.dim_units_combo.grid(row=1, column=1, sticky="ne", pady=5)

			############################################################
			# middle frame
			############################################################
			self.files_lbl = ttk.Label(self.middle_frame, text="Files to resize/compress")
			self.files_lbl.config(font=("Verdana", 14))
			self.files_lbl.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

			self.files_btn = ttk.Button(self.middle_frame, text="Add Files...", command=self.add_files)
			self.files_btn.grid(row=0, column=1, sticky="nw", padx=5, pady=5)

			self.clear_btn = ttk.Button(self.middle_frame, text="Clear", command=self.clear_files)
			self.clear_btn.grid(row=0, column=1, sticky="ne", padx=5, pady=5)

			self.files_list = Listbox(self.middle_frame, width=87)
			self.files_list.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10, pady=10)
			self.files_scroll = ttk.Scrollbar(self.middle_frame)
			self.files_scroll.config(command=self.files_list.yview)
			self.files_list.configure(yscrollcommand=self.files_scroll.set)
			self.files_scroll.grid(row=1, column=1, sticky='nse', pady=10)

			############################################################
			# bottom frame
			############################################################
			self.out_dir_lbl = ttk.Label(self.bottom_frame, text="Output to")
			self.out_dir_lbl.grid(row=0, column=0, sticky='nw')

			self.out_dir_var = StringVar()
			self.out_dir_txt = ttk.Entry(self.bottom_frame, width=50, textvariable=self.out_dir_var)
			self.out_dir_txt.grid(row=0, column=1, sticky='nw', padx=5)

			self.out_dir_btn = ttk.Button(self.bottom_frame, text='Browse...', command=self.select_out_dir)
			self.out_dir_btn.grid(row=0, column=2, sticky='ne', padx=5)

			s = ttk.Style()
			s.configure('run.TButton', font=('Verdana', 16))
			self.execute_btn = ttk.Button(self.bottom_frame, text="Run", command=self.execute_GUI, style='run.TButton')
			self.execute_btn.grid(row=1, column=1, sticky='s', pady=5)
		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def toggle_resize(self):
		self.dim_txt.config(state='normal' if self.resize_var.get() else 'disabled')
		self.dim_units_combo.config(state='normal' if self.resize_var.get() else 'disabled')
		#self.res_txt.config(state='normal' if self.resize_var.get() else 'disabled')

	def toggle_compress(self):
		self.api_key_txt.config(state='normal' if self.compress_var.get() else 'disabled')

	def select_out_dir(self):
		try:
			o = filedialog.askdirectory()

			# if user clicked cancel, we won't remove previously chosen folder
			if o != '':
				self.out_dir_var.set(o)
				self.save_settings({'output_folder': o})
		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def add_files(self):
		try:
			f = filedialog.askopenfilenames(**self.file_opt)

			# if user clicked cancel, we won't remove previously chosen files
			if len(f) > 0:
				self.selected_files = self.selected_files + list(f)

				# use directory of first file of selected files as initialdir, and save it
				# as input_folder and possibly output_folder (if out_directory not already specified)
				first_file_dir = os.path.split(os.path.abspath(f[0]))[0]
				self.file_opt['initialdir'] = first_file_dir

				if self.out_dir_var.get() == '':
					self.out_dir_var.set(first_file_dir)
					self.save_settings({'input_folder': first_file_dir,
										'output_folder': first_file_dir})
				else:
					self.save_settings({'input_folder': first_file_dir})

				self.display_files()
		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def display_files(self):
		try:
			self.files_list.delete(0, END)

			for file in self.selected_files:
				self.files_list.insert(END, file)

		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def clear_files(self):
		try:
			self.selected_files = []
			self.display_files()
		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def execute(self, files, out_dir, resize=True, max_dim=None, resize_units=None, compress=False, api_key=None):
		savings_KB = 0
		total_orig_size = 0

		for idx, file in enumerate(files):
			total_orig_size = total_orig_size + os.stat(file).st_size / 1024.
			log = None

			if(resize and max_dim is not None and str(max_dim).isdigit()):
				print('Resizing "' + os.path.basename(file) + '" (' + str(idx + 1) + ' of ' \
					+ str(len(files)) + ')... ', end='')

				if resize_units is None:
					resize_units = 'px'

				log = image_compressor.resize(file, out_dir=out_dir, suffix='_small',
												max_dim=max_dim, max_dim_units=resize_units)

				if not log['success']:
					return [False, log['message']]
				else:
					print(log['message'])
					savings_KB = savings_KB + log['saved']

			if(compress and api_key is not None):
				print('Compressing "' + os.path.basename(file) + '" (' + str(idx + 1) + ' of ' \
					+ str(len(files)) + ')... ', end='')

				in_file = log['result'] if log is not None else file

				log = image_compressor.compress(api_key=api_key, file=in_file,
												out_dir=out_dir, suffix='')
				if not log['success']:
					return [False, log['message']]
				else:
					print(log['message'])
					savings_KB = savings_KB + log['saved']

			# restore EXIF tags from original file to final result (they are stripped by PIL and TinyPNG)
			# PNGs don't have EXIF data, so skip this for them
			# Also, sometimes you get EXIF warnings from the piexif library when it tries to copy Unicode. Ignore those.
			if file[-4:].lower() in ['.jpg', 'jpeg']:
				try:
					piexif.transplant(file, log['result'])
				except Exception as e:
					# log the error, but not an issue (source might not have EXIF data)
					self.logger.error(e, exc_info=True)

		msg = 'Saved a total of ' + str(round(savings_KB, 0)) + ' KB = ' \
			+ str(round(savings_KB * 100 / total_orig_size, 1)) + '%'

		return [True, msg]

	def execute_GUI(self):
		try:
			if len(self.selected_files) == 0:
				messagebox.showerror("Error", "Select some files.")
				return
			if self.out_dir_var.get() == '':
				messagebox.showerror("Error", "Select an out directory.")
				return
			if self.api_key_var.get() == '':
				messagebox.showerror("Error", "Enter an API key.")
				return

			self.save_settings({'api_key': self.api_key_var.get(),
								'output_folder': self.out_dir_var.get()})

			x = self.execute(files=self.selected_files,
					out_dir=self.out_dir_var.get(),
					resize=self.resize_var.get(),
					max_dim=self.dim_var.get(),
					resize_units=self.dim_units_var.get(),
					compress=self.compress_var.get(),
					api_key=self.api_key_var.get())

			if not x[0]:
				messagebox.showerror("Error", x[1])
				return
			else:
				messagebox.showinfo("Resize/Compression successful", x[1])
				return

		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def exit(self, event):
		sys.exit(0)


if __name__ == '__main__':
	if len(sys.argv) == 1:
		# GUI app
		root = Tk()
		app = ImageCompressor(root)
		root.mainloop()
	else:
		# commandline app

		# defaults
		api_key = None
		resize = False
		compress = False
		dim = 1200

		""" command line args allowed:
		-i input_folder (if not specified, print error)
		-o output_folder (if not specified, assume input_folder)
		-resize (if not specified, don't resize; if neither resize nor compress, just resize)
		-d max_dimension (if not specified, assume 1200px)
		-compress (if not specified, don't compress. If specified without api key, print error)
		-k api_key (if not specified, print error if specified compress)
		"""
		if '-i' in sys.argv and len(sys.argv) > (sys.argv.index('-i') + 1):
			in_folder = sys.argv[sys.argv.index('-i') + 1]
			if not os.path.exists(in_folder):
				print("Bad input directory " + in_folder)
				sys.exit(0)

			files = [os.path.join(in_folder, f) for f in os.listdir(in_folder) if f[-4:].lower() in ['.jpg', '.png', 'jpeg']]

			if len(files) == 0:
				print("No files to resize/compress in specified input folder " + in_folder)
				sys.exit(0)

			out_folder = in_folder
		else:
			print("Input folder not specified")
			sys.exit(0)

		if '-o' in sys.argv:
			if len(sys.argv) <= (sys.argv.index('-o') + 1):
				print("-o specified, but did not include output folder")
				sys.exit(0)

			out_folder = sys.argv[sys.argv.index('-o') + 1]
			if not os.path.exists(out_folder):
				try:
					os.makedirs(out_folder)
				except OSError as exception:
					if exception.errno != errno.EEXIST:
						raise
						sys.exit(0)

		if '-resize' in sys.argv:
			resize = True
		if '-compress' in sys.argv:
			compress = True
			api_key = None
		if not resize and not compress:
			resize = True
			compress = False

		if resize and "-d" in sys.argv and len(sys.argv) > (sys.argv.index('-d') + 1):
			dim = sys.argv[sys.argv.index('-d') + 1]
			if dim.isdigit():
				dim = int(dim)
			else:
				print("Bad max dimension " + dim)
				sys.exit(0)

		if compress and "-k" in sys.argv and len(sys.argv) > (sys.argv.index("-k") + 1):
			api_key = sys.argv[sys.argv.index('-k') + 1]

		if compress and api_key is None:
			print("Specified -compress, but did not include TinyPNG API key")
			sys.exit(0)

		app = ImageCompressor()

		x = app.execute(files=files, out_dir=out_folder, resize=resize, max_dim=dim,
					resize_units='px', compress=compress, api_key=api_key)

		# print success or error message
		print(x[1])
