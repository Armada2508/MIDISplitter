import mido
from mido import Message, MidiFile, MidiTrack
import constants as c
from decimal import *
import copy
import traceback

def parse(input_file, output_file, velocity, align_margin):

	# TODO: Extract parts of parse function into other functions

	# =====================
	#    Initialization
	# =====================

	# Check if the input file wasn't given
	if(input_file == ""):
		# If the input file weren't given, return an exception
		return Exception("Input file not specified")

	# Check if the input file wasn't given
	if(output_file == ""):
		# If the input file weren't given, return an exception
		return Exception("Output file not specified")


	# Create lists for storing notes and meta messages
	track_notes = []
	track_meta = []

	# Try to load the input file
	try:
		# Load the input MIDI file
		input_song = mido.MidiFile(input_file)
	except Exception as err:
		traceback.print_tb(err.__traceback__)
		# If it couldn't be loaded, return an error
		return Exception("Input file could not be loaded, try checking the input file path")

	# Create a new MIDI file for the final song
	output_song = mido.MidiFile(ticks_per_beat=input_song.ticks_per_beat)

	# Check if we should override the note velocity
	new_velocity = -1
	
	try:
		# See if the user has input an integer
		new_velocity = int(velocity)
	except:
		pass

	# If it's out of range, set it to -1
	if(new_velocity < 1 or new_velocity > 127):
		new_velocity = -1

	# Create a dictionary to serve as a look up table for tempo
	tempo_dict = {}

	# Create a aligning margin variable
	alignment_margin = 0

	try:
		# See if the user has input a number
		alignment_margin = float(align_margin)
	except:
		pass

	# ==========================
	#     Loop Through Tracks
	# ==========================

	for i, track in enumerate(input_song.tracks):

		# ==============================
		#     Raw Message Extraction
		# ==============================

		# Store all meta messages in a list
		meta_messages = [msg for msg in track if msg.is_meta]

		# Create a time variable for storing absolute time and set it to 0
		tick_time = 0

		# Create a new empty list inside the main list for all tracks to append notes to
		track_meta.append([])
		# Create a new empty list inside the main list for all tracks to append meta messages to
		track_notes.append([])

		# Loop through all meta messages
		for msg in meta_messages:
			# Append the message to the meta list for this track
			track_meta[i].append(msg)

		# ===========================
		#     Convert Note Format
		# ===========================

		# Create a variable to store the state of the sustain controller
		sustain = False
		# Create a variable to store the state of the sustain controller last loop
		sustain_last = False
		# Create a variable to store the state of the sostenuto controller
		sostenuto = False
		# Create a variable to store the state of the sostenuto controller last loop
		sostenuto_last = False
		# Create a variable to store all notes being sustained by the sostenuto controller
		sostenuto_notes = []
		# Create a variable to turn all notes off 
		off = False


		# Loop through all notes in the track
		for j, msg in enumerate(track):
			# If this is the last message
			if(j == len(track) - 1):
				off = True

			# If there is a change in time then add that to the absolute time
			tick_time += msg.time

			# If we found a set_tempo message
			if(msg.is_meta and msg.type == "set_tempo"):
				# Add it to the look up table
				tempo_dict[tick_time] = msg.tempo
				continue

			# If this is a note on message
			if(msg.type == "note_on"):
				if(msg.velocity != 0):
					# Create a new entry with the format of [TIME ON, TIME OFF, NOTE, VELOCITY, ALIGNED, TRACK INDEX]
					track_notes[i].append([tick_time, None, msg.note, msg.velocity, 0, None])
				else:
					# Loop through the notes list backwards
					for j in reversed(range(len(track_notes[i]))):
						if(msg.note in sostenuto_notes):
							break
						# Check if there is a note that is the same note and doesn't end yet
						if(track_notes[i][j][2] == msg.note and track_notes[i][j][1] == None):
							# Add the current time as its end time
							track_notes[i][j][1] = tick_time
			# If this is a note off message and sustain is not active
			if(msg.type == "note_off" and not sustain):
				# Loop through the notes list backwards
				for j in reversed(range(len(track_notes[i]))):
					if(msg.note in sostenuto_notes):
						break
					# Check if there is a note that is the same note and doesn't end yet
					if(track_notes[i][j][2] == msg.note and track_notes[i][j][1] == None):
						# Add the current time as its end time
						track_notes[i][j][1] = tick_time
			# If this message is a controller change
			if(msg.type == "control_change"):
				# If it is a sustain message
				if(msg.control == 64):
					# Set it on/off
					sustain = not msg.value < 64
				# If it is a sostenuto message 
				if(msg.control == 66):
					# Set it on/off
					sostenuto = not msg.value < 64
				# If this is a controller message to turn all notes off
				if(msg.control == 120):
					# Turn on the flag
					off = True
				# If this is a reset controllers message
				if(msg.control == 121):
					# Turn off sustain and sostenuto
					sustain = False
					sostenuto = False

			# If sostenuto just turned on
			if(sostenuto and not sostenuto_last):
				# Remove the notes it was holding down
				sostenuto_notes.clear()
				# Check which notes are being pressed
				notes_on = list(filter(lambda e: e[1] == None, track_notes[i]))
				# Loop through the notes
				for note in notes_on:
					# Add their pitch to the list
					sostenuto_notes.append(note[2])

			# If sustain has changed to off
			if(sustain_last and not sustain):
				# Check which notes are on and aren't being sustained by sostenuto
				notes_on = list(filter(lambda e: e[1] == None and e[2] not in sostenuto_notes, track_notes[i]))
				# Loop through them
				for note in notes_on:
					# Set their end time to now
					note[1] = tick_time

			# If sostenuto has been released
			if(sostenuto_last and not sostenuto):
				# Loop through all notes
				for note in track_notes[i]:
					# Loop through all notes being sustained by sostenuto
					for sostenuto_note in sostenuto_notes:
						# If they have the same pitch and the note has no end time
						if(note[2] == sostenuto_note and note[1] == None):
							# Set its end time to now
							note[1] = tick_time

			# If there is an all notes off message
			if(off):
				# Loop through all notes
				for note in track_notes[i]:
					# If the note doesn't have an end time
					if(note[1] == None):
						# Set its end time to now
						note[1] = tick_time
				# Clear all sostenuto notes
				sostenuto_notes.clear()
				# Turn off sostenuto
				sostenuto = False
				sostenuto_last = False

			# Set the current value of sustain to the last variable for the next loop
			sustain_last = sustain
			# Set the current value of sostenuto to the last variable for the next loop
			sostenuto_last = sostenuto
			# Turn the off flag off in case it was on
			off = False


		if(len(tempo_dict) == 0):
			tempo_dict[0] = mido.bpm2tempo(120)

		# If this is just a meta track
		if(len(meta_messages) == len(track)):
			# Create a new track
			finished_track = mido.MidiTrack()
			# Append the track to the output song
			output_song.tracks.append(finished_track)
			# Append all messages to the new track
			for msg in track_meta[i]:
				finished_track.append(msg)
			# Skip everything below
			continue

		# =====================
		#    Note Processing
		# =====================

		# If there are any notes that have the same end and start time(0 duration), delete them
		track_notes[i] = [note for note in track_notes[i] if note[0] != note[1]]

		# Remove duplicate notes
		track_notes[i] = [list(t) for t in set(tuple(e) for e in track_notes[i])]

		# Convert the note time to second
		track_notes[i] = notes2second(track_notes[i], tempo_dict, input_song.ticks_per_beat)

		# Sort the notes by their end time
		track_notes[i].sort(key=lambda e: e[1])

		# Loop through notes
		for note in track_notes[i]:
			# Find the minimum time the note must begin/end at
			min_time = note[1] - Decimal(alignment_margin)
			# Find the maximum time the note must begin/end at
			max_time = note[1] + Decimal(alignment_margin)
			# Create a variable to store the mean time of all overlapping notes
			mean_time = Decimal(0)
			# Create a variable to store how many notes are within the margin
			overlap_notes = 0
			# If the note's end has already been aligned
			if(bool(note[4] & 0b01)):
				# Skip the rest of the loop
				continue
			# Loop through all notes
			for overlap in track_notes[i]:
				# If the note starts within the margin and its start has not been aligned
				if(overlap[0] >= min_time and overlap[0] <= max_time and not bool(overlap[4] & 0b10)):
					# Add the note's time to the mean time
					mean_time += overlap[0]
					# Add one to the note count
					overlap_notes += 1
				# If the note ends within the margin and its end has not been aligned
				if(overlap[1] >= min_time and overlap[1] <= max_time and not bool(overlap[4] & 0b01)):
					# Add the note's time to the mean time
					mean_time += overlap[1]
					# Add one to the note count
					overlap_notes += 1
			# If is no other note
			if(overlap_notes < 2):
				# Skip the rest of the loop
				continue
			# Average the mean time
			mean_time /= overlap_notes
			# Loop through all notes
			for overlap in track_notes[i]:
				# If the note starts within the margin and its start has not been aligned
				if(overlap[0] >= min_time and overlap[0] <= max_time and not bool(overlap[4] & 0b10)):
					# Set the note's time to the mean
					overlap[0] = mean_time
					# Turn the bit that signifies the start has been aligned on
					overlap[4] = overlap[4] | 0b10
				# If the note ends within the margin and its end has not been aligned
				if(overlap[1] >= min_time and overlap[1] <= max_time and not bool(overlap[4] & 0b01)):
					# Set the note's time to the mean
					overlap[1] = mean_time
					# Turn the bit that signifies the end has been aligned on
					overlap[4] = overlap[4] | 0b01


		# Convert the note time back to ticks
		track_notes[i] = notes2tick(track_notes[i], tempo_dict, input_song.ticks_per_beat)

		# If there are any notes that have the same end and start time(0 duration), delete them
		track_notes[i] = [note for note in track_notes[i] if note[0] != note[1]]

		# ======================
		#    Track Splitting
		# ======================

		# Create a new list for new tracks
		new_tracks = []

		# Iterate through all notes
		for note in track_notes[i]:
			# Calculate the track index of the note
			track_index = get_track_index(note, track_notes[i])

			# If we need more tracks, add them
			for j in range(0, 1 + track_index - len(new_tracks)):
				new_tracks.append([])

			# Add the note to its track
			new_tracks[track_index].append(note)

		# TODO: Add program messages with channels
		# TODO: Implement different track order options(collated vs uncollated)
		# TODO: Export tempo changes

		# ======================
		#      Track Output
		# ======================

		for j, new_track in enumerate(new_tracks):
			# Create a new track to append to the MIDI file that will be exported
			finished_track = mido.MidiTrack()

			# Add the track to the output file
			output_song.tracks.append(finished_track)

			# Re-use tick_time to represent absolute time and set it to 0
			tick_time = 0

			# Set the finished track name to the old track name with an index starting with 1
			finished_track.name = track.name + " " + str(j + 1)

			# Loop through all of the notes in the new track
			for note in new_track:
				# Add a note_on message for the note
				finished_track.append(Message("note_on", note=note[2], velocity=new_velocity if new_velocity >= 0 else note[3], time=(note[0] - tick_time)))
				# Add a note_off message for the note
				finished_track.append(Message("note_off", note=note[2], velocity=0, time=(note[1] - note[0])))
				# Set the absolute time to the last message added(the note_off message)
				tick_time = note[1]

	# Try to save the song
	try:
		# Save the song
		output_song.save(output_file)
		# If it saves, return true
		return True
	except Exception as err:
		traceback.print_tb(err.__traceback__)
		# If it fails to save, return an exception
		return Exception("Could not save file, try checking the output file path")

