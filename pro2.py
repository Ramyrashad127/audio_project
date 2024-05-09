import tkinter as tk
from tkinter import filedialog, simpledialog
import tkinter.ttk as ttk
import pygame
from pydub import AudioSegment
import tempfile
import os
import threading
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class AudioEditor:
    def __init__(self, master):
        self.master = master
        master.title("Audio Editor")

        # Load the images
        self.play_image = tk.PhotoImage(file="play.png")
        self.stop_image = tk.PhotoImage(file="stop.png")
        self.cut_image = tk.PhotoImage(file="cut.png")

        self.play_image = self.play_image.subsample(10, 10)  # Reduce the size to half
        self.stop_image = self.stop_image.subsample(10, 10)  # Reduce the size to half
        self.cut_image = self.cut_image.subsample(10, 10)  # Reduce the size to half

        # Create the buttons with the images
        self.play_button = tk.Button(master, image=self.play_image, command=self.play_segment)
        self.play_button.grid(row=0, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(master, image=self.stop_image, command=self.stop_audio)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)

        self.cut_button = tk.Button(master, image=self.cut_image, command=self.cut_dialog)
        self.cut_button.grid(row=5, column=1, padx=5, pady=5)

        # Add a progress bar
        style = ttk.Style()
        style.configure("TProgressbar", thickness=25, troughcolor ='#496', background='blue', )
        self.progress = ttk.Progressbar(master, style="TProgressbar", orient="horizontal", length=200, mode="determinate")
        self.progress.grid(row=2, column=2)

        # Add a canvas for the plot
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=master)
        self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=3)
        # Load the merge image
        self.merge_image = tk.PhotoImage(file="merge.png")
        self.merge_image = self.merge_image.subsample(10, 10)  # Reduce the size to half

        # Create the merge button with the image
        self.merge_button = tk.Button(master, image=self.merge_image, command=self.merge_dialog, bg='white', activebackground='black')
        self.merge_button.grid(row=5, column=2, padx=0, pady=5)
        # Create the menu
        self.menu = tk.Menu(master)
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_audio)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        master.config(menu=self.menu)

        self.speed_var = tk.StringVar()
        self.speed_var.set("1x")  # default value
        speed_options = ["1 x", "1.5 x", "2 x"]

        speed_label = tk.Label(master, text="Speed:")
        speed_label.grid(row=2, column=0)
        speed_combobox = ttk.Combobox(master, textvariable=self.speed_var, values=speed_options)
        speed_combobox.grid(row=2, column=1)
        speed_combobox.bind("<<ComboboxSelected>>", self.change_speed)

        frequency_label = tk.Label(master, text="Frequency:")
        frequency_label.grid(row=3, column=0)
        self.change_frequency_scale = tk.Scale(master, from_=1, to=50000, orient=tk.HORIZONTAL, command=self.change_frequency)
        self.change_frequency_scale.grid(row=3, column=1)

        volume_label = tk.Label(master, text="Volume:")
        volume_label.grid(row=4, column=0)
        self.change_volume_scale = tk.Scale(master, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=self.change_volume)
        self.change_volume_scale.grid(row=4, column=1)

        self.audio = None
        self.play_thread = None

    def open_file(self):
        self.audio_path = filedialog.askopenfilename()
        self.audio = self.load(self.audio_path)
        self.plot_waveform(self.audio_path)

    def load(self, input_file):
        return AudioSegment.from_file(input_file)

    def play_segment(self):
        if self.audio:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file.close()
            self.audio.export(temp_file.name, format="mp3")
            self.play_mp3(temp_file.name)
            os.unlink(temp_file.name)

    def play_mp3(self, file_path):
        pygame.init()
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.play_thread = threading.Thread(target=self.wait_for_audio_to_finish)
            self.play_thread.start()
        except pygame.error as e:
            print("Error playing audio:", e)

    def wait_for_audio_to_finish(self):
        while pygame.mixer.music.get_busy():
            # Update the progress bar
            position = pygame.mixer.music.get_pos()  # This is in milliseconds
            duration = len(self.audio)  # This is also in milliseconds
            self.progress["value"] = (position / duration) * 100

            # Update the current position line
            self.current_position_line.set_xdata(position / 1000 * self.audio.frame_rate)
            self.canvas.draw()

            pygame.time.Clock().tick(10)

    def stop_audio(self):
        if self.audio is not None:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            if self.play_thread and self.play_thread.is_alive():
                self.play_thread.join(timeout=1.0)  # Add a timeout
                if self.play_thread.is_alive():  # If the thread is still alive after the timeout
                    print("Failed to stop the play thread.")
                    return  # Return early to avoid hanging the program
            self.progress["value"] = 0
            self.current_position_line.set_xdata(0)
            self.canvas.draw()

    def save_audio(self):
        if self.audio:
            save_path = filedialog.asksaveasfilename(defaultextension=".mp3")
            self.audio.export(save_path, format="mp3")

    def change_speed(self, event=None):
        speed = float(self.speed_var.get().strip('x'))
        if speed != 1:
            self.audio = self.audio.speed(speed)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            self.audio.export(temp.name, format="wav")
            self.plot_waveform(temp.name)  # Update the waveform
            os.unlink(temp.name)  # Delete the temporary file

    def change_frequency(self, frequency):
        self.audio = self.audio.set_frame_rate(int(frequency))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            self.audio.export(temp.name, format="wav")
            self.plot_waveform(temp.name)  # Update the waveform
            os.unlink(temp.name)  # Delete the temporary file

    def change_volume(self, volume):
        self.audio = self.audio + volume

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            self.audio.export(temp.name, format="wav")
            self.plot_waveform(temp.name)  # Update the waveform
            os.unlink(temp.name)  # Delete the temporary file

    def merge_dialog(self):
        audio_path_2 = filedialog.askopenfilename()
        self.merge_audio(audio_path_2)
    
    def merge_audio(self, audio_path_2):
        audio_2 = self.load(audio_path_2)
        self.audio = self.audio + audio_2

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            self.audio.export(temp.name, format="wav")
            self.plot_waveform(temp.name)  # Update the waveform
            os.unlink(temp.name)  # Delete the temporary file

    def convert_to_wav(self, audio_path):
        audio = AudioSegment.from_file(audio_path)
        wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
        audio.export(wav_path, format='wav')
        return wav_path

    def plot_waveform(self, audio_path):
        wav_path = self.convert_to_wav(audio_path)
        sample_rate, data = wavfile.read(wav_path)

        # Create a time axis in milliseconds
        duration = len(data) / sample_rate
        time = np.linspace(0., duration, len(data)) * 1000  # Multiply by 1000 to convert to milliseconds

        self.figure.clear()  # Clear the current plot
        self.plot = self.figure.add_subplot(111)
        self.plot.plot(time, data)  # Plot data against time

        # Add a vertical line for the current position
        self.current_position_line = self.plot.axvline(x=0, color='r')

        self.canvas.draw()

    def cut_dialog(self):
        start_time = simpledialog.askinteger("Input", "Enter start time (in milliseconds):")
        end_time = simpledialog.askinteger("Input", "Enter end time (in milliseconds):")
        self.audio = self.audio[start_time:end_time]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            self.audio.export(temp.name, format="wav")
            self.plot_waveform(temp.name)  # Update the waveform
            os.unlink(temp.name)  # Delete the temporary file

root = tk.Tk()
audio_editor = AudioEditor(root)
root.mainloop()