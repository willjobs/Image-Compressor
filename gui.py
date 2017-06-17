import os
import Tkinter, tkFileDialog, tkMessageBox, sys, shelve
from PIL import Image, ImageTk
from image_compressor import resize, compress, restore_EXIF_tags

class App:
	selected_files = []
	out_directory = saved_out_directory = ''
	api_key = saved_api_key = ''

	# file dialog options
	file_opt = {'filetypes':[('JPEGs and PNGs', '*.jpeg;*.jpg;*.png;')], 'initialdir':''}

	def __init__(self, root):
		root.title('Image Compressor')

		settings = shelve.open('settings')
		if settings.has_key('api_key'):
			self.saved_api_key = settings['api_key']
		if settings.has_key('output_folder'):
			self.saved_out_directory = settings['output_folder']
			self.out_directory = self.saved_out_directory
		if settings.has_key('input_folder'):
			self.file_opt['initialdir'] = settings['input_folder']
		settings.close()

		self.file_display = FileDisplay(root, self)
		self.options = Options(root, self)
		self.menu = AppMenu(root, self)

		root.geometry('810x450')
		root.minsize(width=810, height=350)

		root.grid_columnconfigure(0, weight=1, uniform="a")
		root.grid_columnconfigure(1, weight=1, uniform="a")
		root.grid_rowconfigure(0, weight=1)

		#hotkeys
		root.bind_all('<Control-s>', self.select_files_key)
		root.bind_all('<Control-o>', self.select_dir_key)
		root.bind_all('<Control-q>', self.exit)

	def select_files(self):
		f = tkFileDialog.askopenfilenames(**self.file_opt)
		#if user clicked cancel, we won't remove previously chosen files
		if len(f) > 0:
			self.selected_files = f
			self.file_display.display()
		#as enhancement, consider adding ability to ADD/REMOVE files, rather than simply replacing

	def select_dir(self):
		o = tkFileDialog.askdirectory()
		#if user clicked cancel, we won't remove previously chosen folder
		if o != '':
			self.out_directory = o
			self.options.display_dir()

	def execute(self):
		self.api_key = self.options.key.get()

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
			log = resize(file, out_dir=self.out_directory, suffix='_small')
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
			log = compress(api_key=self.api_key, file=log['result'], out_dir=self.out_directory, suffix='')
			if not log['success']:
				tkMessageBox.showerror("Error", log['message'])
				return
			else:
				print log['message']
				savings_KB = savings_KB + log['saved']


			print 'Restoring EXIF tags... ',
			restore_EXIF_tags(file, log['result'])
			print 'Restore complete!'


		print 'Resizing and compressing together saved ' + str(round(savings_KB,0)) + ' KB = ' \
			+ str(round(savings_KB * 100 / total_orig_size, 1)) + '%'

		tkMessageBox.showinfo("Compression successful", "Success!")


	def select_files_key(self, event):
		self.select_files()

	def select_dir_key(self, event):
		self.select_dir()

	def exit(self, event):
		sys.exit(0)

