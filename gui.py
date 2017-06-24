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



class App:
	def __init__(self, root):
		try:
			root.title('Image Compressor')

			logging.basicConfig(filename='log.txt', format='%(asctime)s (%(levelname)s): %(message)s', level=logging.WARNING)
			logging.captureWarnings(True)
			self.logger = logging.getLogger(__name__)

			self.selected_files = []
			self.file_opt = {'initialdir':'', 'filetypes':[('JPEGs and PNGs', '*.jpeg;*.jpg;*.png;')]}

			# read in settings, if available
			try:
				with open('settings.json', 'r') as f:
					settings = json.load(f)
				self.api_key = settings['api_key']
				self.out_directory = settings['output_folder']
				self.file_opt['initialdir'] = settings['input_folder']
			except IOError:
				self.api_key = ''
				self.out_directory = ''
				self.file_opt['initialdir'] = ''


			root.bind_all('<Control-q>', self.exit)

			self.make_GUI(root)

		except Exception as e:
			logging.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))
			sys.exit(0)

	def save_settings(self, new_settings = {}):
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
			self.compress_chk = ttk.Checkbutton(self.top_left_frame, text="compress?", \
												variable=self.compress_var, onvalue=True, offvalue=False)
			self.compress_chk.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

			self.resize_var = BooleanVar()
			self.resize_var.set(True)
			self.resize_chk = ttk.Checkbutton(self.top_left_frame, text="resize?", \
												variable=self.resize_var, onvalue=True, offvalue=False)
			self.resize_chk.grid(row=1, column=0, sticky="nw", padx=5, pady=5)

			self.key_lbl = ttk.Label(self.top_right_frame, text='TinyPNG API key')
			self.key_lbl.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

			self.key_var = StringVar()
			self.key_txt = ttk.Entry(self.top_right_frame, width=40, textvariable=self.key_var)
			self.key_txt.grid(row=0, column=1, columnspan=2, sticky="nw", padx=5, pady=5)
			self.key_txt.insert(0, self.api_key)

			self.dim_lbl = ttk.Label(self.top_right_frame, text="Max dimension")
			self.dim_lbl.grid(row=1, column=0, sticky="nw", padx=5, pady=5)

			self.dim_var = StringVar()
			self.dim_txt = ttk.Entry(self.top_right_frame, width=10, textvariable=self.dim_var)
			self.dim_txt.grid(row=1, column=1, sticky="nw", padx=5, pady=5)

			self.dim_units_var = StringVar()
			self.dim_units_var.set('px')
			self.dim_units_combo = ttk.Combobox(self.top_right_frame, textvariable=self.dim_units_var, width=4)
			self.dim_units_combo['values'] = ('px', 'in', 'cm')
			self.dim_units_combo.grid(row=1, column=1, sticky="ne", pady=5)

			self.res_lbl = ttk.Label(self.top_right_frame, text="Resolution (optional)")
			self.res_lbl.grid(row=2, column=0, sticky="nw", padx=5, pady=5)

			self.res_var = StringVar()
			self.res_txt = ttk.Entry(self.top_right_frame, width=10, textvariable=self.res_var)
			self.res_txt.grid(row=2, column=1, sticky="nw", padx=5, pady=5)

			############################################################
			# middle frame
			############################################################
			self.files_lbl = ttk.Label(self.middle_frame, text="Files to resize/compress")
			self.files_lbl.config(font=("Verdana",14))
			self.files_lbl.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

			self.files_btn = ttk.Button(self.middle_frame, text="Add Files...", command=self.add_files)
			self.files_btn.grid(row=0, column=1, sticky="nw", padx=5, pady=5)

			self.clear_btn = ttk.Button(self.middle_frame, text="Clear", command=self.clear_files)
			self.clear_btn.grid(row=0, column=1, sticky="ne", padx=5, pady=5)

			self.files_list = Listbox(self.middle_frame, width=87)
			self.files_list.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10, pady=10)
			self.files_scroll = ttk.Scrollbar(self.middle_frame)
			self.files_scroll.config(command = self.files_list.yview)
			self.files_list.configure(yscrollcommand = self.files_scroll.set)
			self.files_scroll.grid(row=1, column=1, sticky='nse', pady=10)

			############################################################
			# bottom frame
			############################################################
			self.out_dir_lbl = ttk.Label(self.bottom_frame, text="Output to")
			self.out_dir_lbl.grid(row=0, column=0, sticky='nw')

			self.out_dir_txt = Text(self.bottom_frame, height=1, width=50)
			self.out_dir_txt.grid(row=0, column=1, sticky='nw', padx=5)
			self.display_out_dir()

			self.out_dir_btn = ttk.Button(self.bottom_frame, text='Browse...', command=self.select_out_dir)
			self.out_dir_btn.grid(row=0, column=2, sticky='ne', padx=5)

			s = ttk.Style()
			s.configure('run.TButton', font=('Verdana', 16))
			self.execute_btn = ttk.Button(self.bottom_frame, text="Run", command=self.execute, style='run.TButton')
			self.execute_btn.grid(row=1, column=1, sticky='s', pady=5)
		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def display_out_dir(self):
		try:
			self.out_dir_txt.delete(1.0, END)
			self.out_dir_txt.insert(END, self.out_directory)
		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def select_out_dir(self):
		try:
			o = filedialog.askdirectory()

			#if user clicked cancel, we won't remove previously chosen folder
			if o != '':
				self.out_directory = o
				self.save_settings({'output_folder': o})
				self.display_out_dir()
		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def add_files(self):
		try:
			f = filedialog.askopenfilenames(**self.file_opt)

			#if user clicked cancel, we won't remove previously chosen files
			if len(f) > 0:
				self.selected_files = self.selected_files + list(f)

				# use directory of first file of selected files as initialdir, and save it
				#	as input_folder and	possibly output_folder (if out_directory not already specified)
				first_file_dir = os.path.split(os.path.abspath(f[0]))[0]
				self.file_opt['initialdir'] = first_file_dir
				self.save_settings({'input_folder': first_file_dir})

				if self.out_directory == '':
					self.out_directory = first_file_dir
					self.save_settings({'output_folder': first_file_dir})
					self.display_out_dir()

				self.display_files()
		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def display_files(self):
		try:
			self.files_list.delete(0,END)

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

	def execute(self):
		try:
			self.api_key = self.key_txt.get()
			self.save_settings({'api_key': self.api_key})

			if len(self.selected_files) == 0:
				messagebox.showerror("Error", "Select some files.")
				return
			if self.out_directory == '':
				messagebox.showerror("Error", "Select an out directory.")
				return
			if self.api_key == '':
				messagebox.showerror("Error", "Enter an API key.")
				return

			savings_KB = 0
			total_orig_size = 0

			for idx, file in enumerate(self.selected_files):
				total_orig_size = total_orig_size + os.stat(file).st_size/1024.

				#----------------------------------
				# Resize
				#----------------------------------
				if self.resize_var.get():
					print('Resizing "' + os.path.basename(file) + '" (' + str(idx+1) + ' of ' \
						+ str(len(self.selected_files)) + ')... ', end='')
					log = image_compressor.resize(file, out_dir=self.out_directory, suffix='_small')
					if not log['success']:
						messagebox.showerror("Error", log['message'])
						return
					else:
						print(log['message'])
						savings_KB = savings_KB + log['saved']


				#----------------------------------
				# Compress
				#----------------------------------
				if self.compress_var.get():
					print('Compressing "' + os.path.basename(file) + '" (' + str(idx+1) + ' of ' \
						+ str(len(self.selected_files)) + ')... ', end='')
					log = image_compressor.compress(api_key=self.api_key, file=log['result'], \
													out_dir=self.out_directory, suffix='')
					if not log['success']:
						messagebox.showerror("Error", log['message'])
						return
					else:
						print(log['message'])
						savings_KB = savings_KB + log['saved']


				# restore EXIF tags from original file to final result (they are stripped by PIL and TinyPNG)
				# PNGs don't have EXIF data, so skip this for them
				# Also, sometimes you get EXIF warnings from the piexif library when it tries to copy Unicode. Ignore those.
				if os.path.splitext(file)[1].lower() in ['.jpg','.jpeg']:
					piexif.transplant(file, log['result'])

			msg = 'Saved a total of ' + str(round(savings_KB, 0)) + ' KB = ' \
				+ str(round(savings_KB * 100 / total_orig_size, 1)) + '%'

			messagebox.showinfo("Compression successful", msg)

		except Exception as e:
			self.logger.error(e, exc_info=True)
			messagebox.showerror(e.__class__.__name__, str(e))

	def exit(self, event):
		sys.exit(0)


if __name__=='__main__':
	root = Tk()
	app = App(root)
	root.mainloop()