# Check if two notes overlap
def check_overlap(start, end, note):
	# If the check note's endpoints are not both before and after the note, it must overlap
	return not ((start < note[0] and end <= note[0]) or (start >= note[1] and end > note[1]))

# Find all overlapping notes
def find_overlaps_range(start, end, notes):
	# Return a list of notes that pass the check_overlap test
	return list(filter(lambda e: check_overlap(start, end, e), notes))

# Find all overlapping notes
def find_overlaps(note, notes):
	# Return a list of notes that overlap the given note
	return find_overlaps_range(note[0], note[1], notes)

# Find notes that overlap and are above the note
def get_notes_above(note, notes):
	# Return a list of notes that overlap and have a pitch greater than the note
	return list(filter(lambda e: e[2] > note[2], find_overlaps(note, notes)))

# Get the track index of a note
def get_track_index(note, notes):
	# If the note has a stored index
	if(note[5] != None):
		# Return it
		return note[5]
	# Get the notes above this note
	notes_above = get_notes_above(note, notes)
	# Default the track index to 0
	track_index = 0
	# Create a list for storing the indices of the notes above this note
	track_indices = []
	# If there are no notes above this note
	if(len(notes_above) == 0):
		# Store the index in the note so we don't have to compute it again
		note[5] = track_index
		# It's track_index is 0
		return track_index
	# If there are notes above it, loop through them
	for note_above in notes_above:
		# Check their track index and add it to the list
		track_indices.append(get_track_index(note_above, notes))
	# Find the lowest number not in the list greater than 0
	while track_index in track_indices:
		track_index += 1
	# Store the index in the note so we don't have to compute it again
	note[5] = track_index
	# Return it
	return track_index

