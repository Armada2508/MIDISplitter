import mido
from mido import Message, MidiFile, MidiTrack
import constants as c

def parse(input_file, output_file, velocity):

	# =====================
	#    Initialization
	# =====================

	# Check if the input or output file wasn't given
	if(input_file == "" or output_file == ""):
		return

	# Create lists for storing notes and meta messages
	track_notes = []
	track_meta = []

	# Load the input MIDI file
	input_song = mido.MidiFile(input_file)

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

	# ==========================
	#     Loop Through Tracks
	# ==========================

	for i, track in enumerate(input_song.tracks):

		# ==============================
		#     Raw Message Extraction
		# ==============================

		# Store all note related messages in a list
		note_messages = [msg for msg in track if msg.type == "note_on" or msg.type == "note_off" or msg.type == "control_change"]

		# Store all meta messages in a list
		meta_messages = [msg for msg in track if msg.is_meta]

		# Create a time variable for storing absolute time and set it to 0
		tickTime = 0

		# Create a new empty list inside the main list for all tracks to append notes to
		track_meta.append([])
		# Create a new empty list inside the main list for all tracks to append meta messages to
		track_notes.append([])

		# Loop through all meta messages
		for msg in meta_messages:
			# Append the message to the meta list for this track
			track_meta[i].append(msg)

		# If this is just a meta track
		if(len(note_messages) == 0):
			# Create a new track
			finished_track = mido.MidiTrack()
			# Append the track to the output song
			output_song.tracks.append(finished_track)
			# Append all messages to the new track
			for msg in track_meta[i]:
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
		for j, msg in enumerate(note_messages):
			# If this is the last message
			if(j == len(note_messages) - 1):
				off = False

			# If there is a change in time then add that to the absolute time
			tickTime += msg.time
			# If this is a note on message
			if(msg.type == "note_on"):
				if(msg.velocity != 0):
					# Create a new entry in the form of [TIME ON, TIME OFF, NOTE, VELOCITY]
					track_notes[i].append([tickTime, None, msg.note, msg.velocity])
				else:
					# Loop through the notes list backwards
					for j in reversed(range(len(track_notes[i]))):
						if(msg.note in sostenuto_notes):
							break
						# Check if there is a note that is the same note and doesn't end yet
						if(track_notes[i][j][2] == msg.note and track_notes[i][j][1] == None):
							# Add the current time as its end time
							track_notes[i][j][1] = tickTime
			# If this is a note off message and sustain is not active
			if(msg.type == "note_off" and not sustain):
				# Loop through the notes list backwards
				for j in reversed(range(len(track_notes[i]))):
					if(msg.note in sostenuto_notes):
						break
					# Check if there is a note that is the same note and doesn't end yet
					if(track_notes[i][j][2] == msg.note and track_notes[i][j][1] == None):
						# Add the current time as its end time
						track_notes[i][j][1] = tickTime
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
					note[1] = tickTime

			# If sostenuto has been released
			if(sostenuto_last and not sostenuto):
				# Loop through all notes
				for note in track_notes[i]:
					# Loop through all notes being sustained by sostenuto
					for sostenuto_note in sostenuto_notes:
						# If they have the same pitch and the note has no end time
						if(note[2] == sostenuto_note and note[1] == None):
							# Set its end time to now
							note[1] = tickTime

			# If there is an all notes off message
			if(off):
				# Loop through all notes
				for note in track_notes[i]:
					# If the note doesn't have an end time
					if(note[1] == None):
						# Set its end time to now
						note[1] = tickTime
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

		# =====================
		#    Note Processing
		# =====================

		# If there are any notes that have the same end and start time(0 duration), delete them
		track_notes[i] = [note for note in track_notes[i] if note[0] != note[1]]

		# Remove duplicate notes
		track_notes[i] = [list(t) for t in set(tuple(e) for e in track_notes[i])]

		# Re-sort the list
		track_notes[i].sort(key=lambda e: e[0])

		# ======================
		#    Track Splitting
		# ======================

		# Create a new list for new tracks
		new_tracks = []

		# Iterate through all notes
		for note in track_notes[i]:
			# Update the time to the current note's start time
			tickTime = note[0]

			# Calculate the track index of the note
			track_index = get_track_index(note, track_notes[i])

			# If we need more tracks, add them
			for j in range(0, 1 + track_index - len(new_tracks)):
				new_tracks.append([])

			# Add the note to its track
			new_tracks[track_index].append(note)


		# ======================
		#      Track Output
		# ======================

		for j, new_track in enumerate(new_tracks):
			# Create a new track to append to the MIDI file that will be exported
			finished_track = mido.MidiTrack()

			# Add the track to the output file
			output_song.tracks.append(finished_track)

			# Re-use tickTime and set it to 0
			tickTime = 0

			# Set the finished track name to the old track name with an index starting with 1
			finished_track.name = track.name + " " + str(j + 1)

			# Loop through all of the notes in the new track
			for note in new_track:
				# Add a note_on message for the note
				finished_track.append(Message("note_on", note=note[2], velocity=new_velocity if new_velocity >= 0 else note[3], time=(note[0] - tickTime)))
				# Add a note_off message for the note
				finished_track.append(Message("note_off", note=note[2], velocity=0, time=(note[1] - note[0])))
				# Set the absolute time to the last message added(the note_off message)
				tickTime = note[1]

	# Save the song
	output_song.save(output_file)

# Check if two notes overlap
def check_overlap(note, check):
	# If the check note's endpoints are not both before and after the note, it must overlap
	return not ((check[0] < note[0] and check[1] <= note[0]) or (check[0] >= note[1] and check[1] > note[1]))

# Find all overlapping notes
def find_overlaps(note, notes):
	# Return a list of notes that pass the check_overlap test
	return list(filter(lambda e: check_overlap(note, e), notes))

# Find notes that overlap and are above the note
def get_notes_above(note, notes):
	# Return a list of notes that overlap and have a pitch greater than the note
	return list(filter(lambda e: e[2] > note[2], find_overlaps(note, notes)))

# Get the track index of a note
def get_track_index(note, notes):
	# Get the notes above this note
	notes_above = get_notes_above(note, notes)
	# Default the track index to 0
	track_index = 0
	# Create a list for storing the indices of the notes above this note
	track_indices = []
	# If there are no notes above this note
	if(len(notes_above) == 0):
		# It's track_index is 0
		return track_index
	# If there are notes above it, loop through them
	for note in notes_above:
		# Check their track index and add it to the list
		track_indices.append(get_track_index(note, notes))
	# Find the lowest number not in the list greater than 0
	while track_index in track_indices:
		track_index += 1
	# Return it
	return track_index