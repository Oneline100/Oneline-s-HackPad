import board
import displayio
import terminalio
from adafruit_display_text import label

from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC
from kmk.modules.layers import Layers
from kmk.modules.macros import Macros, Press, Release, Tap
from kmk.extensions.rgb import RGB

# =====================================================
# Keyboard core
# =====================================================
keyboard = KMKKeyboard()

# =====================================================
# KMK modules
# =====================================================
layers = Layers()
macros = Macros()
keyboard.modules.extend([layers, macros])

# =====================================================
# Switch GPIOs (active-low)
# =====================================================
PINS = (
    board.GP26,  # SW1
    board.GP27,  # SW2
    board.GP28,  # SW3
    board.GP29,  # SW4
    board.GP6,   # SW5
    board.GP7,   # SW6
)

keyboard.matrix = KeysScanner(
    pins=PINS,
    value_when_pressed=False,
)

# =====================================================
# RGB (SK6812 / NeoPixel)
# =====================================================
rgb = RGB(
    pixel_pin=board.GP3,
    num_pixels=2,
    hue_default=180,
    sat_default=255,
    val_default=80,
    animation_mode=RGB.AnimationModes.BREATHING,
)
keyboard.extensions.append(rgb)

# =====================================================
# OLED + Image
# =====================================================
displayio.release_displays()

i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

display = displayio.Display(
    display_bus,
    width=128,
    height=64,
    rotation=0,
)

root = displayio.Group()
display.root_group = root

# ---- Bitmap image ----
bitmap = displayio.OnDiskBitmap("/images/logo.bmp")
tile_grid = displayio.TileGrid(
    bitmap,
    pixel_shader=bitmap.pixel_shader,
    x=0,
    y=0,
)
root.append(tile_grid)

# ---- Layer indicator ----
layer_label = label.Label(
    terminalio.FONT,
    text="Layer 0",
    color=0xFFFFFF,
    x=0,
    y=48,
)
root.append(layer_label)

# ---- Key feedback label ----
key_label = label.Label(
    terminalio.FONT,
    text="",
    color=0xFFFFFF,
    x=0,
    y=60,
)
root.append(key_label)

# =====================================================
# OLED update helpers
# =====================================================
def update_layer_text(keyboard):
    layer_label.text = f"Layer {keyboard.active_layers[0]}"

def key_to_text(key):
    if key is None:
        return ""
    if hasattr(key, "name"):
        return key.name
    return key.__class__.__name__

last_keys = set()

def key_feedback(keyboard):
    global last_keys

    current_keys = set(keyboard.keys_pressed)
    new_keys = current_keys - last_keys

    if new_keys:
        key_index = next(iter(new_keys))
        layer = keyboard.active_layers[0]
        key = keyboard.keymap[layer][key_index]
        key_label.text = key_to_text(key)

    last_keys = current_keys

def after_scan(keyboard):
    update_layer_text(keyboard)
    key_feedback(keyboard)

keyboard.after_matrix_scan = after_scan

# =====================================================
# Keymap
# =====================================================
keyboard.keymap = [
    # -------- Layer 0 --------
    [
        KC.A,
        KC.B,
        KC.C,
        KC.D,
        KC.MACRO("Hello world!"),
        KC.TO(1),
    ],

    # -------- Layer 1 --------
    [
        KC.MEDIA_PLAY_PAUSE,
        KC.MEDIA_NEXT_TRACK,
        KC.MEDIA_PREV_TRACK,
        KC.AUDIO_VOL_UP,
        KC.AUDIO_VOL_DOWN,
        KC.TO(0),
    ],
]

# =====================================================
# Start KMK
# =====================================================
if __name__ == "__main__":
    keyboard.go()
