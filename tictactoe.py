import time
import random
import threading
import pytesseract
import pyautogui
import ctypes
import win32gui
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


def get_game_window_rect():
    hwnd = win32gui.FindWindow(None, GAME_WINDOW_TITLE)
    if hwnd == 0:
        print("❌ Game window not found.")
        return None
    rect = win32gui.GetWindowRect(hwnd)  # (left, top, right, bottom)
    return rect


def get_top_right_text():
    screen_width, screen_height = pyautogui.size()
    screenshot = pyautogui.screenshot()

    # Focus only on top-right area (e.g., 400x150 px)
    left = screen_width - 400
    top = 0
    right = screen_width
    bottom = 150
    cropped = screenshot.crop((left, top, right, bottom))

    gray = cropped.convert('L')
    thresholded = gray.point(lambda x: 0 if x < 180 else 255, mode='1')

    text = pytesseract.image_to_string(thresholded).lower()
    print("[OCR Debug] Top-Right Text:", text)

    return text


def get_screen_text():
    screen_width, screen_height = pyautogui.size()
    screenshot = pyautogui.screenshot()

    # Only exclude bottom 200px (full width retained)
    cropped = screenshot.crop((0, 0, screen_width, screen_height - 200))
    return pytesseract.image_to_string(cropped.convert('L')).lower()


def is_game_focused():
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    window_title = buff.value
    return GAME_WINDOW_TITLE.lower() in window_title.lower()


def detect_added_text():
    return "added" in get_top_right_text()


def detect_received_text():
    return "received" in get_top_right_text()


def detect_mining_result():

    rect = get_game_window_rect()
    if rect is None:
        print("❌ Cannot detect mining result without game window.")
        return False

    left, top, right, bottom = rect
    width = right - left
    height = bottom - top

    # Crop to top 25% of game window
    crop_height = int(height * 0.25)

    screenshot = pyautogui.screenshot(region=(left, top, width, crop_height))

    # Preprocess
    gray = screenshot.convert('L')
    resized = gray.resize((gray.width * 2, gray.height * 2))
    thresholded = resized.point(lambda x: 0 if x < 160 else 255, mode='1')

    # OCR
    text = pytesseract.image_to_string(thresholded, config='--psm 6').lower()

    # Match
    if any(word in text for word in ["received", "added", "found"]):
        print("✅ MATCH: Loot keyword detected!")
        return True

    return False


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
            delay = random.uniform(0.14, 0.17)  # ~5.9 to 7.1 presses/sec
            waited = 0
            chunk = 0.01
            while waited < delay:
                if not mining_active or paused:
                    break
                time.sleep(chunk)
                waited += chunk

            if mining_active and not paused:

                skip_press = random.random() <= 0.03
                if not skip_press:
                    keyboard_controller.press(Key.space)
                    hold_time = random.gauss(0.066, 0.008)  # avg: 0.066s, std dev: 0.008
                    hold_time = max(0.045, min(0.085, hold_time))  # realistic range
                    time.sleep(hold_time)
                    keyboard_controller.release(Key.space)
                    print(
                        f"[Mining] Pressed SPACE (held for {hold_time*1000:.0f}ms) after {delay:.2f}s")
                else:
                    print("[Mining] (Skipped) acted distracted")

                result = detect_mining_result()
                if result:
                    print("[Drop] Item or money detected. Stopping mining.\n")
                    mining_active = False
                    continue

                # ✨ Rare accidental double press
                if not skip_press and random.random() < 0.015:
                    tiny_delay = random.uniform(0.05, 0.12)
                    time.sleep(tiny_delay)
                    keyboard_controller.press(Key.space)
                    hold_time = random.gauss(0.04, 0.007)
                    hold_time = max(0.025, min(0.055, hold_time))

                    time.sleep(hold_time)
                    keyboard_controller.release(Key.space)
                    print(
                        f"[Mining] (Double tap) second tap after {tiny_delay:.2f}s")

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