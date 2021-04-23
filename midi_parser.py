import mido
from mido import MetaMessage, Message, MidiFile, MidiTrack
import constants as c
from decimal import Decimal, ROUND_UP, getcontext
import copy
import traceback

def parse(input_file, output_file, new_velocity, align_margin, collated, normalized_tempo, create_channels, index_patches):

	# TODO: Extract parts of parse function into other functions
	# TODO: Options for merging tracks
	# TODO: Align notes in different tracks
	# TODO: Use channels to split tracks

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

	# If index_patches is selected but not create_channels
	if(index_patches and not create_channels):
		return Exception("Patches cannot be indexed without creating channels")

	# Create lists for storing notes and meta messages
	track_notes = []
	track_meta = []

	# Create a list for storing final tracks
	output_tracks = []

	# Create a list to store which output tracks are only meta
	meta_track_indices = []

	# Create a dictionary to store the patch of each track
	patch_dictionary = {}

	# Create a list to store which indices tracks are split into
	split_indices = []

	# Try to load the input file
	try:
		# Load the input MIDI file
		input_song = mido.MidiFile(input_file)
	except Exception as err:
		# Print the error
		traceback.print_tb(err.__traceback__)
		# If it couldn't be loaded, return an error
		return Exception("Input file could not be loaded, try checking the input file path")

	# Create a new MIDI file for the final song
	output_song = mido.MidiFile(ticks_per_beat=input_song.ticks_per_beat)
	
	# Check if we should override the note velocity
	try:
		# See if the user has input an integer
		new_velocity = int(new_velocity)
	except:
		# If the user has not input an integer, ignore it
		new_velocity = -1
		pass

	# If it's out of range, set it to -1
	if(new_velocity < 1 or new_velocity > 127):
		new_velocity = -1
	
	# Check if we should override the tempo
	try:
		# See if the user has input an integer
		normalized_tempo = int(normalized_tempo)
		# Convert the tempo from bpm to the correct units
		normalized_tempo = mido.bpm2tempo(normalized_tempo)
	except:
		# If the user has not inputted an integer, ignore it
		normalized_tempo = -1
		pass

	# If it's out of range, set it to -1
	if(normalized_tempo < 1):
		normalized_tempo = -1

	# Cast the parameter to a boolean
	create_channels = bool(create_channels)

	# Cast the parameter to a boolean
	index_patches = bool(index_patches)

	# Create a dictionary to serve as a look up table for tempo
	tempo_dict = {}

	# Create a aligning margin variable
	alignment_margin = 0

	try:
		# See if the user has input a number
		alignment_margin = float(align_margin)
	except:
		pass


	# ============================
	#    Extract Tempo Messages
	# ============================
	
	# Loop through all tracks
	for i, track in enumerate(input_song.tracks):

		# Create a time variable for storing absolute time and set it to 0
		tick_time = 0
		
		# Loop through all notes in the track
		for j, msg in enumerate(track):

			# If there is a change in time then add that to the absolute time
			tick_time += msg.time

			# If we found a set_tempo message
			if(msg.is_meta and msg.type == "set_tempo"):
				# Add it to the look up table
				tempo_dict[tick_time] = msg.tempo


	# If there are no tempo messages
	if(len(tempo_dict) == 0):
		# Set the tempo to the default of 120bpm
		tempo_dict[0] = mido.bpm2tempo(120)


	# ==========================
	#     Loop Through Tracks
	# ==========================

	for i, track in enumerate(input_song.tracks):

		# ===================================
		#    Program/Patch Change Messages
		# ===================================
		
		# Create a time variable for storing absolute time and set it to 0
		tick_time = 0

		# Loop through all messages
		for msg in track:
			
			# If there is a change in time then add that to the absolute time
			tick_time += msg.time

			# If this message is a patch change message
			if(msg.type == "program_change"):
				# If this channel doesn't have a dictionary entry
				if not msg.channel in patch_dictionary:
					# Make an entry
					patch_dictionary[msg.channel] = {}
				# Add a patch entry for the current channel at the current time
				patch_dictionary[msg.channel][tick_time] = msg.program

		# ==============================
		#     Raw Message Extraction
		# ==============================

		# Store all meta messages in a list
		meta_messages = [msg for msg in track if msg.is_meta]

		# Reset tick_time to zero
		tick_time = 0

		# Create a new empty list inside the main list for all tracks to append notes to
		track_meta.append([])

		# Create a new empty list inside the main list for all tracks to append meta messages to
		track_notes.append([])
		
		# Loop through all meta messages
		for msg in meta_messages:
			# Append the message to the meta list for this track
			track_meta[i].append(msg)

		# ======================
		#    Meta-only tracks
		# ======================

		# If this is just a meta track
		if(len(meta_messages) == len(track)):
			# We'll first assume the split index is 0
			split_index = 0
			# If this is not the first track
			if(i != 0):
				# Get the indices the previous track was split into
				previous_track = split_indices[len(split_indices) - 1]
				# Set the split index as the previous maximum index plus one
				split_index = previous_track[len(previous_track) - 1] + 1
			# Append this index to the list
			split_indices.append([split_index])
			
			# Add this track index to the list recording which tracks are only meta
			meta_track_indices.append(len(output_tracks))
			# Add sub-list where this track will be stored
			output_tracks.append([])
			# Create a new track
			finished_track = MidiTrack()
			# Append this track to the sub-list
			output_tracks[len(output_tracks) - 1].append(finished_track)
			# Create a new variable to keep track of skipped delta time
			skipped_ticks = 0
			# Loop through all messages
			for msg in track_meta[i]:
				# If this is a tempo message
				if(msg.type == "set_tempo"):
					# Increase the skipped time by the amount of this message
					skipped_ticks += msg.time
					# Don't append it
					continue
				# Increase this message's time by the amount of skipped ticks
				msg.time += skipped_ticks
				# Reset the amount of skipped time
				skipped_ticks = 0
				# Append message to the finished track
				finished_track.append(msg)
			# Skip everything below
			continue

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
				# Turn all notes off
				off = True

			# If there is a change in time then add that to the absolute time
			tick_time += msg.time

			# If this is a note on message
			if(msg.type == "note_on"):
				# If the note has a nonzero velocity
				if(msg.velocity != 0):
					# Create a new entry with the format of [TIME ON, TIME OFF, NOTE, VELOCITY, ALIGNED, TRACK INDEX, CHANNEL, PATCH]
					track_notes[i].append([tick_time, None, msg.note, msg.velocity, 0, None, msg.channel, get_patch(patch_dictionary, msg.channel, tick_time)])
					# If this channel doesn't already have a patch
					if(patch_dictionary[msg.channel] == None):
						# Assume that it is has a default patch of 1
						patch_dictionary[msg.channel] = 1
				# If the note has a zero velocity
				else:
					# Loop through the notes list backwards
					for j in reversed(range(len(track_notes[i]))):
						if(msg.note in sostenuto_notes):
							break
						# Check if there is a note that is the same note and doesn't end yet
						if(track_notes[i][j][2] == msg.note and track_notes[i][j][1] == None):
							# Set the current time as its end time
							track_notes[i][j][1] = tick_time
			# If this is a note off message and sustain is not active
			if(msg.type == "note_off" and not sustain):
				# If this note is being sustained by sostenuto
				if(msg.note in sostenuto_notes):
					# Don't stop it
					break
				# Loop through the notes list backwards
				for j in reversed(range(len(track_notes[i]))):
					# Check if there is an active note that doesn't end yet
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
				# Turn the all notes off flag off
				off = False

			# Set the current value of sustain to the last variable for the next loop
			sustain_last = sustain
			# Set the current value of sostenuto to the last variable for the next loop
			sostenuto_last = sostenuto

		# =====================
		#    Note Processing
		# =====================

		# If there are any notes that have the same end and start time(0 duration), delete them
		track_notes[i] = [note for note in track_notes[i] if note[0] != note[1]]

		# Remove duplicate notes
		track_notes[i] = [list(new_note) for new_note in set(tuple(note) for note in track_notes[i])]

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

		# If we should not normalize the tempo
		if(normalized_tempo < 0):
			# Convert the note time back to ticks with the original tempos
			track_notes[i] = notes2tick(track_notes[i], tempo_dict, input_song.ticks_per_beat)
		# If we should normalize the tempo
		else:
			# Convert the note time back to ticks with a single tempo
			track_notes[i] = notes2tick(track_notes[i], {0: normalized_tempo}, input_song.ticks_per_beat)


		# Only keep notes that do not have the same start and end time(nonzero duration)
		track_notes[i] = [note for note in track_notes[i] if note[0] != note[1]]
		
		# Sort the notes by their start time
		track_notes[i].sort(key=lambda e: e[0])

		# ======================
		#    Track Splitting
		# ======================

		# Create a new list for new(split) tracks
		new_tracks = []

		# Iterate through all notes in the current track
		for note in track_notes[i]:
			# Calculate the track index of the note
			track_index = get_track_index(note, track_notes[i])

			# If we need more tracks, add them
			for j in range(1 + track_index - len(new_tracks)):
				new_tracks.append([])

			# Add the note to its track
			new_tracks[track_index].append(note)

		# ==================
		#      Indexing
		# ==================

		# Create a new variable to store the starting index
		initial_index = 0

		# Loop through all split tracks in the output_tracks list
		for split_tracks in output_tracks:
			# Increase the starting index by the amount of split tracks
			initial_index += len(split_tracks)

		# If we are indexing patches
		if(index_patches):
			# For every new track
			for i, new_track in enumerate(new_tracks):
				# Loop through the notes
				for note in new_track:
					# Set the patch to a clamped index value between 0 and 127
					note[7] = min(max(0, initial_index + i), 127)


		# ======================
		#      Track Output
		# ======================

		# Add parent list where split tracks from this track will be stored
		output_tracks.append([])

		for j, new_track in enumerate(new_tracks):
			# Create a new track to append to the MIDI file that will be exported
			finished_track = MidiTrack()

			# Use tick_time to represent absolute time and set it to 0
			tick_time = 0

			# Set the finished track name to the old track name concatenated with an index starting with 1
			finished_track.name = track.name + " " + str(j + 1)

			# Loop through all of the notes in the new track
			for note in new_track:
				# Add a note_on message for the note
				finished_track.append(Message("note_on", note=note[2], velocity=new_velocity if new_velocity >= 0 else note[3], time=(note[0] - tick_time), channel=note[6]))
				# Add a note_off message for the note
				finished_track.append(Message("note_off", note=note[2], velocity=0, time=(note[1] - note[0]), channel=note[6]))
				# Set the absolute time counter to the last message added(the note_off message)
				tick_time = note[1]
			
			# Append the finished track to the list of tracks to be output
			output_tracks[i].append(finished_track)
		
		# We'll first assume the starting index is 0
		starting_index = 0
		# If this is not the first track
		if(i != 0):
			# Get the indices the previous track was split into
			previous_track = split_indices[len(split_indices) - 1]
			
			# Set the starting index as the previous maximum index plus one
			starting_index = previous_track[len(previous_track) - 1] + 1
		# Append a sub-list to store the indices this track is split into
		split_indices.append([])
		# Loop through the number of tracks this track will be split into
		for j in range(len(output_tracks[i])):
			# Add the indices to the sub-list
			split_indices[i].append(starting_index + j)

	# =======================
	#     Song Processing
	# =======================

	# If we are collating the output
	if(collated):
		# Create a variable to store the maximum number of times a track was split
		max_split = 0
		# Loop through all tracks
		for split_track in output_tracks:
			# If this track was split more times, make it the new maximum
			max_split = max(max_split, len(split_track))
		# Loop through the sub-lists
		for i in range(max_split):
			# Loop through the initial(outer) lists
			for split_track in output_tracks:
				# If we have already appended all split tracks on this track
				if(i >= len(split_track)):
					# Skip this loop iteration
					continue
				# Add track to output file
				output_song.tracks.append(split_track[i])
	# If the tracks should not be collated
	else:
		# Flatten the list of output tracks
		output_tracks = [output_track for split_track in output_tracks for output_track in split_track]
		# Loop through tracks
		for track in output_tracks:
			# Add track to output file
			output_song.tracks.append(track)

	# If we should normalize the tempo
	if(normalized_tempo > 0):
		# Set the tempo at the beginning of the song
		output_song.tracks[0].insert(0, MetaMessage("set_tempo", tempo=normalized_tempo))
	# If we are not normalizing the tempo
	else:

		# If there are no meta only tracks
		if(len(meta_track_indices) == 0):
			# Create a new track
			output_song.tracks.insert(0, MidiTrack())
			# Add its index to the list of meta only tracks
			meta_track_indices.append(0)

		# Create a list to store tempos in
		tempos = []

		# Convert tempo_dict to a 2d list
		for time in tempo_dict:
			tempos.append([time, tempo_dict[time]])
		
		# Re-use tick_time to store absolute time
		tick_time = 0

		# Create a variable to store the index of the last tempo inserted
		tempo_index = 0

		# Create a variable to store the total length of the track
		total_time = 0

		# Get the length of the track
		for msg in output_song.tracks[meta_track_indices[0]]:
			total_time += msg.time
		
		# Create a new variable to store if the first meta track is empty
		first_meta_empty = len(output_song.tracks[meta_track_indices[0]]) == 0

		# Loop through the first meta track to which we will add tempo messages(which will be the original length + # of tempo messages when done)
		for i in range(len(output_song.tracks[meta_track_indices[0]]) + len(tempos)):
			# If we addded all the tempos
			if(tempo_index == len(tempos)):
				# Stop adding them
				break
			# If the meta track is/was empty
			if(first_meta_empty):
				# Insert the message
				output_song.tracks[meta_track_indices[0]].append(MetaMessage("set_tempo", tempo=tempos[tempo_index][1], time=tempos[tempo_index][0]-tick_time))
				# Increment tick_time
				tick_time += output_song.tracks[meta_track_indices[0]][i].time
				# Increment the tempo index
				tempo_index += 1
				# Skip everything below
				continue
			# Increment tick_time
			tick_time += output_song.tracks[meta_track_indices[0]][i].time
			# If we're at the end of the list
			if(i == len(output_song.tracks[meta_track_indices[0]]) - 1):
				# Insert the message
				output_song.tracks[meta_track_indices[0]].append(MetaMessage("set_tempo", tempo=tempos[tempo_index][1], time=tempos[tempo_index][0]-tick_time))
				# Increment the tempo index
				tempo_index += 1
				# Skip everything below
				continue
			# If the tempo is between these messages
			if(tick_time <= tempos[tempo_index][0] and tempos[tempo_index][0] <= tick_time + output_song.tracks[meta_track_indices[0]][i + 1].time):
				# Decrease the delta of the message after it
				output_song.tracks[meta_track_indices[0]][i + 1].time -= tempos[tempo_index][0]-tick_time
				# Insert the message
				output_song.tracks[meta_track_indices[0]].insert(i + 1, MetaMessage("set_tempo", tempo=tempos[tempo_index][1], time=tempos[tempo_index][0]-tick_time))
				# Increment the tempo index
				tempo_index += 1
		# If we didn't add all the tempos
		if(tempo_index < len(tempos) - 1):
			# Loop through the remaining tempos
			for i in range(tempo_index, len(tempos)):
				# Append the remaining messages
				output_song.tracks[meta_track_indices[0]].append(MetaMessage("set_tempo", tempo=tempos[i][1], time=tempos[i][0]-tick_time))
				# Set tick_time
				tick_time = tempos[i][0]

	# If we are assigning patches on the output tracks
	if(index_patches):
		# Loop through all the tracks
		for i, track in enumerate(output_song.tracks):
			# Start off with a patch index of the current track index
			patch_index = i
			# For every meta only track before it, subtract one
			for index in meta_track_indices:
				if index < i:
					patch_index -= 1
			# Set the patch of each of the track
			output_song.tracks[i] = set_track_patch(track, patch_index, patch_index)

					
	# If we are creating output channels
	if(create_channels):
		# Loop through all the tracks
		for i, track in enumerate(output_song.tracks):
			# Start off with a channel index of the current track index
			channel_index = i
			# For every meta only track before it, subtract one
			for index in meta_track_indices:
				if index < i:
					channel_index -= 1
			# Set the channel of each of the tracks
			output_song.tracks[i] = set_channel(track, channel_index)
	

	# ====================
	#     Song Output
	# ====================


	# Try to save the song
	try:
		# Save the song
		output_song.save(output_file)
		# If it saves, return true
		return True
	except Exception as err:
		# Print the error
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
	# Return a list of notes that overlap and have a pitch greater than the not or have a pitch equal to and start earlier than the note
	return list(filter(lambda e: e[2] > note[2] or (e[2] == note[2] and e[0] > note[0]), find_overlaps(note, notes)))

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