# Find the tempo from a dictionary from the time in ticks
def get_tempo(d, time, ticks_per_beat=0, seconds=False):
	# Create a list to store the tempos at different times
	tempos = []
	# Loop through the tempos in the dictionary
	for time in d:
		# Add each tempo to the list
		tempos.append([time, d[time]])
	# If there are no items
	if(len(tempos) == 0):
		# Return 500000
		return 500000
	# If there is only one item
	if(len(tempos) == 1):
		# If we've passed the tempo
		if(time >= tempos[0][0]):
			# Return it
			return tempos[0][1]
		# Otherwise return the default 120 BPM
		return 500000
	# Sort the tempos by time
	tempos.sort(key=lambda e: e[0])
	# If time is in seconds and not ticks
	if(seconds):
		# If ticks_per_beat was not specified
		if(ticks_per_beat == 0):
			# Throw an error
			raise Exception("Error: ticks_per_beat cannot be 0")
		# Create a variable to store time in
		total_time = 0
		# Loop through the tempos
		for i in range(0, len(tempos)):
			# If this is the first loop iteration
			if(i == 0):
				# Assume the tempo is initially 120 BPM if it is not specified at the beginning
				total_time += mido.tick2second(tempos[i][0], ticks_per_beat, 500000)
			# Otherwise
			else:
				# Add the difference in time to the total time
				total_time += mido.tick2second(tempos[i][0] - tempos[i - 1][0], ticks_per_beat, tempos[i - 1][1])
			# Set the tempo's time to the calculated time
			tempos[i][0] = total_time
	# Loop through the tempos in the list
	for i in range(0, len(tempos) - 1):
		# If have passed this tempo but not the next tempo
		if(time >= tempos[i][0] and time < tempos[i + 1][0]):
			# Return it
			return tempos[i][1]
	# If we've passed all of them, return the last one
	return tempos[len(tempos) - 1][1]

