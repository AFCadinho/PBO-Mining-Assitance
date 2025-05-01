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
from PIL import ImageDraw


GAME_WINDOW_TITLE = "Pokemon Blaze Online"
PAUSE_SOUND = "pause.mp3"
RESUME_SOUND = "unpause.mp3"

mining_active = False
listener_running = True
paused = False
should_stop_after_n_presses = 0
skip_one_counter = 0


def get_game_window_rect():
    hwnd = win32gui.FindWindow(None, GAME_WINDOW_TITLE)
    if hwnd == 0:
        print("❌ Game window not found.")
        return None
    rect = win32gui.GetWindowRect(hwnd)  # (left, top, right, bottom)
    return rect


def get_top_right_text(debug=False):
    screen_width, screen_height = pyautogui.size()

    left_pct = 0.0   # Only grab the far right 20%
    right_pct = 0.00
    top_pct = 0.00
    bottom_pct = 0.55   # Cut off bottom 80%, keep top 20%

    left = int(screen_width * left_pct)
    top = int(screen_height * top_pct)
    right = int(screen_width * (1 - right_pct))
    bottom = int(screen_height * (1 - bottom_pct))

    width = max(1, right - left)
    height = max(1, bottom - top)

    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    gray = screenshot.convert('L')

    if debug:
        debug_img = screenshot.copy()
        draw = ImageDraw.Draw(debug_img)
        draw.rectangle([0, 0, width - 1, height - 1], outline="red", width=3)
        debug_img.show(title="OCR Region (get_top_right_text)")

    text = pytesseract.image_to_string(gray).lower()
    return text


def get_screen_text(debug=False):
    screen_width, screen_height = pyautogui.size()

    left_pct = 0.05
    right_pct = 0.25
    top_pct = 0.10
    bottom_pct = 0.10

    # Convert to absolute pixel values
    left = int(screen_width * left_pct)
    top = int(screen_height * top_pct)
    right = int(screen_width * (1 - right_pct))
    bottom = int(screen_height * (1 - bottom_pct))

    width = right - left
    height = bottom - top

    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    gray = screenshot.convert('L')

    if debug:
        from PIL import ImageDraw
        debug_img = screenshot.copy()
        draw = ImageDraw.Draw(debug_img)
        draw.rectangle([0, 0, width - 1, height - 1], outline="red", width=3)
        debug_img.show(title="OCR Region (get_screen_text)")

    text = pytesseract.image_to_string(gray).lower()
    return text


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
    text = get_top_right_text()
    if any(word in text for word in ["received", "added", "found", "f.", "added", "bag"]):
        print("✅ MATCH: Loot keyword detected!")
        return True
    return False


def detect_question_text():
    text = get_screen_text()

    # Only trigger resume if these specific words are found
    must_include = "question"
    unfinished_words = ["progress", "in progress", "inprogress"]
    trigger_keywords = ["fortune", "adventure", "treasures"]

    if any(keyword in text for keyword in unfinished_words):
        print("[Prompt] ⚡Unfinished Mine detected! Resuming helper...")
        return True

    if must_include in text and any(keyword in text for keyword in trigger_keywords):
        print("[Prompt] ⚡ Entering Miningsite prompt detected! Resuming helper...")
        return True

    return False


def auto_mine():
    global paused, mining_active, should_stop_after_n_presses, skip_one_counter
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
            # Total target cycle time for press + hold
            total_cycle_time = random.uniform(0.1408, 0.1493)

            # Simulated key hold time (spacebar hold)
            hold_time = random.gauss(0.066, 0.008)
            # Clamp to realistic range
            hold_time = max(0.045, min(0.085, hold_time))

            # Remaining time before key press
            delay_before_press = max(0, total_cycle_time - hold_time)
            time.sleep(delay_before_press)

            if mining_active and not paused:
                skip_press = random.random() <= 0.03
                if not skip_press:
                    keyboard_controller.press(Key.space)
                    time.sleep(hold_time)
                    keyboard_controller.release(Key.space)
                    print(
                        f"[Mining] Pressed SPACE (held for {hold_time*1000:.0f}ms) after {delay_before_press:.2f}s"
                    )
                else:
                    print("[Mining] (Skipped) acted distracted")

                if skip_one_counter >= 4:
                    result = detect_mining_result()
                else:
                    result = False
                    skip_one_counter += 1

                if result:
                    print("[Drop] Item or money detected. Stopping mining.\n")

                    extra_presses = random.choice([0, 1, 2, 0, 0])
                    for i in range(extra_presses):
                        tiny_delay = random.uniform(0.05, 0.18)
                        time.sleep(tiny_delay)
                        keyboard_controller.press(Key.space)
                        extra_hold = random.gauss(0.04, 0.007)
                        extra_hold = max(0.025, min(0.055, extra_hold))
                        time.sleep(extra_hold)
                        keyboard_controller.release(Key.space)
                        print(
                            f"[Mining] (Extra tap {i+1}/{extra_presses}) after result detection")

                    mining_active = False
                    threading.Thread(target=playsound, args=(
                        "cash_sound.mp3",), daemon=True).start()
                    continue

                if not skip_press and random.random() < 0.015:
                    tiny_delay = random.uniform(0.05, 0.12)
                    time.sleep(tiny_delay)
                    keyboard_controller.press(Key.space)
                    double_hold = random.gauss(0.04, 0.007)
                    double_hold = max(0.025, min(0.055, double_hold))
                    time.sleep(double_hold)
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
    global mining_active, paused, should_stop_after_n_presses, skip_one_counter

    if not is_game_focused():
        return

    try:
        if key == Key.space:
            if not paused and not mining_active:
                print("[Trigger] SPACE pressed. Starting auto-mining.")
                mining_active = True
                skip_one_counter = 0

        elif key.char.lower() in ['w', 'a', 's', 'd']:
            if mining_active:
                print("[Movement] Movement detected. Stopping mining immediately.")
                mining_active = False

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
    # get_screen_text(debug=True)
    # get_top_right_text(debug=True)
    main()
