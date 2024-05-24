from pydub import AudioSegment
import pydub.playback

# Load the MP3 audio file
audio = AudioSegment.from_mp3("new1.mp3")

# Define the speed multiplier for slowing down
speed_multiplier = 0.5  # For example, slow down by 0.5 times

# Adjust the frame rate to change the speed (slowing down)
new_frame_rate = int(audio.frame_rate * speed_multiplier)
slowed_audio = audio.set_frame_rate(new_frame_rate)

# Play the modified audio
pydub.playback.play(slowed_audio)
