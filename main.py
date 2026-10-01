import pygame
import pytchat
import threading
import queue
import random
import time
import sys
import numpy as np


VIDEO_ID = "Maw-LKwhr2c"

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650
FPS = 60


# COLOR_PALETTE
COLOR_BG = (15, 17, 26)
COLOR_PANEL = (25, 28, 44)
COLOR_BORDER =(45, 50, 75)
COLOR_PLAYER = (0, 240, 180)

import math
import queue
import random
import threading
import time

import pygame

try:
    import pytchat
except ImportError:
    pytchat = None


VIDEO_ID = "ufkCHo9GA-g"
WIDTH, HEIGHT, FPS = 900, 650, 60
COMMANDS = {"left", "right", "up", "down", "jump", "reset"}
BG = (15, 17, 26)
PANEL = (25, 28, 44)
BORDER = (45, 50, 75)
TEXT = (240, 240, 250)
MUTED = (130, 135, 160)
PLAYER = (0, 240, 180)
COIN = (255, 205, 40)
ACCENT = (255, 85, 115)


def chat_worker(video_id, output, stop):
    if pytchat is None:
        output.put(("status", "pytchat not installed — LOCAL PLAY"))
        return
    while not stop.is_set():
        try:
            chat = pytchat.create(video_id=video_id)
            output.put(("status", "CHAT CONNECTED"))
            while chat.is_alive() and not stop.is_set():
                for item in chat.get().sync_items:
                    command = item.message.strip().lower().lstrip("!")
                    if command in COMMANDS:
                        output.put(("command", command, item.author.name))
                stop.wait(0.5)
        except Exception as error:
            output.put(("status", "CHAT RECONNECTING"))
            print(f"YouTube chat error: {error}")
            stop.wait(5)


