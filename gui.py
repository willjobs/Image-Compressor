import Tkinter, tkFileDialog, tkMessageBox, sys
from PIL import Image, ImageTk
from image_compressor import resize_and_compress

class App:
	selected_files = []
	out_directory = ''
	tinykey = ''
	file_opt = {'filetypes':[('JPEG files', '*.jpeg;*.jpg;*.JPG;*.JPEG')]}	#file dialog options

	def __init__(self, root):
		root.title('Image Compressor')

		self.file_display = FileDisplay(root, self)
		self.options = Options(root, self)
		self.menu = AppMenu(root, self)

		root.geometry('800x450')

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
			self.file_display.display(self)
		#as enhancement, consider adding ability to ADD/REMOVE files, rather than simply replacing

	def select_dir(self):
		self.out_directory = tkFileDialog.askdirectory()
		self.options.display_dir(self)

	def execute(self):
		self.tinykey = self.options.key.get()

		if len(self.selected_files) > 0:
			if self.out_directory != '':
				if self.tinykey != '':
					if resize_and_compress(self.selected_files, self.out_directory, self.tinykey):
						tkMessageBox.showinfo("Compression successful", "Success!")
					else:
						tkMessageBox.showerror("Error", "An error occurred.")
				else:
					tkMessageBox.showerror("Error", "Enter a key.")
			else:
				tkMessageBox.showerror("Error", "Select an out directory.")
		else:
			tkMessageBox.showerror("Error", "Select some files.")

	def select_files_key(self, event):
		self.select_files()

	def select_dir_key(self, event):
		self.select_dir()

	def exit(self, event):
		sys.exit(0)

class AppMenu:

	def __init__(self, root, app):
		self.app = app

		menubar = Tkinter.Menu(root)

		filemenu = Tkinter.Menu(menubar, tearoff=0)
		filemenu.add_command(label='Select files', accelerator='Ctrl+S', command=app.select_files)
		filemenu.add_command(label='Select output folder', accelerator='Ctrl+O', command=app.select_dir)

		filemenu.add_separator()
		filemenu.add_command(label='Exit', accelerator='Ctrl+Q', command=root.quit)

		menubar.add_cascade(label='File', menu=filemenu)
		root.config(menu=menubar)

class FileDisplay:

	def __init__(self, parent, app):
		self.frame = Tkinter.Frame(parent, bd=10)
		self.frame.grid(row=0, column=0, sticky='nsew')

		self.select_files_button = Tkinter.Button(self.frame, text="Select Files", command=app.select_files)
		self.select_files_button.pack(anchor=Tkinter.NW)

		self.scrollbar = Tkinter.Scrollbar(self.frame)
		self.txt = Tkinter.Text(self.frame, yscrollcommand=self.scrollbar.set, state=Tkinter.DISABLED)
		self.txt.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT, pady=5)
		self.scrollbar.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=5)
		self.scrollbar.config(command=self.txt.yview)

	def display(self, app):
		#delete existing files from display
		self.txt.config(state=Tkinter.NORMAL)
		self.txt.delete(1.0, Tkinter.END)

		#add selected files to display
		if len(app.selected_files) > 0:
			self.txt.insert(Tkinter.END, app.selected_files[0])
			for file in app.selected_files[1:]:
				self.txt.insert(Tkinter.END, '\n' + file)
		
		self.txt.config(state=Tkinter.DISABLED)

class Options:
	def __init__(self, parent, app):
		self.frame = Tkinter.Frame(parent, bd=10)
		self.frame.grid(row=0, column=1, sticky='nsew', padx=5)

		self.key_label = Tkinter.Label(self.frame, text='Tiny key: ')
		self.key_label.grid(row=0, column=0, sticky='w')
		self.key = Tkinter.Entry(self.frame, width=33)
		self.key.grid(row=0, column=1, stick='w', padx=5)

		self.execute_button = Tkinter.Button(self.frame, text="Apply", command=app.execute)
		self.execute_button.grid(row=2, column=0, sticky='sw')

		self.select_dir_btn = Tkinter.Button(self.frame, text='Select Output Folder', command=app.select_dir)
		self.select_dir_btn.grid(row=1, column=0, sticky='w', pady=5)

		self.out_dir = Tkinter.Text(self.frame, state=Tkinter.DISABLED, height=1)
		self.out_dir.grid(row=1, column=1, sticky='w', padx=5)

	def display_dir(self, app):
		self.out_dir.config(state=Tkinter.NORMAL)
		self.out_dir.delete(1.0, Tkinter.END)
		self.out_dir.insert(Tkinter.END, app.out_directory)
		self.out_dir.config(state=Tkinter.DISABLED)

if __name__=='__main__':
	root = Tkinter.Tk()
	app = App(root)
	root.mainloop()