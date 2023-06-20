import numpy as np
import sounddevice as sd
from matplotlib import pyplot as plt
from scipy.fft import rfft, rfftfreq
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

ON_BUTTON = 5
NEXT_BUTTON = 6
PREV_BUTTON = 12

GPIO.setup(ON_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PREV_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(NEXT_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

SERVO_PINS = [26, 19, 13, 16, 20, 21]

for pin in SERVO_PINS:
    GPIO.setup(pin, GPIO.OUT)

is_listening = False
selected_index = 0

DURATION = 1  # seconds
SAMPLE_RATE = 48000  # Hz
N = int(DURATION * SAMPLE_RATE)
T = 1.0 / SAMPLE_RATE
AMP_THRESHOLD = 1000  # MIC BOVEN KLANKKAST
# AMP_THRESHOLD = 100  # MIC AAN NEK

note_frequencies = [82.41, 110.00, 146.83, 196.00, 246.94, 329.63] # E2, A2, D3, G3, B4, E4

sd.default.samplerate = SAMPLE_RATE
sd.default.channels = 1
sd.default.dtype = "int16"


def sleep(duration, get_now=time.perf_counter):
    now = get_now()
    end = now + duration
    while now < end:
        now = get_now()

def plot_fourier_transform(fourier, freq):
    plt.plot(freq, fourier)
    plt.grid()
    plt.show()

def find_loudest_frequency(fourier, freq):
    for index, value in enumerate(fourier):
        if value > AMP_THRESHOLD:
            return freq[index]
    return 0

def rotate_servo(selected_index, loudest_freq):
    servo_pin = SERVO_PINS[selected_index]
    target_frequency = note_frequencies[selected_index]
    threshold = 2 # in Hz

    frequency_diff = target_frequency - loudest_freq
    if abs(frequency_diff) > threshold:
        servo = GPIO.PWM(servo_pin,50)
        servo.start(0)
        sleep(0.1)

        if frequency_diff > 0:
            if selected_index < 3:
                servo.ChangeDutyCycle(6)
            else:
                servo.ChangeDutyCycle(8)
            
        if frequency_diff < 0:
            if selected_index < 3:
                servo.ChangeDutyCycle(8)
            else:
                servo.ChangeDutyCycle(6)

        sleep(0.1)

        servo.ChangeDutyCycle(0)
        servo.stop()
        return servo

while True:
    try:
        on_button_state = GPIO.input(ON_BUTTON)
        prev_button_state = GPIO.input(PREV_BUTTON)
        next_button_state = GPIO.input(NEXT_BUTTON)

        if on_button_state == False:
            is_listening = not is_listening
            time.sleep(1)
            
        if prev_button_state == False:
            if selected_index == 0:
                selected_index = 5
            else:
                selected_index -= 1
            time.sleep(1)
        if next_button_state == False:
            if selected_index == 5:
                selected_index = 0
            else:
                selected_index += 1
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
            plot_fourier_transform(fourier, freq)

            # Find the loudest frequency in the recording
            loudest_freq = find_loudest_frequency(fourier, freq)

            print("Current frequency:", loudest_freq)

            if loudest_freq > 0:
                servo = rotate_servo(selected_index, loudest_freq)

    except KeyboardInterrupt:
        if servo:
            servo.stop()
        GPIO.cleanup()
        break
    