# Find the tempo at a specific time with dictionary of tempos
def get_tempo(d, time, ticks_per_beat=0, seconds=False):
	# Create a list to store the tempos at different times
	tempos = []

	# Loop through the tempos in the dictionary
	for t, tempo in d.items():
		# Add each tempo to the list
		tempos.append([t, tempo])

	# If there are no items
	if(len(tempos) == 0):
		# Return the default 120 BPM
		return 500000

	# If we haven't passed the first tempo
	if(time < tempos[0][0]):
		# Return the default 120 BPM
		return 500000

	# If there is only one item
	if(len(tempos) == 1):
		# Return it(we've passed it)
		return tempos[0][1]

	# Sort the tempos by time
	tempos.sort(key=lambda e: e[0])
	# If time is in seconds and not ticks
	if(seconds):
		# If ticks_per_beat was not specified
		if(ticks_per_beat == 0):
			# Throw an error
			raise Exception("Error: ticks_per_beat cannot be 0")
		# Create a new list to store the converted tick times
		tempo_times = []
		# Create a variable to store time in
		total_time = 0
		# Loop through the tempos
		for i in range(len(tempos)):
			# If this is the first loop iteration
			if(i == 0):
				# Assume the tempo is initially 120 BPM if it is not specified at the beginning
				total_time += mido.tick2second(tempos[i][0], ticks_per_beat, 500000)
			# Otherwise
			else:
				# Add the difference in time to the total time
				total_time += mido.tick2second(tempos[i][0] - tempos[i - 1][0], ticks_per_beat, tempos[i - 1][1])
			# Record the tempo's time
			tempo_times.append(total_time)
		# Loop through the tempos
		for i in range(len(tempos)):
			# Set the new end times
			tempos[i][0] = tempo_times[i]

		
	# Loop through the tempos in the list(until one index before the last element)
	for i in range(len(tempos) - 1):
		# If we have passed this tempo but not the next tempo
		if(time >= tempos[i][0] and time < tempos[i + 1][0]):
			# Return it
			return tempos[i][1]

	# If we've passed all of them, return the last one
	return tempos[len(tempos) - 1][1]

