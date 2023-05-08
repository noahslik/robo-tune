import numpy as np
import sounddevice as sd
from matplotlib import pyplot as plt
from scipy.fft import rfft, rfftfreq

DURATION = 1  # seconds
SAMPLE_RATE = 48000  # Hz
N = DURATION * SAMPLE_RATE
T = 1.0 / SAMPLE_RATE

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


def main():
    while True:
        # Record microphone input
        print("Recording...")
        recording = sd.rec(int(DURATION * SAMPLE_RATE), blocking=True)
        recording = recording[:, 0]

        # Calculate and plot FFT
        fourier = (2.0 / N) * np.abs(rfft(recording)[:N // 2])
        freq = rfftfreq(N, T)[:N // 2]
        plot_fourier_transform(fourier, freq)

        # Find the loudest frequency in the recording
        loudest_freq = freq[np.argmax(fourier)]

        # Find the closest note to the found frequency
        closest_note = None
        closest_note_diff = None
        for key in notes_dict:
            diff = notes_dict[key] - loudest_freq
            if (closest_note_diff is None) or (abs(diff) < abs(closest_note_diff)):
                closest_note = key
                closest_note_diff = diff

        print("Current frequency:", loudest_freq, "Closest note:", closest_note, "Difference:", closest_note_diff)


if __name__ == '__main__':
    main()