# Create an more aptly named method that converts the note time from ticks to seconds
def notes2second(input_notes, tempo_dict, ticks_per_beat):
	return convert_note_time(input_notes, tempo_dict, ticks_per_beat, True)

# Create an more aptly named method that converts the note time from seconds to ticks
def notes2tick(input_notes, tempo_dict, ticks_per_beat):
	return convert_note_time(input_notes, tempo_dict, ticks_per_beat, False)

# Create a method to convert the note time from seconds to ticks or vice versa
def convert_note_time(input_notes, tempo_dict, ticks_per_beat, to_second):
	
	# Create a copy of the notes list
	notes = copy.deepcopy(input_notes)

	# Store a list of times that the tempo changes
	tempo_change_times = [[key, -1] for key in tempo_dict.keys()]

	# Add the tempo change times to the notes list so we know when to change the tempo
	for time in tempo_change_times:
		notes.append(time)

	# Re-sort the list so that the tempo change times are at the right times
	notes.sort(key=lambda e: (e[0], e[1]))

	# Set the tempo to the first tempo
	current_tempo = get_tempo(tempo_dict, 0, seconds=not to_second, ticks_per_beat=ticks_per_beat)

	# Round down if necessary
	getcontext().rounding = ROUND_DOWN

	# Create a variable to keep track of the current time in the output units
	total_time = Decimal(0)

	# Create a variable to keep track of the last time in the input units 
	last_time = Decimal(0)

	# Convert note start time
	for note in notes:
		# If this is a tempo message
		if(note[1] == -1):
			# Set the tempo
			current_tempo = note[0]
		# If we are converting to seconds
		if(to_second):
			# Add to the converted time to the total time
			total_time += tick2second(note[0] - last_time, ticks_per_beat, get_tempo(tempo_dict, note[0]))
		# Otherwise
		else:
			# Round the output and cast it to an int, then increment total_time
			total_time += second2tick(note[0] - last_time, ticks_per_beat, get_tempo(tempo_dict, note[0], seconds=True, ticks_per_beat=ticks_per_beat))
		# Set last_time to the value that the note had
		last_time = note[0]
		# If we are converting to seconds
		if(to_second):
			# Set the note's start time to the current time in the new unit
			note[0] = total_time
		# Otherwise
		else:
			# Cast the time to an int, then set the note's start time to the current time in the new unit
			note[0] = int(total_time)

	# Delete the tempo messages
	notes = [note for note in notes if note[1] >= 0]

	# Store a list of times that the tempo changes
	tempo_change_times = [[-1, key] for key in tempo_dict.keys()]

	# Add the tempo change times to the notes list so we know when to change the tempo
	for time in tempo_change_times:
		notes.append(time)

	# Re-sort the list so that the tempo change times are at the right times
	notes.sort(key=lambda e: (e[1], e[0]))

	# Set the tempo to the first tempo
	current_tempo = get_tempo(tempo_dict, 0, seconds=not to_second, ticks_per_beat=ticks_per_beat)
	
	# Reset the variable to keep track of the current time in the output units
	total_time = Decimal(0)

	# Reset the variable to keep track of the last time in the input units 
	last_time = Decimal(0)

	# Convert note end time
	for note in notes:
		# If this is a tempo message
		if(note[0] == -1):
			# Set the tempo
			current_tempo = note[1]
		# If we are converting to seconds
		if(to_second):
			# Add to the converted time to the total time
			total_time += tick2second(note[1] - last_time, ticks_per_beat, get_tempo(tempo_dict, note[1]))
		# Otherwise
		else:
			# Round the output and cast it to an int, then increment total_time
			total_time += second2tick(note[1] - last_time, ticks_per_beat, get_tempo(tempo_dict, note[1], seconds=True, ticks_per_beat=ticks_per_beat))
		# Set last_time to the value that the note had
		last_time = note[1]
		# If we are converting to seconds
		if(to_second):
			# Set the note's start time to the current time in the new unit
			note[1] = total_time
		# Otherwise
		else:
			# Cast the time to an int, then set the note's start time to the current time in the new unit
			note[1] = int(total_time)

	# Delete the tempo messages
	notes = [note for note in notes if note[0] >= 0]

	# Re-sort the notes
	notes.sort(key=lambda e: e[0])

	# Return the notes list
	return notes

# Redefine the tick2second method from mido to use decimals instead of floats
def tick2second(tick, ticks_per_beat, tempo):
	# Conversion factor from ticks to seconds
    scale = Decimal(tempo) * Decimal(1e-6) / Decimal(ticks_per_beat)
	# Multiple by the scaling factor
    return Decimal(tick) * scale

# Redefine the second2tick method from mido to use decimals instead of floats
def second2tick(second, ticks_per_beat, tempo):
	# Conversion factor from ticks to seconds
    scale = Decimal(tempo) * Decimal(1e-6) / Decimal(ticks_per_beat)
	# Divide by the scaling factor
    return Decimal(second) / scale