import pygame
import pytchat
import threading
import queue
import random
import time
import sys
import numpy as np


VIDEO_ID = "ufkCHo9GA-g"

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650
FPS = 60


# COLOR_PALETTE
COLOR_BG = (15, 17, 26)
COLOR_PANEL = (25, 28, 44)
COLOR_BORDER =(45, 50, 75)
COLOR_PLAYER = (0, 240, 180)

# GLOWING_CYAN
COLOR_COIN = (255, 205, 40)

# BRIGHT_GOLD
COLOR_TEXT = (240, 240, 250)
COLOR_MUTED = (130, 135, 160)
COLOR_ACENT = (255, 85, 115)


def create_beep_sound(freq=600, duration_ms=80):
    sample_rate = 44100
    n_samples = int(sample_rate + (duration_ms / 1000.0))

    t = np.linspace(0, duration_ms / 1000.0, n_samples, False)
    wave = 0.3 * np.sin( 2*np.pi*freq*t)
    decay = np.linspace(10, 0.0, n_samples)

    wave = (wave * decay * 32767).astype(np.int16)

    stereo_wave = np.column_stack((wave, wave))
    return pygame.sndarray.make_sound(stereo_wave)



command_queue = queue.Queue()

def youtube_chat_worker(vid_id):
    if vid_id == "YOU_VIDEO_ID":
        print("[!] Warning: Using placeholder VIDEO_ID. RUNNING in Local Test Mode.")
        return

    while True:
        try:
            chat = pytchat.create(video_id=vid_id)
            print(f"[+] Connected to youtube stream: {vid_id}")

            while chat.is_alive():
                for c in chat.get().sync_items:
                    msg = c.message.strip().lower()
                    author = c.author.name

                    cmd = msg if not msg.startswith("!") else msg[1:]

                    if cmd in ["left", "right", "up", "down", "jump", "reset"]:

                        command_queue.put({"cmd":cmd, "user":author})
                time.sleep(2)

        except Exception as err:
            print(f"[-]Chat connection dropped : {err}, Reconnecting in 5 seconds....")

            time.sleep(5)


# def main():
#     pygame.init()
#     pygame.mixer.init(frequency=44100, size=-16, channels=2)
#     screen = pygame.display.set_mode((SCREEN_HEIGHT, SCREEN_HEIGHT))




