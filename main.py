import numpy as np
import sounddevice as sd
from matplotlib import pyplot as plt
from scipy.fft import rfft, rfftfreq
import RPi.GPIO as GPIO
import time
import pigpio

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
        if value > FREQ_THRESHOLD:
            return freq[index]
    return 0

def rotate_servo(selected_index, loudest_freq):
    servo_pin = SERVO_PINS[selected_index]
    target_frequency = note_frequencies[selected_index]
    threshold = 5 # in Hz

    frequency_diff = target_frequency - loudest_freq
    if abs(frequency_diff) > threshold:

        pwm = pigpio.pi()
        pwm.set_mode(servo_pin, pigpio.OUTPUT)
        pwm.set_PWM_frequency(servo_pin, 50)

        if frequency_diff > 0:
            
            pwm.set_servo_pulsewidth(servo_pin, 1250)
            sleep(0.5)
            pwm.set_PWM_dutycycle(servo_pin, 0)
            pwm.set_PWM_frequency(servo_pin, 0)

        if frequency_diff < 0:
            
            pwm.set_servo_pulsewidth(servo_pin, 1750) 
            sleep(0.5)
            pwm.set_PWM_dutycycle(servo_pin, 0)
            pwm.set_PWM_frequency(servo_pin, 0)

        pwm.set_PWM_dutycycle(servo_pin, 0)
        pwm.set_PWM_frequency(servo_pin, 0)
        pwm.stop()

    return

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
        if selected_index == 5:
            selected_index = 0
        time.sleep(1)
    if next_button_state == False:
        if selected_index > 0:
            selected_index -= 1
        if selected_index == 0:
            selected_index = 5
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
        
        if loudest_freq > 0:
            rotate_servo(selected_index)