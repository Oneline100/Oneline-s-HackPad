import board
import busio
import displayio
import terminalio
import time
import adafruit_displayio_ssd1306
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.line import Line

from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC, make_key
from kmk.modules.layers import Layers
from kmk.extensions.media_keys import MediaKeys
from kmk.modules.macros import Macros, Press, Release, Tap, Delay

# =========================================================
# CONFIGURATION
# =========================================================

PINS         = (board.D7, board.D8, board.D9, board.D10, board.D0, board.D6)
DISPLAY_W    = 128
DISPLAY_H    = 32
TICKER_SPEED = 1      # pixels scrolled per matrix scan
TICKER_IDLE  = 5.0    # seconds of idle before ticker starts
UI_RESET     = 1.5    # seconds before display resets after action

LAYER_NAMES = {
    0: "Main Menu",
    1: "Media Controls",
    2: "Websites",
}

LAYER_TICKERS = {
    0: "You are really working hard, keep up!!!",
    1: "Made by Oneline, Made with love",
    2: "Where to now, the word is yours!",
}

# =========================================================
# KEYBOARD INIT
# =========================================================

keyboard = KMKKeyboard()
keyboard.modules.append(Layers())
keyboard.modules.append(Macros())
keyboard.extensions.append(MediaKeys())

keyboard.matrix = KeysScanner(
    pins=PINS,
    value_when_pressed=False,
    pull=True,
)

# =========================================================
# DISPLAY INIT
# =========================================================

displayio.release_displays()
i2c = busio.I2C(board.SCL, board.SDA)

try:
    import i2cdisplaybus
    display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
except ImportError:
    display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

display = adafruit_displayio_ssd1306.SSD1306(
    display_bus, width=DISPLAY_W, height=DISPLAY_H, rotation=180
)

# =========================================================
# BOOT SPLASH  —  wipe in, hold, wipe out
# =========================================================

def _wipe(group, wipe_in, steps=16):
    step_w = DISPLAY_W // steps
    for i in range(steps + 1):
        w = i * step_w
        x = w if wipe_in else 0
        cover = DISPLAY_W - w if wipe_in else w
        if len(group) > 1:
            group.pop()
        if cover > 0:
            group.append(Rect(x, 0, min(cover, DISPLAY_W), DISPLAY_H, fill=0x000000))
        time.sleep(0.04 if wipe_in else 0.03)

def show_boot_image():
    try:
        grp = displayio.Group()
        with open("/boot_1.bmp", "rb") as f:
            odb  = displayio.OnDiskBitmap(f)
            grp.append(displayio.TileGrid(odb, pixel_shader=odb.pixel_shader))
            grp.append(Rect(0, 0, DISPLAY_W, DISPLAY_H, fill=0x000000))
            display.root_group = grp
            _wipe(grp, wipe_in=True)
            time.sleep(2.0)
            _wipe(grp, wipe_in=False)
    except (OSError, ValueError):
        grp = displayio.Group()
        grp.append(label.Label(terminalio.FONT, text="MACRO PAD", color=0xFFFFFF, x=30, y=16))
        display.root_group = grp
        time.sleep(1.5)

show_boot_image()

# =========================================================
# MAIN UI  —  built once, mutated by update functions
# =========================================================

main_group   = displayio.Group()
ui_header    = label.Label(terminalio.FONT, text="MAIN APPS",    color=0xFFFFFF, x=4,  y=8)
ui_status    = label.Label(terminalio.FONT, text="SYSTEM READY", color=0xFFFFFF, x=28, y=25)
ticker_label = label.Label(terminalio.FONT, text="",             color=0xFFFFFF, x=DISPLAY_W, y=25)
vol_group    = displayio.Group()

main_group.append(ui_header)
main_group.append(Line(0, 16, DISPLAY_W, 16, color=0xFFFFFF))
main_group.append(ui_status)
main_group.append(ticker_label)
main_group.append(vol_group)

