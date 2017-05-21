import Tkinter, tkFileDialog, sys
from PIL import Image, ImageTk
from image_compressor import resize_and_compress

selected_files = []
out_directory = ''

class AppMenu:
	opt = {'filetypes':[('JPEG files', '*.jpeg;*.jpg;*.JPG;*.JPEG')]}	#file dialog options

	def __init__(self, root):
		menubar = Tkinter.Menu(root)

		filemenu = Tkinter.Menu(menubar, tearoff=0)
		filemenu.add_command(label='Select files', accelerator='Ctrl+S', command=self.select_files)
		filemenu.add_command(label='Select output directory', accelerator='Ctrl+O', command=self.select_dir)

		filemenu.add_separator()
		filemenu.add_command(label='Exit', accelerator='Ctrl+Q', command=root.quit)

		menubar.add_cascade(label='File', menu=filemenu)
		root.config(menu=menubar)

		#hotkeys
		root.bind_all('<Control-s>', self.select_files_key)
		root.bind_all('<Control-o>', self.select_dir_key)
		root.bind_all('<Control-q>', self.exit)

	def select_files(self):
		global selected_files
		selected_files = tkFileDialog.askopenfilenames(**self.opt)
		if len(selected_files) > 0:
			file_display.display()

	def select_files_key(self, event):
		self.select_files()

	def select_dir(self):
		global out_directory
		out_directory = tkFileDialog.askdirectory()
		if out_directory != '':
			options.display_dir()

	def select_dir_key(self, event):
		self.select_dir()

	def exit(self, event):
		sys.exit(0)

class FileDisplay:

	def __init__(self, parent):
		self.frame = Tkinter.Frame(parent)
		self.frame.grid(row=0, column=0, sticky='nsew')


		self.label = Tkinter.Label(self.frame)
		self.txt = Tkinter.Text(self.frame)
		self.scrollbar = Tkinter.Scrollbar(self.frame)


	def display(self):
		self.label.destroy()
		self.txt.destroy()
		self.scrollbar.destroy()

		self.label = Tkinter.Label(self.frame, anchor=Tkinter.NW, text='Selected files:')
		self.label.pack(anchor=Tkinter.NW)

		self.scrollbar = Tkinter.Scrollbar(self.frame)
		self.txt = Tkinter.Text(self.frame, yscrollcommand=self.scrollbar.set)

		self.txt.insert(Tkinter.END, selected_files[0])
		for file in selected_files[1:]:
			self.txt.insert(Tkinter.END, '\n' + file)

		self.txt.pack(fill=Tkinter.BOTH, side=Tkinter.LEFT)
		self.scrollbar.pack(side=Tkinter.LEFT, fill=Tkinter.Y)
		self.scrollbar.config(command=self.txt.yview)

class Options:
	def __init__(self, parent):
		self.frame = Tkinter.Frame(parent, bd=10)
		self.frame.grid(row=0, column=1, sticky='nsew')

		self.execute_button = Tkinter.Button(self.frame, text="Apply", command=self.execute)
		self.execute_button.grid(row=1, column=0, sticky='sw')

		self.out_dir_label = Tkinter.Label(self.frame)
		self.out_dir = Tkinter.Text(self.frame)

	def display_dir(self):
		self.out_dir_label.destroy()
		self.out_dir.destroy()

		self.out_dir_label = Tkinter.Label(self.frame, text='Output folder: ', anchor=Tkinter.SW)
		self.out_dir_label.grid(row=0, column=0, sticky='w')
		self.out_dir = Tkinter.Text(self.frame, height=1)
		self.out_dir.insert(Tkinter.END, out_directory)
		self.out_dir.grid(row=0, column=1, sticky='w')

	def execute(self):
		resize_and_compress(selected_files, out_directory)

if __name__=='__main__':
	root = Tkinter.Tk()
	root.title('Image Compressor')

	file_display = FileDisplay(root)
	options = Options(root)
	menu = AppMenu(root)

	root.grid_columnconfigure(0, weight=1, uniform="a")
	root.grid_columnconfigure(1, weight=1, uniform="a")
	root.grid_rowconfigure(0, weight=1)
	
	root.mainloop()