class AppMenu:

	def __init__(self, root, app):
		self.app = app

		self.menubar = Tkinter.Menu(root)

		self.filemenu = Tkinter.Menu(self.menubar, tearoff=0)
		self.filemenu.add_command(label='Select files', accelerator='Ctrl+S', command=app.select_files)
		self.filemenu.add_command(label='Select output folder', accelerator='Ctrl+O', command=app.select_dir)

		self.filemenu.add_separator()
		self.filemenu.add_command(label='Exit', accelerator='Ctrl+Q', command=root.quit)

		self.settingsmenu = Tkinter.Menu(self.menubar, tearoff=0)
		self.settingsmenu.add_command(label='Preferences', command=self.open_preferences)

		self.menubar.add_cascade(label='File', menu=self.filemenu)
		self.menubar.add_cascade(label='Settings', menu=self.settingsmenu)
		root.config(menu=self.menubar)

	def open_preferences(self):
		self.pref_window = Tkinter.Toplevel()
		self.pref_window.title('Preferences')

		self.initialize_api_key()

		self.initialize_output_folder()

		self.initialize_input_folder()

		self.initialize_save_cancel()

	def initialize_api_key(self):
		self.save_key_status = Tkinter.IntVar()
		self.save_key_chkbtn = Tkinter.Checkbutton(self.pref_window, text='Save API key', variable=self.save_key_status, command=self.save_key_status_change)
		self.save_key_chkbtn.grid(row=0, column=0, sticky='w')

		self.key_to_save = Tkinter.Entry(self.pref_window, width=33)
		if self.app.saved_api_key != '':
			self.save_key_chkbtn.select()
			self.key_to_save.config(state=Tkinter.NORMAL)
			self.key_to_save.delete(0, Tkinter.END)
			self.key_to_save.insert(0, self.app.saved_api_key)
		else:
			self.key_to_save.config(state=Tkinter.DISABLED)
		self.key_to_save.grid(row=1, column=0, padx=5, sticky='w')

	def initialize_output_folder(self):
		self.save_out_status = Tkinter.IntVar()
		self.save_out_chkbtn = Tkinter.Checkbutton(self.pref_window, text='Set Default Output Folder', variable=self.save_out_status, command=self.save_out_status_change)
		self.save_out_chkbtn.grid(row=2, column=0, sticky='w', pady=(15, 0))

		out_frame = Tkinter.Frame(self.pref_window)
		self.set_out_btn = Tkinter.Button(out_frame, text='Select Output Folder', command=self.select_default_out, state=Tkinter.DISABLED)
		self.out_txt = Tkinter.Text(out_frame, state=Tkinter.DISABLED, height=1, width=50)
		if self.app.saved_out_directory != '':
			self.temp_out = self.app.saved_out_directory

			self.save_out_chkbtn.select()

			self.set_out_btn.config(state=Tkinter.NORMAL)

			self.out_txt.config(state=Tkinter.NORMAL)
			self.out_txt.delete(1.0, Tkinter.END)
			self.out_txt.insert(1.0, app.saved_out_directory)
			self.out_txt.config(state=Tkinter.DISABLED)
		else:
			self.temp_out = ''
		out_frame.grid(row=3, column=0, sticky='w', padx=5)
		self.set_out_btn.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT)
		self.out_txt.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT, padx=5)

	def initialize_input_folder(self):
		self.save_in_status = Tkinter.IntVar()
		self.save_in_chkbtn = Tkinter.Checkbutton(self.pref_window, text='Set Default Input Folder', variable=self.save_in_status, command=self.save_in_status_change)
		self.save_in_chkbtn.grid(row=4, column=0, sticky='w', pady=(15, 0))

		in_frame = Tkinter.Frame(self.pref_window)
		self.set_in_btn = Tkinter.Button(in_frame, text='Select Input Folder', command=self.select_default_in, state=Tkinter.DISABLED)
		self.in_txt = Tkinter.Text(in_frame, state=Tkinter.DISABLED, height=1, width=50)
		if self.app.file_opt['initialdir'] != '':
			self.temp_in = self.app.file_opt['initialdir']

			self.save_in_chkbtn.select()

			self.set_in_btn.config(state=Tkinter.NORMAL)

			self.in_txt.config(state=Tkinter.NORMAL)
			self.in_txt.delete(1.0, Tkinter.END)
			self.in_txt.insert(1.0, self.temp_in)
			self.in_txt.config(state=Tkinter.DISABLED)
		else:
			self.temp_in = ''
		in_frame.grid(row=5, column=0, sticky='w', padx=5)
		self.set_in_btn.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT)
		self.in_txt.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT, padx=(14, 0))

	def initialize_save_cancel(self):
		save_cancel_frame = Tkinter.Frame(self.pref_window, bd=5)
		self.save_btn = Tkinter.Button(save_cancel_frame, text='Save', command=self.save_prefs)
		self.cancel_btn = Tkinter.Button(save_cancel_frame, text='Cancel', command=self.cancel_prefs)
		save_cancel_frame.grid(row=6, column=0, sticky='w', pady=(5, 0))
		self.save_btn.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT)
		self.cancel_btn.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT, padx=5)

	def save_key_status_change(self):
		if self.save_key_status.get():
			self.key_to_save.config(state=Tkinter.NORMAL)
		else:
			self.key_to_save.delete(0, Tkinter.END)
			self.key_to_save.config(state=Tkinter.DISABLED)

	def save_out_status_change(self):
		if self.save_out_status.get():
			self.set_out_btn.config(state=Tkinter.NORMAL)
		else:
			self.set_out_btn.config(state=Tkinter.DISABLED)
			self.out_txt.config(state=Tkinter.NORMAL)
			self.out_txt.delete(1.0, Tkinter.END)
			self.out_txt.config(state=Tkinter.DISABLED)

	def select_default_out(self):
		self.temp_out = tkFileDialog.askdirectory()
		if self.temp_out != '':
			self.out_txt.config(state=Tkinter.NORMAL)
			self.out_txt.delete(1.0, Tkinter.END)
			self.out_txt.insert(1.0, self.temp_out)
			self.out_txt.config(state=Tkinter.DISABLED)

	def save_in_status_change(self):
		if self.save_in_status.get():
			self.set_in_btn.config(state=Tkinter.NORMAL)
		else:
			self.set_in_btn.config(state=Tkinter.DISABLED)
			self.in_txt.config(state=Tkinter.NORMAL)
			self.in_txt.delete(1.0, Tkinter.END)
			self.in_txt.config(state=Tkinter.DISABLED)

	def select_default_in(self):
		self.temp_in = tkFileDialog.askdirectory()
		if self.temp_in != '':
			self.in_txt.config(state=Tkinter.NORMAL)
			self.in_txt.delete(1.0, Tkinter.END)
			self.in_txt.insert(1.0, self.temp_in)
			self.in_txt.config(state=Tkinter.DISABLED)

	def save_prefs(self):
		self.app.saved_api_key = self.key_to_save.get()
		self.app.saved_out_directory = self.temp_out

		settings = shelve.open('settings')

		##API KEY##
		if self.save_key_status.get():
			settings['api_key'] = self.app.saved_api_key
			self.app.options.key.delete(0, Tkinter.END)
			self.app.options.key.insert(0, self.app.saved_api_key)
		else:
			settings['api_key'] = ''

		##OUTPUT FOLDER##
		if self.save_out_status.get():
			self.app.out_directory = self.app.saved_out_directory		#set folder used when Apply button clicked
			settings['output_folder'] = self.app.out_directory			#save the setting
			self.app.options.out_dir.config(state=Tkinter.NORMAL)		#display selected folder on main window
			self.app.options.out_dir.delete(1.0, Tkinter.END)
			self.app.options.out_dir.insert(1.0, self.app.out_directory)
			self.app.options.out_dir.config(state=Tkinter.DISABLED)
		else:
			settings['output_folder'] = ''

		##INPUT FOLDER##
		if self.save_in_status.get():
			settings['input_folder'] = self.temp_in
			self.app.file_opt['initialdir'] = self.temp_in
		else:
			settings['input_folder'] = ''
			self.app.file_opt['initialdir'] = ''

		settings.close()

		self.pref_window.destroy()

	def cancel_prefs(self):
		self.pref_window.destroy()

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
		#delete existing files from display
		self.txt.config(state=Tkinter.NORMAL)
		self.txt.delete(1.0, Tkinter.END)

		#add selected files to display
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
		self.key.insert(0, app.saved_api_key)

		self.execute_button = Tkinter.Button(self.frame, text="Apply", command=app.execute)
		self.execute_button.grid(row=2, column=0, sticky='sw')

		self.select_dir_btn = Tkinter.Button(self.frame, text='Select Output Folder', command=app.select_dir)
		self.select_dir_btn.grid(row=1, column=0, sticky='w', pady=5)

		self.out_dir = Tkinter.Text(self.frame, state=Tkinter.DISABLED, height=1)
		self.out_dir.grid(row=1, column=1, sticky='w', padx=5)
		self.display_dir()

	def display_dir(self):
		self.out_dir.config(state=Tkinter.NORMAL)
		self.out_dir.delete(1.0, Tkinter.END)
		self.out_dir.insert(Tkinter.END, self.app.out_directory)
		self.out_dir.config(state=Tkinter.DISABLED)

if __name__=='__main__':
	root = Tkinter.Tk()
	app = App(root)
	root.mainloop()