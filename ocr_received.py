import time
import pytesseract
import pyautogui
from PIL import Image
from datetime import datetime

def preprocess_image(image):
    # Convert to grayscale
    gray = image.convert('L')

    # Resize (2x) to improve OCR on small fonts
    resized = gray.resize((gray.width * 2, gray.height * 2))

    # Optional: Binarize image (threshold)
    thresholded = resized.point(lambda x: 0 if x < 160 else 255, mode='1')

    return thresholded

def scan_for_received():
    screenshot = pyautogui.screenshot()
    processed = preprocess_image(screenshot)

    text = pytesseract.image_to_string(processed, config='--psm 6').lower()

    print("🔍 OCR Output:")
    print(text.strip())
    print("-" * 50)

    if "received" in text:
        print("✅ MATCH: 'received' was detected on screen!")
        timestamp = datetime.now().strftime("%H-%M-%S")
        filename = f"match_{timestamp}.png"
        screenshot.save(filename)
        print(f"💾 Saved screenshot: {filename}")
    else:
        print("❌ 'received' not found.")

if __name__ == "__main__":
    print("🕐 Starting in 5 seconds. Open your screenshot or game...")
    time.sleep(5)

    try:
        while True:
            scan_for_received()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[Exit] Script stopped.")
