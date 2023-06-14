import numpy as np
import sounddevice as sd
from matplotlib import pyplot as plt
from scipy.fft import rfft, rfftfreq
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

ON_BUTTON = 13
PREV_BUTTON = 19
NEXT_BUTTON = 26

GPIO.setup(ON_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PREV_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(NEXT_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

SERVO_PINS = [1, 2, 3, 4, 5, 6]

is_listening = False
selected_index = 0

DURATION = 1  # seconds
SAMPLE_RATE = 48000  # Hz
N = int(DURATION * SAMPLE_RATE)
T = 1.0 / SAMPLE_RATE
# FREQ_THRESHOLD = 1000  # MIC BOVEN KLANKKAST
FREQ_THRESHOLD = 100  # MIC AAN NEK

notes_dict = {
    "E2": 82.41,
    "A2": 110.00,
    "D3": 146.83,
    "G3": 196.00,
    "B3": 246.94,
    "E4": 329.63
}

sd.default.samplerate = SAMPLE_RATE
sd.default.channels = 1
sd.default.dtype = "int16"


def plot_fourier_transform(fourier, freq):
    plt.plot(freq, fourier)
    plt.grid()
    plt.show()


def find_closest_note(loudest_freq):
    closest_note = None
    closest_note_diff = None
    for key in notes_dict:
        diff = notes_dict[key] - loudest_freq
        if (closest_note_diff is None) or (abs(diff) < abs(closest_note_diff)):
            closest_note = key
            closest_note_diff = diff
    return closest_note, closest_note_diff


def find_loudest_frequency(fourier, freq):
    for index, value in enumerate(fourier):
        if value > FREQ_THRESHOLD:
            return freq[index]
    return 0


while True:
    on_button_state = GPIO.input(ON_BUTTON)
    prev_button_state = GPIO.input(PREV_BUTTON)
    next_button_state = GPIO.input(NEXT_BUTTON)
    
    if on_button_state == False:
        is_listening = not is_listening
        time.sleep(1)
    if prev_button_state == False:
        if selected_index < 5:
            selected_index += 1
        time.sleep(1)
    if next_button_state == False:
        if selected_index > 0:
            selected_index -= 1
        time.sleep(1)

    print(is_listening, selected_index)

    if is_listening:
        # Record microphone input
        recording = sd.rec(int(DURATION * SAMPLE_RATE), blocking=True)
        recording = recording[:, 0]

        # Calculate and plot FFT
        fourier = (2.0 / N) * np.abs(rfft(recording)[:N // 2])
        for i in range(70):
            fourier[i] = 0
        freq = rfftfreq(N, T)[:N // 2]
        # plot_fourier_transform(fourier, freq)

        # Find the loudest frequency in the recording
        loudest_freq = find_loudest_frequency(fourier, freq)

        # Find the closest note to the found frequency
        closest_note, closest_note_diff = find_closest_note(loudest_freq)

        print("Current frequency:", loudest_freq, "|",
            "Closest note:", closest_note, "|",
            "Difference:", closest_note_diff)
