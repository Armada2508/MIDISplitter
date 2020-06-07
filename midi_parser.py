import mido

def parse(filename):
	song = mido.MidiFile(filename)
	for i, track in enumerate(song.tracks):
		print('Track {}: {}'.format(i, track.name))
		for msg in track:
			print(msg)