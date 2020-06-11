import tkinter as tk
import tkinter.filedialog
import tkinter.font
import midi_parser as mp
import constants as c

class Interface(tk.Frame):
	"""The main interface of the application"""
	def __init__(self):
		# Initialize the main window
		self.master = tk.Tk()
		super().__init__(self.master)
		# Set the min and max window sizes
		self.master.minsize(width=c.MIN_WIDTH, height=c.MIN_HEIGHT)
		self.master.maxsize(width=c.MAX_WIDTH, height=c.MAX_HEIGHT)
		# Set the default window size
		self.master.geometry(str(c.DEFAULT_WIDTH) + "x" + str(c.DEFAULT_HEIGHT))
		# Set the window title
		self.winfo_toplevel().title(c.WINDOW_TITLE)
		# Configure fonts
		self.font_small = tk.font.Font(family=c.SMALL_FONT_FAMILY, size=c.SMALL_FONT_SIZE, weight=c.SMALL_FONT_WEIGHT)
		self.font_medium = tk.font.Font(family=c.MEDIUM_FONT_FAMILY, size=c.MEDIUM_FONT_SIZE, weight=c.MEDIUM_FONT_WEIGHT)
		self.font_large = tk.font.Font(family=c.LARGE_FONT_FAMILY, size=c.LARGE_FONT_SIZE, weight=c.LARGE_FONT_WEIGHT)
		# Set these variables to None so we know that the user has not selected a file yet
		self.input_file_chooser = None
		self.output_file_chooser = None
		# Add an icon
		self.master.iconbitmap(c.ICON_PATH)
		self.pack()
		# Create the main gui with widgets
		self.create_gui()
		# Run the gui
		tk.mainloop()

	def select_input(self):
		# Open a dialog to select the input file
		self.input_file_chooser = tk.filedialog.askopenfilename(title="Input MIDI File", filetypes=(("MIDI Files", "*.mid"), ("MIDI Files", "*.midi"), ("All files", "*.*")))
		# If the user didn't cancel the dialog
		if(self.input_file_chooser != ""):
			# Set the input file
			self.input_file.set(self.input_file_chooser)

	def select_output(self):
		# Open a dialog to select the output file
		self.output_file_chooser = tk.filedialog.asksaveasfilename(title="Output MIDI File", filetypes=(("MIDI Files", "*.mid"), ("MIDI Files", "*.midi"), ("All files", "*.*")), defaultextension=".mid")
		# If the user didn't cancel the dialog
		if(self.output_file_chooser != ""):
			# Set the output file
			self.output_file.set(self.output_file_chooser)

	# Create the main gui with widgets
	def create_gui(self):
		# TODO: Add completion indicator
		# TODO: Add track split method option
		# Initialize Frame objects for containing widgets
		self.info = tk.Frame(self.master, width=0, height=80)
		self.input = tk.Frame(self.master, width=0, height=80)
		self.output = tk.Frame(self.master, width=0, height=80)
		self.options = tk.Frame(self.master, width=0, height=80)
		self.velocity = tk.Frame(self.options, width=0, height=0)
		self.aligning = tk.Frame(self.options, width=0, height=0)
		self.convert = tk.Frame(self.master, width=0, height=100)
		# Create the main title
		self.title = tk.Label(self.info, text="MIDI Splitter", font=self.font_large, justify="center", width=10, border=0)
		# Create an input and output button which brings up a dialog for selecting files
		self.input_button = tk.Button(self.input, text="Input MIDI File", font=self.font_small, command=self.select_input, relief="groove", borderwidth=2)
		self.output_button = tk.Button(self.output, text="Output MIDI File", font=self.font_small, command=self.select_output, relief="groove", borderwidth=2)
		# Create the main convert button
		self.convert_button = tk.Button(self.convert, text="Convert", font=self.font_medium, command=self.convert_song, relief="groove", borderwidth=2)
		# Create string variables so that values can be accessed that are typed into entries
		self.input_file = tk.StringVar()
		self.output_file = tk.StringVar()
		self.note_velocity = tk.StringVar()
		self.aligning_margin = tk.StringVar()
		# Create entries for files and options
		self.input_file_entry = tk.Entry(self.input, font=self.font_small, justify="center", textvariable=self.input_file)
		self.output_file_entry = tk.Entry(self.output, font=self.font_small, justify="center", textvariable=self.output_file)
		self.velocity_entry = tk.Entry(self.velocity, font=self.font_small, justify="center", textvariable=self.note_velocity)
		self.aligning_entry = tk.Entry(self.aligning, font=self.font_small, justify="center", textvariable=self.aligning_margin)
		# Create labels for options
		self.velocity_label = tk.Label(self.velocity, font=self.font_small, text="Change All Note Velocity(1-127)")
		self.aligning_label = tk.Label(self.aligning, font=self.font_small, text="Note Aligning Margin(seconds)")
		# Resize frames if not big enough to hold widgets
		self.info.pack_propagate(0)
		self.input.pack_propagate(0)
		self.output.pack_propagate(0)
		self.convert.pack_propagate(0)
		self.options.pack_propagate(0)
		self.velocity.pack_propagate(0)
		self.aligning.pack_propagate(0)
		# Pack all of the Frames
		self.convert.pack(side=tk.BOTTOM, expand=1, fill='both')
		self.options.pack(side=tk.BOTTOM, expand=1, fill='both')
		self.velocity.pack(side=tk.LEFT, expand=1, fill='both')
		self.aligning.pack(side=tk.RIGHT, expand=1, fill='both')
		self.info.pack(side=tk.TOP, expand=1, fill='both')
		self.input.pack(side=tk.LEFT, expand=1, fill='both')
		self.output.pack(side=tk.RIGHT, expand=1, fill='both')
		# Pack the title
		self.title.pack(side=tk.TOP, expand=1, fill='y', pady=(10, 10))
		self.convert_button.pack(side=tk.TOP, fill='both', expand=1, padx=(20, 20), pady=(20, 20))
		# Pack the file selection buttons
		self.input_button.pack(side=tk.TOP, fill='both', padx=(10, 10), pady=(10, 10))
		self.output_button.pack(side=tk.TOP, fill='both', padx=(10, 10), pady=(10, 10))
		# Pack the file entries
		self.input_file_entry.pack(side=tk.TOP, fill='both', padx=(10, 10))
		self.output_file_entry.pack(side=tk.TOP, fill='both', padx=(10, 10))
		# Pack the options
		self.velocity_label.pack(side=tk.TOP, pady=(10, 0))
		self.velocity_entry.pack(side=tk.BOTTOM, pady=(0, 10))
		self.aligning_label.pack(side=tk.TOP, pady=(10, 0))
		self.aligning_entry.pack(side=tk.BOTTOM, pady=(0, 10))

	def convert_song(self):
		# Parse the file
		mp.parse(self.input_file.get(), self.output_file.get(), self.note_velocity.get())