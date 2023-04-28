import numpy as np
import sounddevice as sd
from matplotlib import pyplot as plt
from scipy.fft import rfft, rfftfreq

DURATION = 3  # seconds
SAMPLE_RATE = 48000  # Hz
N = DURATION * SAMPLE_RATE
T = 1.0 / SAMPLE_RATE

sd.default.samplerate = SAMPLE_RATE
sd.default.channels = 1
sd.default.dtype = "int16"


def plot_fourier_transform(fourier, freq):
    plt.plot(freq, fourier)
    plt.grid()
    plt.show()


def main():
    # Record microphone input
    print("Recording...")
    recording = sd.rec(int(DURATION * SAMPLE_RATE), blocking=True)
    recording = recording[:, 0]

    # Calculate and plot FFT
    fourier = (2.0 / N) * np.abs(rfft(recording)[:N // 2])
    freq = rfftfreq(N, T)[:N // 2]
    plot_fourier_transform(fourier, freq)

    # Find and print the loudest frequency in the recording
    loudest_freq = freq[np.argmax(fourier)]
    print(loudest_freq)


if __name__ == '__main__':
    main()
