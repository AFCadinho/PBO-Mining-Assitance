import time
from pynput import keyboard

print("⏱ Hold and release SPACE to measure speed and hold time.")
print("✅ Press ESC to stop and see the results.\n")

press_times = []
release_times = []

pressed_at = None

def on_press(key):
    global pressed_at
    if key == keyboard.Key.space:
        pressed_at = time.time()

def on_release(key):
    global pressed_at

    if key == keyboard.Key.esc:
        if len(press_times) < 2:
            print("⚠️ Not enough presses recorded.")
        else:
            intervals = [t2 - t1 for t1, t2 in zip(press_times[:-1], press_times[1:])]
            holds = [r - p for p, r in zip(press_times, release_times)]

            avg_interval = sum(intervals) / len(intervals)
            avg_hold = sum(holds) / len(holds)

            print(f"\n🔎 Measured {len(press_times)} presses.")
            print(f"📉 Average interval: {avg_interval:.3f} seconds")
            print(f"⏳ Average hold time: {avg_hold:.3f} seconds")
            print(f"⚡ Speed: {1 / avg_interval:.2f} presses per second")

        return False

    if key == keyboard.Key.space and pressed_at is not None:
        now = time.time()
        press_times.append(pressed_at)
        release_times.append(now)
        hold_time = now - pressed_at
        print(f"[{len(press_times)}] Held for {hold_time:.3f} seconds")
        pressed_at = None

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
