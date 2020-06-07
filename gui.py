import tkinter as tk
import tkinter.filedialog
import tkinter.font
import midi_parser as mp

class Interface(tk.Frame):
	"""The main interface of the application"""
	def __init__(self):
		self.master = tk.Tk()
		super().__init__(self.master)		
		self.master.minsize(width=400, height=300)
		self.master.maxsize(width=1800, height=800)
		self.master.geometry("1000x300")
		self.font_small = tk.font.Font(family="helvetica", size=12, weight="normal")
		self.font_medium = tk.font.Font(family="helvetica", size=24, weight="normal")
		self.font_large = tk.font.Font(family="helvetica", size=36, weight="normal")
		self.input_file_chooser = None;
		self.output_file_chooser = None;
		self.master.iconbitmap('icon.ico')
		self.pack()
		self.create_gui()
		tk.mainloop()

	def select_input(self):
		self.input_file_chooser = tk.filedialog.askopenfilename(title="Input MIDI File", filetypes=(("MIDI Files", "*.mid"), ("MIDI Files", "*.midi"), ("All files", "*.*")))
		self.input_file.set(self.input_file_chooser)
		print("abcd")

	def select_output(self):
		self.output_file_chooser = tk.filedialog.asksaveasfilename(title="Output MIDI File", filetypes=(("MIDI Files", "*.mid"), ("MIDI Files", "*.midi"), ("All files", "*.*")), defaultextension=".mid")
		self.output_file.set(self.output_file_chooser)

	def create_gui(self):
		self.info = tk.Frame(self.master, width=300, height=100)
		self.input = tk.Frame(self.master, width=300, height=100)
		self.output = tk.Frame(self.master, width=300, height=100)
		self.convert = tk.Frame(self.master, width=600, height=100)
		self.title = tk.Entry(self.info, font=self.font_large, justify="center", width=10, border=0)
		self.title.insert(0, "MIDI Splitter")
		self.title.config(state='readonly')
		self.input_button = tk.Button(self.input, text="Input MIDI File", font=self.font_small, command=self.select_input, relief="groove", borderwidth=2)
		self.output_button = tk.Button(self.output, text="Output MIDI File", font=self.font_small, command=self.select_output, relief="groove", borderwidth=2)
		self.convert_button = tk.Button(self.convert, text="Convert", font=self.font_medium, command=self.convert_song, relief="groove", borderwidth=2)
		self.input_file = tk.StringVar();
		self.output_file = tk.StringVar();
		self.input_file_entry = tk.Entry(self.input, font=self.font_small, justify="center", textvariable=self.input_file)
		self.output_file_entry = tk.Entry(self.output, font=self.font_small, justify="center", textvariable=self.output_file)
		self.info.pack_propagate(0)
		self.input.pack_propagate(0)
		self.output.pack_propagate(0)
		self.convert.pack_propagate(0)
		self.convert.pack(side=tk.BOTTOM, expand=1, fill='x')
		self.info.pack(side=tk.TOP, expand=1, fill='x')
		self.input.pack(side=tk.LEFT, expand=1, fill='x')
		self.output.pack(side=tk.RIGHT, expand=1, fill='x')
		self.title.pack(side=tk.TOP, expand=0, pady=(25, 25))
		self.convert_button.pack(side=tk.TOP, fill='x', expand=1, padx=(20, 20))
		self.input_button.pack(side=tk.TOP, fill='x', padx=(10, 10), pady=(10, 10))
		self.output_button.pack(side=tk.TOP, fill='x', padx=(10, 10), pady=(10, 10))
		self.input_file_entry.pack(side=tk.TOP, fill='x', padx=(10, 10))
		self.output_file_entry.pack(side=tk.TOP, fill='x', padx=(10, 10))
		self.input_file_entry

	def convert_song(self):
		mp.parse(self.input_file.get())