display.root_group = main_group

# =========================================================
# STATE
# =========================================================

volume_val     = 50
last_ui_time   = 0.0
showing_custom = False
last_layer     = 0
ticker_active  = False
ticker_text    = ""
ticker_x       = DISPLAY_W

# =========================================================
# ANIMATIONS
# =========================================================

def type_text(text, delay=0.045):
    ui_status.hidden = False
    for i in range(len(text) + 1):
        ui_status.text = text[:i] + ("_" if i < len(text) else "")
        time.sleep(delay)
    ui_status.text = text

def flash_display():
    for _ in range(2):
        ui_header.color = 0x000000
        time.sleep(0.04)
        ui_header.color = 0xFFFFFF
        time.sleep(0.04)

def _clear_vol():
    while vol_group:
        vol_group.pop()

def _draw_vol_bar():
    _clear_vol()
    vol_group.append(Rect(24, 21, 80, 8, outline=0xFFFFFF))
    vol_group.append(Rect(26, 23, max(1, int(volume_val / 100 * 76)), 4, fill=0xFFFFFF))

# =========================================================
# DISPLAY UPDATE
# =========================================================

def update_display(header, status=None, is_vol=False, flash=False, typing=False):
    global last_ui_time, showing_custom, ticker_active

    ticker_active     = False
    ticker_label.text = ""
    ui_header.text    = header

    if is_vol:
        ui_status.hidden = True
        _draw_vol_bar()
    else:
        _clear_vol()
        ui_status.hidden = False
        if status:
            if typing:
                type_text(status)
            else:
                ui_status.text = status

    if flash:
        flash_display()

    last_ui_time   = time.monotonic()
    showing_custom = True

def reset_to_idle():
    global showing_custom, last_ui_time
    layer = keyboard.active_layers[0]
    name  = LAYER_NAMES.get(layer, f"Layer {layer}")
    _clear_vol()
    ui_header.text   = f"[L{layer}] {name}"
    ui_status.text   = "System Ready"
    ui_status.hidden = False
    showing_custom   = False
    last_ui_time     = time.monotonic()

# =========================================================
# TICKER
# =========================================================

def start_ticker(layer):
    global ticker_active, ticker_x, ticker_text
    ticker_text        = LAYER_TICKERS.get(layer, "")
    ticker_x           = DISPLAY_W
    ticker_label.text  = ticker_text
    ticker_label.x     = ticker_x
    ui_status.hidden   = True
    ticker_active      = True

def tick_ticker():
    global ticker_x
    ticker_x -= TICKER_SPEED
    if ticker_x < -(len(ticker_text) * 6):
        ticker_x = DISPLAY_W
    ticker_label.x = ticker_x

# =========================================================
# MATRIX SCAN HOOK
# =========================================================

def check_status(*args, **kwargs):
    global showing_custom, last_layer, ticker_active, last_ui_time, ticker_x, ticker_text

    now   = time.monotonic()
    layer = keyboard.active_layers[0]

    if layer != last_layer:
        name = LAYER_NAMES.get(layer, f"Layer {layer}")
        ticker_active     = False
        ticker_label.text = ""
        _clear_vol()
        ui_header.text   = f"[L{layer}] {name}"
        ui_status.hidden = False
        type_text("Ready")
        last_ui_time   = now
        showing_custom = True
        last_layer     = layer
        return

    if showing_custom and now - last_ui_time > UI_RESET:
        reset_to_idle()
        return

    if not showing_custom and not ticker_active and now - last_ui_time > TICKER_IDLE:
        start_ticker(layer)
        return

    if ticker_active:
        tick_ticker()

keyboard.before_matrix_scan = check_status

# =========================================================
# KEY BUILDERS
# =========================================================

def vol_up_press(key, keyboard, *args, **kwargs):
    global volume_val
    volume_val = min(volume_val + 2, 100)
    update_display(f"VOL: {volume_val}%", is_vol=True)
    keyboard.tap_key(KC.VOLU)