def get_patch(patch_dict, channel, time):
	# Set the default patch to time 0 and patch 0
	last_patch = (0, 0)
	# Loop through all patches for this note's channel
	for patch_time in patch_dict[channel]:
		# If the patch starts before the note
		if(patch_time < time):
			# Set last_patch equal to (time, patch #)
			last_patch = (patch_time, patch_dict[channel][patch_time])
			# Skip this loop iteration
			continue
		# If the note is before the past, but after the last
		if(time < patch_time and last_patch[0] < time):
			# Return the last patch
			return last_patch[1]
	# If the note was after all patches, set it to the last patch
	return last_patch[1]


# Create a more aptly named method that converts the note time from ticks to seconds
def notes2second(input_notes, tempo_dict, ticks_per_beat):
	return convert_note_time(input_notes, tempo_dict, ticks_per_beat, True)

# Create a more aptly named method that converts the note time from seconds to ticks
def notes2tick(input_notes, tempo_dict, ticks_per_beat):
	return convert_note_time(input_notes, tempo_dict, ticks_per_beat, False)

# Create a method to convert the note time from seconds to ticks or vice versa
def convert_note_time(input_notes, tempo_dict, ticks_per_beat, to_second):
	
	# Create a copy of the notes list
	notes = copy.deepcopy(input_notes)

	# Round up
	getcontext().rounding = ROUND_UP

	# Use 12 significant digits
	getcontext().prec = 12

	# Store a list of times that the tempo changes
	tempo_changes = [[time, -1] for time in tempo_dict.keys()]

	# Add the tempo change times to the notes list so we know when to change the tempo
	for time in tempo_changes:
		notes.append(time)

	# Create a variable to keep track of the current time in the output units
	total_time = Decimal(0)

	# Create a variable to keep track of the last time in the input units 
	last_time = Decimal(0)

	# Create a variable to store the current tempo
	current_tempo = get_tempo(tempo_dict, 0)
	
	# If we are converting to ticks we have to convert the tempo times to seconds
	if(not to_second):
		# Loop through all of the tempo changes
		for i in range(len(tempo_changes)):
			# Calculate the current tempo
			current_tempo = get_tempo(tempo_dict, total_time)
			# If this is the first loop iteration
			if(i == 0):
				# Use the default tempo of 120 BPM to calculate the time before the first tempo message
				total_time += tick2second(tempo_changes[i][0], ticks_per_beat, current_tempo)
			# If this is not the first loop iteration
			else:
				# Calculate the amount of time since the previous tempo message and convert it
				total_time += tick2second(tempo_changes[i][0] - last_time, ticks_per_beat, current_tempo)
			# Update last_time
			last_time = Decimal(tempo_changes[i][0])
			# Update the tempo message's time
			tempo_changes[i][0] = total_time
	
	# Re-sort the list so that the tempo change times are at the right times
	notes.sort(key=lambda e: (e[0], e[1]))

	# Reset the variable storing the current tempo
	current_tempo = get_tempo(tempo_dict, 0)
	
	# Reset the variable to keep track of the current time in the output units
	total_time = Decimal(0)

	# Reset the variable to keep track of the last time in the input units 
	last_time = Decimal(0)

	# Convert note start time
	for note in notes:
		# If we are converting to seconds
		if(to_second):
			# Add to the converted time to the total time
			total_time += tick2second(note[0] - last_time, ticks_per_beat, current_tempo)
		# Otherwise
		else:
			# Add to the converted time to the total time
			total_time += second2tick(note[0] - last_time, ticks_per_beat, current_tempo)
		# If this is a tempo message
		if(note[1] == -1):
			# If we are converting to seconds
			if(to_second):
				# Set the tempo
				current_tempo = get_tempo(tempo_dict, note[0])
			# If we are converting to ticks
			else:
				# Set the tempo
				current_tempo = get_tempo(tempo_dict, note[0], seconds=True, ticks_per_beat=ticks_per_beat)
		# Set last_time to the value that the note had
		last_time = Decimal(note[0])
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
	tempo_changes = [[-1, time] for time in tempo_dict.keys()]

	# Reset the variable storing the current tempo
	current_tempo = get_tempo(tempo_dict, 0)

	# Reset the variable to keep track of the current time in the output units
	total_time = Decimal(0)

	# Reset the variable to keep track of the last time in the input units 
	last_time = Decimal(0)
	
	# If we are converting to ticks we have to convert the tempo times to seconds
	if(not to_second):
		# Loop through all of the tempo changes
		for i in range(len(tempo_changes)):
			# Calculate the current tempo
			current_tempo = get_tempo(tempo_dict, total_time)
			# If this is the first loop iteration
			if(i == 0):
				# Use the default tempo of 120 BPM to calculate the time before the first tempo message
				total_time += tick2second(tempo_changes[i][1], ticks_per_beat, current_tempo)
			# If this is not the first loop iteration
			else:
				# Calculate the amount of time since the previous tempo message and convert it
				total_time += tick2second(tempo_changes[i][1] - last_time, ticks_per_beat, current_tempo)
			# Update last_time
			last_time = Decimal(tempo_changes[i][1])
			# Update the tempo message's time
			tempo_changes[i][1] = total_time

	# Add the tempo change times to the notes list so we know when to change the tempo
	for time in tempo_changes:
		notes.append(time)

	# Re-sort the list so that the tempo change times are at the right times
	notes.sort(key=lambda e: (e[1], e[0]))
	
	# Reset the variable to keep track of the current time in the output units
	total_time = Decimal(0)

	# Reset the variable to keep track of the last time in the input units 
	last_time = Decimal(0)

	# Reset the variable storing the current tempo
	current_tempo = get_tempo(tempo_dict, 0)

	# Convert note end time
	for note in notes:
		# If we are converting to seconds
		if(to_second):
			# Add to the converted time to the total time
			total_time += tick2second(note[1] - last_time, ticks_per_beat, current_tempo)
		# Otherwise
		else:
			# Add to the converted time to the total time
			total_time += second2tick(note[1] - last_time, ticks_per_beat, current_tempo)
		# If this is a tempo message
		if(note[0] == -1):
			# If we are converting to seconds
			if(to_second):
				# Set the tempo
				current_tempo = get_tempo(tempo_dict, note[1])
			# If we are converting to ticks
			else:
				# Set the tempo
				current_tempo = get_tempo(tempo_dict, note[1], seconds=True, ticks_per_beat=ticks_per_beat)
		# Set last_time to the value that the note had
		last_time = Decimal(note[1])
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
	# Multiply by the scaling factor
    return Decimal(tick) * scale

