import os, sys
import shelve
import Tkinter, tkFileDialog, tkMessageBox
from PIL import Image, ImageTk
import piexif
import warnings
import image_compressor


class App:

	def __init__(self, root):
		root.title('Image Compressor')

		self.selected_files = []
		self.file_opt = {'initialdir':'', 'filetypes':[('JPEGs and PNGs', '*.jpeg;*.jpg;*.png;')]}

		settings = shelve.open('settings')
		self.api_key = settings['api_key'] if settings.has_key('api_key') else ''		
		self.out_directory = settings['output_folder'] if settings.has_key('output_folder') else ''
		self.file_opt['initialdir'] = settings['input_folder'] if settings.has_key('input_folder') else ''
		settings.close()

		self.file_display = FileDisplay(root, self)
		self.options = Options(root, self)

		root.geometry('810x450')
		root.minsize(width=810, height=350)

		root.grid_columnconfigure(0, weight=1, uniform="a")
		root.grid_columnconfigure(1, weight=1, uniform="a")
		root.grid_rowconfigure(0, weight=1)

		root.bind_all('<Control-q>', self.exit)

	def save_setting(self, setting_name, val):
		settings = shelve.open('settings')
		settings[setting_name] = val
		settings.close()

	def select_files(self):
		f = tkFileDialog.askopenfilenames(**self.file_opt)
		
		#if user clicked cancel, we won't remove previously chosen files
		if len(f) > 0:
			self.selected_files = f

			# use first file's directory as initialdir, and save it as input_folder and
			#	possibly output_folder (if out_directory not already specified)
			first_file_dir = os.path.split(os.path.abspath(self.selected_files[0]))[0]
			self.file_opt['initialdir'] = first_file_dir
			self.save_setting('input_folder', first_file_dir)

			if self.out_directory == '':
				self.out_directory = first_file_dir
				self.save_setting('output_folder', first_file_dir)
				self.options.display_out_dir()

			self.file_display.display()

	def select_out_dir(self):
		o = tkFileDialog.askdirectory()
		
		#if user clicked cancel, we won't remove previously chosen folder
		if o != '':
			self.out_directory = o
			self.save_setting('output_folder', o)
			self.options.display_out_dir()

	def execute(self):
		self.api_key = self.options.key.get()
		self.save_setting('api_key', self.api_key)

		if len(self.selected_files) == 0:
			tkMessageBox.showerror("Error", "Select some files.")
			return
		if self.out_directory == '':
			tkMessageBox.showerror("Error", "Select an out directory.")
			return
		if self.api_key == '':
			tkMessageBox.showerror("Error", "Enter an API key.")
			return


		savings_KB = 0
		total_orig_size = 0

		for idx, file in enumerate(self.selected_files):
			total_orig_size = total_orig_size + os.stat(file).st_size/1024.

			#----------------------------------
			# Resize
			#----------------------------------
			print 'Resizing "' + os.path.basename(file) + '" (' + str(idx+1) + ' of ' \
				+ str(len(self.selected_files)) + ')... ',
			log = image_compressor.resize(file, out_dir=self.out_directory, suffix='_small')
			if not log['success']:
				tkMessageBox.showerror("Error", log['message'])
				return
			else:
				print log['message']
				savings_KB = savings_KB + log['saved']


			#----------------------------------
			# Compress
			#----------------------------------
			print 'Compressing "' + os.path.basename(file) + '" (' + str(idx+1) + ' of ' \
				+ str(len(self.selected_files)) + ')... ',
			log = image_compressor.compress(api_key=self.api_key, file=log['result'], out_dir=self.out_directory, suffix='')
			if not log['success']:
				tkMessageBox.showerror("Error", log['message'])
				return
			else:
				print log['message']
				savings_KB = savings_KB + log['saved']


			# restore EXIF tags from original file to final result (they are stripped by PIL and TinyPNG)
			# PNGs don't have EXIF data, so skip this for them
			# Also, sometimes you get EXIF warnings from the piexif library when it tries to copy Unicode. Ignore those.
			warnings.filterwarnings('ignore', category=UnicodeWarning)
			if os.path.splitext(file)[1].lower() in ['.jpg','.jpeg']:
				try:
					piexif.transplant(file, log['result'])
				except UnicodeWarning:
					pass
			warnings.resetwarnings()

		print 'Resizing and compressing together saved ' + str(round(savings_KB,0)) + ' KB = ' \
			+ str(round(savings_KB * 100 / total_orig_size, 1)) + '%'

		tkMessageBox.showinfo("Compression successful", "Finished!")

	def exit(self, event):
		sys.exit(0)


class FileDisplay:

	def __init__(self, parent, app):
		self.app = app

		self.frame = Tkinter.Frame(parent, bd=10)
		self.frame.grid(row=0, column=0, sticky='nsew')

		self.select_files_button = Tkinter.Button(self.frame, text="Select Files", command=app.select_files)
		self.select_files_button.pack(anchor=Tkinter.NW)

		self.scrollbar = Tkinter.Scrollbar(self.frame)
		self.txt = Tkinter.Text(self.frame, yscrollcommand=self.scrollbar.set, width=45, state=Tkinter.DISABLED)
		self.txt.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT, pady=5)
		self.scrollbar.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=5)
		self.scrollbar.config(command=self.txt.yview)

	def display(self):
		# delete existing files from display
		self.txt.config(state=Tkinter.NORMAL)
		self.txt.delete(1.0, Tkinter.END)

		# add selected files to display
		if len(self.app.selected_files) > 0:
			self.txt.insert(Tkinter.END, self.app.selected_files[0])
			for file in self.app.selected_files[1:]:
				self.txt.insert(Tkinter.END, '\n' + file)

		self.txt.config(state=Tkinter.DISABLED)

class Options:
	def __init__(self, parent, app):
		self.app = app

		self.frame = Tkinter.Frame(parent, bd=10)
		self.frame.grid(row=0, column=1, sticky='nsew', padx=5)

		self.key_label = Tkinter.Label(self.frame, text='API key: ')
		self.key_label.grid(row=0, column=0, sticky='w')
		self.key = Tkinter.Entry(self.frame, width=33)
		self.key.grid(row=0, column=1, stick='w', padx=5)
		self.key.insert(0, app.api_key)

		self.execute_button = Tkinter.Button(self.frame, text="Run", command=app.execute)
		self.execute_button.grid(row=2, column=0, sticky='sw')

		self.select_out_dir_btn = Tkinter.Button(self.frame, text='Browse...', command=app.select_out_dir)
		self.select_out_dir_btn.grid(row=1, column=0, sticky='w', pady=5)

		self.out_dir = Tkinter.Text(self.frame, state=Tkinter.DISABLED, height=1)
		self.out_dir.grid(row=1, column=1, sticky='w', padx=5)
		self.display_out_dir()

	def display_out_dir(self):
		self.out_dir.config(state=Tkinter.NORMAL)
		self.out_dir.delete(1.0, Tkinter.END)
		self.out_dir.insert(Tkinter.END, self.app.out_directory)
		self.out_dir.config(state=Tkinter.DISABLED)

if __name__=='__main__':
	root = Tkinter.Tk()
	app = App(root)
	root.mainloop()