def vol_down_press(key, keyboard, *args, **kwargs):
    global volume_val
    volume_val = max(volume_val - 2, 0)
    update_display(f"VOL: {volume_val}%", is_vol=True)
    keyboard.tap_key(KC.VOLD)

VOL_UP   = make_key(names=("VOL_UP_D",),   on_press=vol_up_press)
VOL_DOWN = make_key(names=("VOL_DOWN_D",), on_press=vol_down_press)

def make_media_key(kc, name):
    def on_press(key, keyboard, *args, **kwargs):
        update_display("MEDIA", name, flash=True)
        keyboard.tap_key(kc)
    return make_key(names=(name,), on_press=on_press)

PLAY_PAUSE = make_media_key(KC.MPLY, "Play/Pause")
NEXT_TRACK = make_media_key(KC.MNXT, "Next Track")
PREV_TRACK = make_media_key(KC.MPRV, "Prev Track")
MUTE_KEY   = make_media_key(KC.MUTE, "Mute")
STOP_KEY   = make_media_key(KC.MSTP, "Stop")

def url_to_taps(url):
    special = {':': KC.COLN, '/': KC.SLSH, '.': KC.DOT, '-': KC.MINS,
               '_': KC.UNDS, '?': KC.QUES, '=': KC.EQL, '#': KC.HASH, '@': KC.AT}
    taps = []
    for ch in url:
        if ch in special:
            taps.append(Tap(special[ch]))
        elif ch.isalpha():
            taps.append(Tap(getattr(KC, ch.upper())))
        elif ch.isdigit():
            taps.append(Tap(getattr(KC, f"N{ch}")))
    return taps

def create_web_macro(url, name):
    seq = [Press(KC.LWIN), Tap(KC.R), Release(KC.LWIN), Delay(450)]
    seq += url_to_taps(url)
    seq.append(Tap(KC.ENTER))
    key = KC.MACRO(*seq)
    orig = key.on_press
    def on_press(key_obj, kb, *a, **kw):
        update_display("LAUNCHING...", name, flash=True)
        return orig(key_obj, kb, *a, **kw)
    key.on_press = on_press
    return key

# =========================================================
# MACRO KEYS
# =========================================================

YT_M     = create_web_macro("https://youtube.com","Youtube")
DIS_M    = create_web_macro("https://discord.com/channels/@me", "Discord")
GCPS_M   = create_web_macro("https://apps.gcpsk12.org",  "GCPS Portal")
GMAIL_M  = create_web_macro("https://gmail.com", "Gmail")
GH_M     = create_web_macro("https://github.com", "Github")
REDDIT_M = create_web_macro("https://reddit.com", "Reddit")
CHAT_M   = create_web_macro("https://gemini.google.com", "Google Gemini")
TWITCH_M = create_web_macro("https://twitch.tv", "Twitch")

# =========================================================
# KEYMAP
#
#  Physical layout:   D7    D8    D9
#                     D10   D0    D6
#
#  Layer 0 MAIN:    VOL-   YT    HOLD=L1/TAP=PLAY
#                   DISC   VOL+  TG(2)
#
#  Layer 1 MEDIA:   PREV   NEXT  (hold)
#                   STOP   MUTE  PLAY
#
#  Layer 2 WEB:     GMAIL  GH    REDDIT
#                   CHAT   TWCH  TG(2)
# =========================================================

keyboard.keymap = [
    [VOL_DOWN,   YT_M,      KC.LT(1, KC.MPLY),
     DIS_M,      VOL_UP,    KC.TG(2)],

    [PREV_TRACK, NEXT_TRACK, KC.TRNS,
     STOP_KEY,   MUTE_KEY,   PLAY_PAUSE],

    [GMAIL_M,    GH_M,       REDDIT_M,
     CHAT_M,     TWITCH_M,   KC.TG(2)],
]

if __name__ == "__main__":
    keyboard.go()
