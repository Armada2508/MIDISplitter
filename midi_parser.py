import mido
from mido import Message, MidiFile, MidiTrack
import constants as c
import numbers

def parse(input_file, output_file, velocity):

	# =====================
	#    Initialization
	# =====================

	# Create lists for storing notes and meta messages
	track_notes = []
	track_meta = []

	# Select the types of meta messages to be exported
	meta_types = ["time_signature", "set_tempo", "track_name", "end_of_track"]

	# Load the input file
	input_song = mido.MidiFile(input_file)

	# Create a new file for the final song
	output_song = mido.MidiFile(ticks_per_beat=input_song.ticks_per_beat)

	# Check if we should override the note velocity
	new_velocity = 0
	try:
		new_velocity = int(velocity)
	except:
		new_velocity = -1

	if(new_velocity < 0 or new_velocity > 127):
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

		# Set the time to 0
		tickTime = 0

		# Create a new empty list inside the main list for all tracks to append notes to
		track_meta.append([])
		# Create a new empty list inside the main list for all tracks to append meta messages to
		track_notes.append([])

		# Loop through all meta messages
		for msg in meta_messages:
			# If the meta message is one of the specified types
			if(msg.type in meta_types):
				# Append it to the meta list for this track
				track_meta[i].append(msg)
			# If it is a track name message
			if(msg.type == meta_types[2]):
				# Apply the time offset
				tickTime = msg.time

		# If this is just a meta track
		if(len([msg for msg in track if msg.type == "note_on" or msg.type == "note_off"]) == 0):
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

		sustain_last = False
		sustain = False
		sostenuto_last = False
		sostenuto = False
		sostenuto_notes = []
		off = False

		# Loop through all notes in the track
		for j, msg in enumerate(note_messages):
			# If this is the last note
			if(j == len(note_messages) - 1):
				# End all notes
				off = True
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
			if(msg.type == "control_change"):
				if(msg.control == 64):
					sustain = not msg.value < 64
				if(msg.control == 66):
					sostenuto = not msg.value < 64
				if(msg.control == 120):
					off = True
				if(msg.control == 121):
					sustain = False
					sostenuto = False
			
			if((sustain_last and not sustain) or off):
				notes_on = list(filter(lambda e: e[1] == None and e[2] not in sostenuto_notes, track_notes[i]))
				for note in notes_on:
					note[1] = tickTime

			if(sostenuto and not sostenuto_last):
				sostenuto_notes.clear()
				notes_on = list(filter(lambda e: e[1] == None, track_notes[i]))
				for note in notes_on:
					sostenuto_notes.append(note[2])
					
			if(sostenuto_last and not sostenuto):
				for note[2] in sostenuto_notes:
					note[1] = tickTime
			
			sustain_last = sustain
			sostenuto_last = sostenuto
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

		lastTime = 0

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

			for j in range(0, 1 + track_index - len(new_tracks)):
				new_tracks.append([])

			new_tracks[track_index].append(note)


		# ======================
		#      Track Output
		# ======================

		for j, new_track in enumerate(new_tracks):
			finished_track = mido.MidiTrack()

			output_song.tracks.append(finished_track)

			lastTime = 0

			finished_track.name = track.name + " " + str(j + 1)

			new_track.sort(key=lambda e: e[0])

			print("Track: " + finished_track.name)

			for note in new_track:
				if(note[0] - lastTime < 0):
					print("ON " + str(note))

				if(note[1] - note[0] < 0):
					print("OFF " + str(note))
				finished_track.append(Message("note_on", note=note[2], velocity=new_velocity if new_velocity >= 0 else note[3], time=(note[0] - lastTime)))
				finished_track.append(Message("note_off", note=note[2], velocity=0, time=(note[1] - note[0])))
				lastTime = note[1]

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
	notes_above = get_notes_above(note, notes)
	track_index = 0
	track_indices = []
	if(len(notes_above) == 0):
		return track_index
	for note in notes_above:
		track_indices.append(get_track_index(note, notes))
	while track_index in track_indices:
		track_index += 1
	return track_index