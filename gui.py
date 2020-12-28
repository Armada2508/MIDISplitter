from os import path
import os
import base64
import tkinter as tk
import tkinter.filedialog
import tkinter.font
import tkinter.messagebox
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
		icondata= base64.b64decode(c.ICON_BASE64)
		tempFile= "icon.ico"
		iconfile= open(tempFile,"wb")
		iconfile.write(icondata)
		iconfile.close()
		self.master.iconbitmap(c.ICON_PATH)
		os.remove(tempFile)
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
			self.input_file_string.set(self.input_file_chooser)

	def select_output(self):
		# Open a dialog to select the output file
		self.output_file_chooser = tk.filedialog.asksaveasfilename(title="Output MIDI File", filetypes=(("MIDI Files", "*.mid"), ("MIDI Files", "*.midi"), ("All files", "*.*")), defaultextension=".mid")
		# If the user didn't cancel the dialog
		if(self.output_file_chooser != ""):
			# Set the output file
			self.output_file_string.set(self.output_file_chooser)

	# Create the main gui with widgets
	def create_gui(self):
		# Initialize Frame object for containing title
		header_container = tk.Frame(self.master, width=0, height=50)
		# Initialize Frame objects for containing file selector widgets
		input_container = tk.Frame(self.master, width=0, height=80)
		output_container = tk.Frame(self.master, width=0, height=80)
		# Initialize Frame objects for containing options
		top_options_container = tk.Frame(self.master, width=0, height=70)
		bottom_options_container = tk.Frame(self.master, width=0, height=70)
		# Initialize Frame containers for options
		# Top
		note_velocity_container = tk.Frame(top_options_container, width=80, height=0)
		track_export_order_container = tk.Frame(top_options_container, width=80, height=0)
		aligning_container = tk.Frame(top_options_container, width=80, height=0)
		# Bottom
		channel_index_container = tk.Frame(bottom_options_container, width=80, height=0)
		assign_instrument_container = tk.Frame(bottom_options_container, width=80, height=0)
		normalize_tempo_container = tk.Frame(bottom_options_container, width=80, height=0)
		# Initialize convert button container
		convert_container = tk.Frame(self.master, width=0, height=80)
		# Create the main title
		title = tk.Label(header_container, text="MIDI Splitter", font=self.font_large, justify="center", width=10, border=0)
		# Create an input and output button which brings up a dialog for selecting files
		input_file_button = tk.Button(input_container, text="Input MIDI File", font=self.font_small, command=self.select_input, relief="groove", borderwidth=2)
		output_file_button = tk.Button(output_container, text="Output MIDI File", font=self.font_small, command=self.select_output, relief="groove", borderwidth=2)
		# Create the main convert button
		self.convert_button = tk.Button(convert_container, text="Convert", font=self.font_medium, command=self.convert_song, relief="groove", borderwidth=2)
		# Create string variables so that values can be accessed that are typed into entries
		self.input_file_string = tk.StringVar()
		self.output_file_string = tk.StringVar()
		self.note_velocity_string = tk.StringVar()
		self.aligning_margin_string = tk.StringVar()
		self.track_export_order_string = tk.StringVar()
		self.normalize_tempo_string = tk.StringVar()
		# Create int variables so that the state of checkboxes can be accessed
		self.channel_index_int = tk.IntVar(value=1)
		self.assign_instrument_int = tk.IntVar(value=1)
		# Set the default track export order method
		self.track_export_order_string.set("Collated")
		# Create entries for files
		input_file_entry = tk.Entry(input_container, font=self.font_small, justify="center", textvariable=self.input_file_string)
		output_file_entry = tk.Entry(output_container, font=self.font_small, justify="center", textvariable=self.output_file_string)
		# Create entries for options
		note_velocity_entry = tk.Entry(note_velocity_container, font=self.font_small, justify="center", textvariable=self.note_velocity_string, width=10)
		aligning_entry = tk.Entry(aligning_container, font=self.font_small, justify="center", textvariable=self.aligning_margin_string, width=10)
		normalize_tempo_entry = tk.Entry(normalize_tempo_container, font=self.font_small, justify="center", textvariable=self.normalize_tempo_string, width=10)
		# Create checkboxes for options
		channel_index_checkbox = tk.Checkbutton(channel_index_container, variable=self.channel_index_int)
		assign_instrument_checkbox = tk.Checkbutton(assign_instrument_container, variable=self.assign_instrument_int)
		# Color the entries based on if they are valid
		self.input_file_string.trace('w', lambda *args: input_file_entry.config(bg=self.path_color(self.input_file_string.get(), False)))
		self.output_file_string.trace('w', lambda *args: output_file_entry.config(bg=self.path_color(self.output_file_string.get(), True)))
		self.note_velocity_string.trace('w', lambda *args: note_velocity_entry.config(bg=self.velocity_color(self.note_velocity_string.get())))
		self.aligning_margin_string.trace('w', lambda *args: aligning_entry.config(bg=self.margin_color(self.aligning_margin_string.get())))
		self.normalize_tempo_string.trace('w', lambda *args: normalize_tempo_entry.config(bg=self.tempo_color(self.normalize_tempo_string.get())))
		# Reset convert button if any options are changed
		self.input_file_string.trace('w', lambda *args: self.convert_button.config(bg="SystemButtonFace"))
		self.output_file_string.trace('w', lambda *args: self.convert_button.config(bg="SystemButtonFace"))
		self.note_velocity_string.trace('w', lambda *args: self.convert_button.config(bg="SystemButtonFace"))
		self.aligning_margin_string.trace('w', lambda *args: self.convert_button.config(bg="SystemButtonFace"))
		self.track_export_order_string.trace('w', lambda *args: self.convert_button.config(bg="SystemButtonFace"))
		self.normalize_tempo_string.trace('w', lambda *args: self.convert_button.config(bg="SystemButtonFace"))
		self.channel_index_int.trace('w', lambda *args: self.convert_button.config(bg="SystemButtonFace"))
		self.assign_instrument_int.trace('w', lambda *args: self.convert_button.config(bg="SystemButtonFace"))
		# Create dropdown for selecting track export order method
		track_export_order_menu = tk.OptionMenu(track_export_order_container, self.track_export_order_string, "Collated", "Uncollated")
		# Format menu
		track_export_order_menu.config(font=self.font_small)
		# Format items
		track_export_order_menu_items = self.nametowidget(track_export_order_menu.menuname)
		track_export_order_menu_items.config(font=self.font_small)
		# Create labels for options
		velocity_label = tk.Label(note_velocity_container, font=self.font_small, text="Set Note Velocity(1-127)")
		aligning_label = tk.Label(aligning_container, font=self.font_small, text="Aligning Margin(seconds)")
		track_export_order_label = tk.Label(track_export_order_container, font=self.font_small, text="Track Export Order")
		channel_index_label = tk.Label(channel_index_container, font=self.font_small, text="Index Output Track Channels")
		assign_instrument_label = tk.Label(assign_instrument_container, font=self.font_small, text="Assign Instruments to Tracks")
		normalize_tempo_label = tk.Label(normalize_tempo_container, font=self.font_small, text="Normalize Tempo(BPM)")
		# Don't resize frames if not big enough to hold widgets
		header_container.pack_propagate(0)
		input_container.pack_propagate(0)
		output_container.pack_propagate(0)
		convert_container.pack_propagate(0)
		top_options_container.pack_propagate(0)
		bottom_options_container.pack_propagate(0)
		# Pack all of the Frames
		convert_container.pack(side=tk.BOTTOM, expand=1, fill='both')
		bottom_options_container.pack(side=tk.BOTTOM, expand=1, fill='both')
		top_options_container.pack(side=tk.BOTTOM, expand=1, fill='both')
		note_velocity_container.pack(side=tk.LEFT, expand=1, fill='both')
		track_export_order_container.pack(side=tk.RIGHT, expand=1, fill='both')
		aligning_container.pack(side=tk.RIGHT, expand=1, fill='both')
		channel_index_container.pack(side=tk.LEFT, expand=1, fill='both')
		normalize_tempo_container.pack(side=tk.RIGHT, expand=1, fill='both')
		assign_instrument_container.pack(side=tk.RIGHT, expand=1, fill='both')
		header_container.pack(side=tk.TOP, expand=1, fill='both')
		input_container.pack(side=tk.LEFT, expand=1, fill='both')
		output_container.pack(side=tk.RIGHT, expand=1, fill='both')
		# Pack the title
		title.pack(side=tk.TOP, expand=1, fill='y', pady=(10, 10))
		self.convert_button.pack(side=tk.TOP, fill='both', expand=1, padx=(10, 10), pady=(10, 10))
		# Pack the file selection buttons
		input_file_button.pack(side=tk.TOP, fill='both', padx=(10, 10), pady=(10, 10))
		output_file_button.pack(side=tk.TOP, fill='both', padx=(10, 10), pady=(10, 10))
		# Pack the file entries
		input_file_entry.pack(side=tk.TOP, fill='both', padx=(10, 10))
		output_file_entry.pack(side=tk.TOP, fill='both', padx=(10, 10))
		# Pack the options
		# Top
		velocity_label.pack(side=tk.TOP, pady=(5, 5))
		note_velocity_entry.pack(side=tk.TOP, pady=(0, 5))
		aligning_label.pack(side=tk.TOP, pady=(5, 5))
		aligning_entry.pack(side=tk.TOP, pady=(0, 5))
		track_export_order_label.pack(side=tk.TOP, pady=(5, 5))
		track_export_order_menu.pack(side=tk.TOP, pady=(0, 5))
		# Bottom
		channel_index_label.pack(side=tk.TOP, pady=(5, 5))
		channel_index_checkbox.pack(side=tk.TOP, pady=(0, 5))
		assign_instrument_label.pack(side=tk.TOP, pady=(5, 5))
		assign_instrument_checkbox.pack(side=tk.TOP, pady=(0, 5))
		normalize_tempo_label.pack(side=tk.TOP, pady=(5, 5))
		normalize_tempo_entry.pack(side=tk.TOP, pady=(0, 5))

	def convert_song(self):
		# Parse the file
		result = mp.parse(self.input_file_string.get(), self.output_file_string.get(), self.note_velocity_string.get(), self.aligning_margin_string.get(), self.track_export_order_string.get() == "Collated", self.normalize_tempo_string.get(), self.channel_index_int.get(), self.assign_instrument_int.get())
		self.convert_button.config(bg="green" if not isinstance(result, Exception) else "red")
		if isinstance(result, Exception):
			tkinter.messagebox.showerror(title="Conversion Error", message=result)
	
	def path_color(self, filepath, save):
		if(filepath == ""):
			return "white"
		# If we're saving the file
		if(save):
			# If the path is valid and it has the correct extension
			return "green" if path.exists(path.dirname(filepath)) and (path.splitext(filepath)[-1].lower() == ".mid" or path.splitext(filepath)[-1].lower() == ".midi") else "red"
		# If we're trying to load the file check if it exists and has the right extension
		return "green" if path.isfile(filepath) and (path.splitext(filepath)[-1].lower() == ".mid" or path.splitext(filepath)[-1].lower() == ".midi") else "red"
	
	def velocity_color(self, value):
		if(value == ""):
			return "white"
		try:
			value = int(value)
			return "green" if value < 128 and value > 0 else "red"
		except:
			return "red"
	
	def margin_color(self, value):
		if(value == ""):
			return "white"
		try:
			value = float(value)
			return "green" if value >= 0 else "red"
		except:
			return "red"

	def tempo_color(self, value):
		if(value == ""):
			return "white"
		try:
			value = int(value)
			return "green" if value > 0 else "red"
		except:
			return "red"