class CoinArena:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("CHAT PLAYS — COIN ARENA")
        self.clock = pygame.time.Clock()
        self.small = pygame.font.SysFont("consolas", 14, bold=True)
        self.medium = pygame.font.SysFont("consolas", 18, bold=True)
        self.large = pygame.font.SysFont("consolas", 30, bold=True)
        self.arena = pygame.Rect(30, 112, 600, 500)
        self.player = pygame.Rect(0, 0, 34, 34)
        self.player.center = self.arena.center
        self.coin = pygame.Rect(0, 0, 18, 18)
        self.move_sound = self.make_sound(350, 45)
        self.coin_sound = self.make_sound(880, 120)
        self.place_coin()

        self.inbox = queue.Queue()
        self.stop = threading.Event()
        self.worker = threading.Thread(target=chat_worker,
                                       args=(VIDEO_ID, self.inbox, self.stop), daemon=True)
        self.worker.start()
        self.status = "CONNECTING"
        self.score = self.actions = 0
        self.last_user, self.last_command = "Waiting for chat", "—"
        self.activity = []
        self.user_scores = {}
        self.running = True

    @staticmethod
    def make_sound(frequency, milliseconds):
        if not pygame.mixer.get_init():
            return None
        try:
            rate = pygame.mixer.get_init()[0]
            count = int(rate * milliseconds / 1000)
            samples = [int(7000 * (1 - i / count) * math.sin(2 * math.pi * frequency * i / rate))
                       for i in range(count)]
            import array
            data = array.array("h", (sample for value in samples for sample in (value, value)))
            return pygame.sndarray.make_sound(data)
        except (pygame.error, ValueError):
            return None

    def place_coin(self):
        self.coin.center = (random.randint(self.arena.left + 25, self.arena.right - 25),
                            random.randint(self.arena.top + 25, self.arena.bottom - 25))

    def enqueue(self, command, user="HOST"):
        self.inbox.put(("command", command, user))

    def command(self, command, user):
        self.actions += 1
        self.last_user, self.last_command = user, command.upper()
        self.activity.insert(0, (user, command.upper()))
        del self.activity[6:]
        delta = {"left": (-34, 0), "right": (34, 0), "up": (0, -34),
                 "jump": (0, -34), "down": (0, 34)}
        if command == "reset":
            self.player.center = self.arena.center
        elif command in delta:
            dx, dy = delta[command]
            self.player.move_ip(dx, dy)
        self.player.clamp_ip(self.arena.inflate(-8, -8))
        if self.move_sound:
            self.move_sound.play()
        if self.player.colliderect(self.coin):
            self.score += 1
            self.user_scores[user] = self.user_scores.get(user, 0) + 1
            self.place_coin()
            if self.coin_sound:
                self.coin_sound.play()

    def events(self):
        key_commands = {pygame.K_LEFT: "left", pygame.K_RIGHT: "right",
                        pygame.K_UP: "up", pygame.K_DOWN: "down",
                        pygame.K_SPACE: "jump", pygame.K_r: "reset"}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key in key_commands:
                    self.enqueue(key_commands[event.key])

    def process_inbox(self):
        for _ in range(40):
            try:
                message = self.inbox.get_nowait()
            except queue.Empty:
                break
            if message[0] == "status":
                self.status = message[1]
            else:
                self.command(message[1], message[2])

    def label(self, value, position, color=TEXT, font=None):
        self.screen.blit((font or self.small).render(str(value), True, color), position)

    def panel(self, rect):
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=10)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=10)

    def draw(self):
        self.screen.fill(BG)
        self.label("CHAT PLAYS", (30, 23), TEXT, self.large)
        self.label("COIN ARENA  /  LIVE", (33, 65), MUTED)
        self.panel(self.arena)
        for x in range(self.arena.left + 30, self.arena.right, 30):
            pygame.draw.line(self.screen, (31, 35, 52), (x, self.arena.top + 1), (x, self.arena.bottom - 1))
        for y in range(self.arena.top + 30, self.arena.bottom, 30):
            pygame.draw.line(self.screen, (31, 35, 52), (self.arena.left + 1, y), (self.arena.right - 1, y))
        pygame.draw.circle(self.screen, (95, 72, 30), self.coin.center, 16 + (pygame.time.get_ticks() // 180) % 3)
        pygame.draw.circle(self.screen, COIN, self.coin.center, 10)
        pygame.draw.circle(self.screen, (255, 240, 170), self.coin.center, 4)
        pygame.draw.rect(self.screen, PLAYER, self.player, border_radius=9)
        pygame.draw.rect(self.screen, (180, 255, 235), self.player.inflate(-14, -14), border_radius=5)
        self.label("ARROWS / CHAT: MOVE     SPACE: JUMP     R: RESET", (30, 620), MUTED)
        self.sidebar()
        pygame.display.flip()

    def sidebar(self):
        x, width = 655, 215
        self.panel(pygame.Rect(x, 25, width, 104))
        self.label("COINS", (x + 16, 40), MUTED)
        self.label(f"{self.score:03d}", (x + 14, 59), COIN, self.large)
        self.label(f"{self.actions} moves", (x + 112, 76), MUTED)

        status_color = PLAYER if "CONNECTED" in self.status else ACCENT
        if "LOCAL" in self.status or "not installed" in self.status:
            status_color = (75, 190, 255)
        pygame.draw.circle(self.screen, status_color, (x + 18, 155), 5)
        self.label(self.status[:25], (x + 31, 148), status_color)

        self.panel(pygame.Rect(x, 175, width, 112))
        self.label("LAST COMMAND", (x + 15, 190), MUTED)
        self.label(self.last_command, (x + 15, 212), TEXT, self.medium)
        self.label("BY", (x + 15, 249), MUTED)
        self.label(self.last_user[:20], (x + 43, 247), (75, 190, 255))

        self.panel(pygame.Rect(x, 300, width, 185))
        self.label("RECENT MOVES", (x + 15, 315), MUTED)
        if not self.activity:
            self.label("Waiting for commands...", (x + 15, 346), MUTED)
        for index, (user, command) in enumerate(self.activity):
            y = 346 + index * 22
            self.label(command, (x + 15, y), PLAYER)
            self.label(user[:14], (x + 91, y), TEXT)

        self.panel(pygame.Rect(x, 498, width, 114))
        self.label("TOP COIN COLLECTORS", (x + 15, 512), MUTED)
        leaders = sorted(self.user_scores.items(), key=lambda pair: (-pair[1], pair[0]))[:3]
        if not leaders:
            self.label("Collect the gold coin!", (x + 15, 544), MUTED)
        for rank, (user, score) in enumerate(leaders):
            y = 541 + rank * 21
            self.label(f"{rank + 1}.", (x + 15, y), COIN)
            self.label(user[:13], (x + 39, y), TEXT)
            self.label(score, (x + 185, y), COIN)

    def run(self):
        try:
            while self.running:
                self.events()
                self.process_inbox()
                self.draw()
                self.clock.tick(FPS)
        finally:
            self.stop.set()
            pygame.quit()


def main():
    CoinArena().run()


if __name__ == "__main__":
    main()