# Redefine the second2tick method from mido to use decimals instead of floats
def second2tick(second, ticks_per_beat, tempo):
	# Conversion factor from ticks to seconds
    scale = Decimal(tempo) * Decimal(1e-6) / Decimal(ticks_per_beat)
	# Divide by the scaling factor
    return Decimal(second) / scale

# Set the channel of all messages in a track
def set_channel(track, channel_index):
	# If the channel_index is out of range
	if(channel_index < 0 or channel_index > 15):
		# Force it into range
		channel_index = min(max(channel_index, 0), 15)
	# Loop through all messages
	for msg in track:
		# Try to set the channel
		try:
			msg.channel = channel_index
		# If it fails, don't worry about it
		except:
			pass
	# Return the track
	return track

# Set the patch of a track
def set_track_patch(track, patch_index, channel_index):
	# If the channel_index is out of range
	if(channel_index < 0 or channel_index > 15):
		# Force it into range
		channel_index = min(max(channel_index, 0), 15)
	# If the patch index is out of range
	if(patch_index < 0 or patch_index > 127):
		# Force it into range
		channel = min(max(channel, 0), 127)
	# Remove all patch change messages
	track = [msg for msg in track if not msg.type == "program_change"]
	# Insert a patch change message at the start of the track
	track.insert(1, Message("program_change", channel=channel_index, program=patch_index))
	# Return the track
	return track