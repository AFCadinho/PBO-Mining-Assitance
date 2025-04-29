import time
import random
import threading
import pytesseract
import pyautogui
import ctypes
from pynput import keyboard
from pynput.keyboard import Key, Controller
from playsound import playsound

GAME_WINDOW_TITLE = "Pokemon Blaze Online"
PAUSE_SOUND = "pause.mp3"
RESUME_SOUND = "unpause.mp3"

mining_active = False
listener_running = True
paused = False
should_stop_after_n_presses = 0


def get_screen_text(crop_ratio=0.85):
    screen_width, screen_height = pyautogui.size()
    screenshot = pyautogui.screenshot()
    cropped = screenshot.crop(
        (0, 0, int(screen_width * crop_ratio), int(screen_height * crop_ratio)))
    return pytesseract.image_to_string(cropped.convert('L')).lower()


def is_game_focused():
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    window_title = buff.value
    return GAME_WINDOW_TITLE.lower() in window_title.lower()


def detect_question_text():
    text = get_screen_text()

    # Only trigger resume if these specific words are found
    must_include = "question"
    unfinished_word = "progress"
    trigger_keywords = ["fortune", "adventure", "treasures"]

    if unfinished_word in text:
        print("[Prompt] ⚡Unfinished Mine detected! Resuming helper...")
        return True

    if must_include in text and any(keyword in text for keyword in trigger_keywords):
        print("[Prompt] ⚡ Entering Miningsite prompt detected! Resuming helper...")
        return True

    return False


def auto_mine():
    global paused, mining_active, should_stop_after_n_presses
    keyboard_controller = Controller()
    was_focused = True
    last_ocr_check = time.monotonic()

    while listener_running:
        game_focused = is_game_focused()

        if not game_focused:
            if was_focused:
                print("[Focus] Game not active. Waiting...")
                was_focused = False
            time.sleep(0.5)
            continue
        else:
            if not was_focused:
                print("[Focus] Game focused again. Resuming helper...")
                was_focused = True

        if paused:
            now = time.monotonic()
            if now - last_ocr_check >= 1.0:
                last_ocr_check = now
                found = detect_question_text()
                if found:

                    paused = False
                    playsound(RESUME_SOUND)
            time.sleep(0.1)
            continue

        if mining_active:
            # Delay between mining presses
            delay = random.uniform(0.25, 0.5)  # (was 0.2-0.4)
            waited = 0
            chunk = 0.01
            while waited < delay:
                if not mining_active or paused:
                    break
                time.sleep(chunk)
                waited += chunk

            if mining_active and not paused:
                # ✨ New: sometimes skip pressing SPACE
                if random.random() > 0.03:  # 97% chance to press
                    keyboard_controller.press(Key.space)
                    hold_time = random.gauss(0.05, 0.015)
                    hold_time = max(0.03, min(0.08, hold_time))
                    time.sleep(hold_time)
                    keyboard_controller.release(Key.space)
                    print(
                        f"[Mining] Pressed SPACE (held for {hold_time*1000:.0f}ms) after {delay:.2f}s")

                    # ✨ New: very rare accidental double-press
                    if random.random() < 0.015:  # about 1.5% chance
                        tiny_delay = random.uniform(
                            0.05, 0.12)  # small hesitation
                        time.sleep(tiny_delay)
                        keyboard_controller.press(Key.space)
                        # second press even quicker
                        hold_time = random.gauss(0.045, 0.01)
                        hold_time = max(0.02, min(0.06, hold_time))
                        time.sleep(hold_time)
                        keyboard_controller.release(Key.space)
                        print(
                            f"[Mining] (Accidental double press) second tap after {tiny_delay:.2f}s")
                else:
                    print("[Mining] (Skipped) acted distracted")

                if should_stop_after_n_presses > 0:
                    should_stop_after_n_presses -= 1
                    if should_stop_after_n_presses == 0:
                        print(
                            "[Movement] Stopping mining naturally after extra presses.")
                        mining_active = False
                    else:
                        time.sleep(0.1)


def detect_progress_only():
    return "progress" in get_screen_text()


def on_press(key):
    global mining_active, paused, should_stop_after_n_presses

    if not is_game_focused():
        return

    try:
        if key == Key.space:
            if not paused and not mining_active:
                print("[Trigger] SPACE pressed. Starting auto-mining.")
                mining_active = True

        elif key.char.lower() in ['w', 'a', 's', 'd']:
            if mining_active and should_stop_after_n_presses == 0:
                should_stop_after_n_presses = random.randint(1, 3)
                print(
                    f"[Movement] Movement detected. Will stop mining after {should_stop_after_n_presses} more presses.")
                # ✨ New: small human delay after movement
                time.sleep(random.uniform(0.05, 0.2))

    except AttributeError:
        if key == Key.esc:

            if detect_progress_only():
                print("[Escape] Mining tool closed. No pause triggered.")
                return

            if not paused:
                print("[Pause] Helper paused. Waiting for miner prompt to resume.")
                mining_active = False
                paused = True
                playsound(PAUSE_SOUND)
            else:
                print("[Already Paused] Helper already paused.")


def main():
    print("🛠 Mining Helper Started")
    print("• SPACE = start auto-mining")
    print("• W/A/S/D = stop mining after a few presses")
    print("• ESC = pause/resume (waiting for 'Question' or 'Progress')")
    print("• Ctrl+C = exit completely\n")

    threading.Thread(target=auto_mine, daemon=True).start()
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[Exit] Ctrl+C pressed. Exiting...")


if __name__ == "__main__":
    main()
