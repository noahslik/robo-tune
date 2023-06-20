import numpy as np
import sounddevice as sd
from matplotlib import pyplot as plt
from scipy.fft import rfft, rfftfreq
import RPi.GPIO as GPIO
import time
from subprocess import Popen, PIPE
from time import sleep, perf_counter
from datetime import datetime
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

GPIO.setmode(GPIO.BCM)

# LCD SETUP
lcd_columns = 16
lcd_rows = 2

lcd_rs = digitalio.DigitalInOut(board.D22)
lcd_en = digitalio.DigitalInOut(board.D17)
lcd_d4 = digitalio.DigitalInOut(board.D25)
lcd_d5 = digitalio.DigitalInOut(board.D24)
lcd_d6 = digitalio.DigitalInOut(board.D23)
lcd_d7 = digitalio.DigitalInOut(board.D18)

lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                      lcd_d7, lcd_columns, lcd_rows)

message_1 = "Press Start\n"
message_2 = ""

# BUTTON SETUP
ON_BUTTON = 5
NEXT_BUTTON = 12
PREV_BUTTON = 6

GPIO.setup(ON_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PREV_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(NEXT_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# BUTTON STATES
is_listening = False
selected_index = 0

# SERVO SETUP
SERVO_PINS = [26, 19, 13, 16, 20, 21]
for pin in SERVO_PINS:
    GPIO.setup(pin, GPIO.OUT)

# AUDIO RECORDING SETTINGS
DURATION = 1  # seconds
SAMPLE_RATE = 48000  # Hz
sd.default.samplerate = SAMPLE_RATE
sd.default.channels = 1
sd.default.dtype = "int16"

# FOURIER SETTINGS
N = int(DURATION * SAMPLE_RATE)
T = 1.0 / SAMPLE_RATE
AMP_THRESHOLD = 1000  # MIC BOVEN KLANKKAST
# AMP_THRESHOLD = 100  # MIC AAN NEK

note_frequencies = [82.41, 110.00, 146.83, 196.00, 246.94, 329.63] # E2, A2, D3, G3, B4, E4
tuned_strings = [False, False, False, False, False, False]

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

def on_btn_pressed(channel):
    global is_listening
    is_listening = not is_listening

    clear_lcd()
    if is_listening:
        message_1 = "Play string " + str(selected_index + 1)
    else:
        message_1 = "Press Start"

    write_to_lcd(message_1, message_2)

def next_btn_pressed(channel):
    print("next pressed")
    global selected_index

    if selected_index == 5:
        selected_index = 0
    else:
        selected_index += 1
    time.sleep(1)

    message_1 = "Play string " + str(selected_index + 1)
    write_to_lcd(message_1, message_2)

def prev_btn_pressed(channel):
    global selected_index

    if selected_index == 0:
        selected_index = 5
    else:
        selected_index -= 1
    time.sleep(1)

    message_1 = "Play string " + str(selected_index + 1)
    write_to_lcd(message_1, message_2)


def clear_lcd():
    lcd.message = "                \n                "

def write_to_lcd(message_1, message_2):
    lcd.message = message_1 + message_2

def main():
    GPIO.add_event_detect(ON_BUTTON, GPIO.RISING, callback=on_btn_pressed, bouncetime=1000)
    GPIO.add_event_detect(NEXT_BUTTON, GPIO.RISING, callback=next_btn_pressed, bouncetime=1000)
    GPIO.add_event_detect(PREV_BUTTON, GPIO.RISING, callback=prev_btn_pressed, bouncetime=1000)
    write_to_lcd(message_1, message_2)

    while True:
        try:
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

if __name__ == "__main__":
    main()
