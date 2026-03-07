import board
import busio
import displayio
import terminalio
import time
import neopixel
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
TICKER_IDLE  = 5.0    # seconds idle before ticker starts
UI_RESET     = 1.5    # seconds before display resets after action

# ── Layer registry ─────────────────────────────────────────
# L0 Main Menu  │ L1 Media     │ L2 Websites
# L3 Settings   │ L4 Gaming    │ L5 Dev Tools

LAYER_NAMES = {
    0: "Main Menu",
    1: "Media",
    2: "Websites",
    3: "Settings",
    4: "Gaming",
    5: "Dev Tools",
}

LAYER_TICKERS = {
    0: "My first project!",
    1: "Made by Oneline, Made with love",
    2: "Search Somthing Up",
    3: "Careful — you can mess somthing up",
    4: "Boy you trash",
    5: "6 hours later => Still messed up",
}

# ── NeoPixel LED colors per layer ─────────────────────────
# One built-in NeoPixel on the XIAO RP2040 (board.NEOPIXEL)

NEOPIXEL_PIN   = board.NEOPIXEL
LED_BRIGHTNESS = 0.15   # 0.0 – 1.0  (keep low, it's very bright!)

LAYER_COLORS = {
    0: (255, 255, 255),   # L0 Main Menu  → White
    1: (0,   100, 255),   # L1 Media      → Blue
    2: (0,   200,  80),   # L2 Websites   → Green
    3: (255, 140,   0),   # L3 Settings   → Amber
    4: (180,   0, 255),   # L4 Gaming     → Purple
    5: (255,  40,  40),   # L5 Dev Tools  → Red
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
# NEOPIXEL INIT
# =========================================================

np = neopixel.NeoPixel(NEOPIXEL_PIN, 1, brightness=LED_BRIGHTNESS, auto_write=True)

def set_led(layer):
    """Set the NeoPixel to the color associated with the given layer."""
    np[0] = LAYER_COLORS.get(layer, (255, 255, 255))

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
# BOOT SPLASH
# =========================================================

def _wipe(group, wipe_in, steps=16):
    step_w = DISPLAY_W // steps
    for i in range(steps + 1):
        w     = i * step_w
        x     = w if wipe_in else 0
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
            odb = displayio.OnDiskBitmap(f)
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

# Boot: show splash then set LED to Main Menu color
show_boot_image()
set_led(0)

# =========================================================
# MAIN UI  — built once, mutated by helpers
#
#  ┌────────────────────────────────┐  ← 128×32 OLED
#  │ ● MAIN MENU                   │  row 0-13  (header)
#  │────────────────────────────────│  row 14-15 (divider, 2px)
#  │  System Ready                 │  row 16-31 (status / vol / ticker)
#  └────────────────────────────────┘
# =========================================================

# Layer icon map — single char prefix per layer
LAYER_ICONS = {
    0: chr(0x10),   # ► arrow (terminalio built-in glyph)
    1: "~",         # wave = music
    2: "@",         # web
    3: "*",         # settings star
    4: "+",         # gaming crosshair
    5: "$",         # dev / code
}

main_group   = displayio.Group()

# Header row  (y=9 = vertical centre of top 14 px)
ui_header    = label.Label(terminalio.FONT, text="MAIN MENU", color=0xFFFFFF, x=2, y=9)

# Divider — two 1px lines for a bolder separator
div1         = Rect(0, 14, DISPLAY_W, 1, fill=0xFFFFFF)
div2         = Rect(0, 15, DISPLAY_W, 1, fill=0xFFFFFF)

# Status / hint line  (y=24 = vertical centre of bottom 16 px)
ui_status    = label.Label(terminalio.FONT, text="System Ready", color=0xFFFFFF, x=2, y=24)

# Scrolling ticker — starts off-screen to the right
ticker_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=DISPLAY_W, y=24)

# Volume bar group — drawn on demand
vol_group    = displayio.Group()

main_group.append(ui_header)
main_group.append(div1)
main_group.append(div2)
main_group.append(ui_status)
main_group.append(ticker_label)
main_group.append(vol_group)

display.root_group = main_group

# =========================================================
# STATE
# =========================================================

volume_val      = 50
last_ui_time    = 0.0
showing_custom  = False
last_layer      = 0
ticker_active   = False
ticker_text     = ""
ticker_x        = DISPLAY_W
last_tick_time  = 0.0        # throttle ticker scroll speed
TICK_INTERVAL   = 0.03       # seconds between each pixel scroll (~33fps)

# =========================================================
# ANIMATIONS & DRAWING HELPERS
# =========================================================

def type_text(text, delay=0.04):
    """Typewriter effect on the status line."""
    ui_status.hidden = False
    ticker_label.text = ""
    for i in range(len(text) + 1):
        ui_status.text = text[:i] + ("_" if i < len(text) else "")
        time.sleep(delay)
    ui_status.text = text

def blink_header(times=2):
    """Briefly blink the header text to acknowledge a keypress."""
    for _ in range(times):
        ui_header.color = 0x000000
        time.sleep(0.03)
        ui_header.color = 0xFFFFFF
        time.sleep(0.03)

def _clear_vol():
    while vol_group:
        vol_group.pop()

def _draw_vol_bar():
    """Draw a clean volume bar with percentage label."""
    _clear_vol()
    # Background track
    vol_group.append(Rect(0, 17, DISPLAY_W, 14, fill=0x000000))
    # Label
    pct_text = label.Label(terminalio.FONT, text=f"VOL {volume_val:3d}%",
                           color=0xFFFFFF, x=2, y=24)
    vol_group.append(pct_text)
    # Bar outline  (starts after label ~52px)
    bar_x = 54
    bar_w = DISPLAY_W - bar_x - 2
    vol_group.append(Rect(bar_x, 20, bar_w, 8, outline=0xFFFFFF))
    # Bar fill
    fill_w = max(1, int(volume_val / 100 * (bar_w - 2)))
    vol_group.append(Rect(bar_x + 1, 21, fill_w, 6, fill=0xFFFFFF))

# =========================================================
# DISPLAY UPDATE
# =========================================================

def _set_header(layer):
    """Build the header string: icon + layer name."""
    icon = LAYER_ICONS.get(layer, "-")
    name = LAYER_NAMES.get(layer, f"L{layer}")
    ui_header.text = f"{icon} {name}"

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
        blink_header()

    last_ui_time   = time.monotonic()
    showing_custom = True

def reset_to_idle():
    """Return to the clean idle state for the current layer."""
    global showing_custom, last_ui_time, ticker_active, ticker_x
    layer = keyboard.active_layers[0]
    _clear_vol()
    _set_header(layer)
    ui_status.text    = "Ready"
    ui_status.hidden  = False
    ticker_label.text = ""
    ticker_label.x    = DISPLAY_W
    ticker_active     = False
    ticker_x          = DISPLAY_W
    showing_custom    = False
    last_ui_time      = time.monotonic()

# =========================================================
# TICKER
# =========================================================

def start_ticker(layer):
    global ticker_active, ticker_x, ticker_text, last_tick_time
    ticker_text       = LAYER_TICKERS.get(layer, "")
    ticker_x          = DISPLAY_W
    ticker_label.text = ticker_text
    ticker_label.x    = ticker_x
    ticker_label.hidden = False
    ui_status.hidden  = True
    last_tick_time    = time.monotonic()
    ticker_active     = True

def tick_ticker():
    global ticker_x, last_tick_time
    now = time.monotonic()
    if now - last_tick_time < TICK_INTERVAL:
        return                          # not time to scroll yet
    last_tick_time = now
    ticker_x -= TICKER_SPEED
    if ticker_x < -(len(ticker_text) * 6):
        ticker_x = DISPLAY_W            # loop back to start
    ticker_label.x = ticker_x

# =========================================================
# MATRIX SCAN HOOK
# =========================================================

def check_status(*args, **kwargs):
    global showing_custom, last_layer, ticker_active, last_ui_time

    now   = time.monotonic()
    layer = keyboard.active_layers[0]

    if layer != last_layer:
        set_led(layer)              # ← update NeoPixel on layer change
        ticker_active     = False
        ticker_label.text = ""
        _clear_vol()
        _set_header(layer)
        ui_status.hidden = False
        type_text("Ready")
        last_ui_time   = now
        showing_custom = True
        last_layer     = layer
        return

    if showing_custom and now - last_ui_time > UI_RESET:
        reset_to_idle()
        return

    # On Main Menu (L0): page through key-map hints instead of ticker
    if layer == 0 and not showing_custom:
        update_menu_hint()
        return

    if not showing_custom and not ticker_active and now - last_ui_time > TICKER_IDLE:
        start_ticker(layer)
        return

    if ticker_active:
        tick_ticker()

keyboard.before_matrix_scan = check_status

# =========================================================
# HELPER — Layer-toggle key with display hint
# =========================================================

# What to show on the bottom status line when on L0 idle.
# Cycles through two "pages" so all 5 destinations are visible.
MENU_PAGE_A = "1:Media 2:Websites 3:Settings"
MENU_PAGE_B = "4:Game 5:Dev"
_menu_page      = 0
_menu_page_time = 0.0
MENU_PAGE_INTERVAL = 3.0   # seconds per page

def update_menu_hint():
    """Called from check_status when on L0 idle — pages through key hints."""
    global _menu_page, _menu_page_time
    now = time.monotonic()
    if now - _menu_page_time > MENU_PAGE_INTERVAL:
        _menu_page = 1 - _menu_page
        _menu_page_time = now
    ui_status.hidden = False
    ui_status.text   = MENU_PAGE_A if _menu_page == 0 else MENU_PAGE_B

def make_menu_toggle(layer_num, label_text, returning=False):
    """
    Toggle a layer on/off with a display transition.
    returning=True  → plays a 'Going Home' animation (used by back keys).
    returning=False → plays a 'Switching' animation (used by menu keys).
    """
    key  = KC.TO(layer_num)
    orig = key.on_press
    def on_press(key_obj, kb, *a, **kw):
        global ticker_active, ticker_x, showing_custom, last_ui_time
        icon = LAYER_ICONS.get(layer_num, "-")
        if returning:
            ticker_active     = False
            ticker_x          = DISPLAY_W
            ticker_label.text = ""
            ticker_label.x    = DISPLAY_W
            _clear_vol()
            ui_header.text    = f"{icon} {label_text}"
            ui_status.hidden  = False
            ui_status.text    = "< Back to Menu"
            showing_custom    = True
            last_ui_time      = time.monotonic()
            blink_header(1)
        else:
            update_display(f"{icon} {label_text}", "Switching...", flash=True)
        return orig(key_obj, kb, *a, **kw)
    key.on_press = on_press
    return key

# Forward navigation — from Main Menu into a layer
TO_MEDIA    = make_menu_toggle(1, "Media")
TO_WEBSITES = make_menu_toggle(2, "Websites")
TO_SETTINGS = make_menu_toggle(3, "Settings")
TO_GAMING   = make_menu_toggle(4, "Gaming")
TO_DEVTOOLS = make_menu_toggle(5, "Dev Tools")

# Back navigation
TO_MAIN     = make_menu_toggle(0, "Main Menu", returning=True)

# =========================================================
# VOLUME KEYS
# =========================================================

def vol_up_press(key, keyboard, *args, **kwargs):
    global volume_val
    volume_val = min(volume_val + 2, 100)
    update_display("~ Volume", is_vol=True)
    keyboard.tap_key(KC.VOLU)

def vol_down_press(key, keyboard, *args, **kwargs):
    global volume_val
    volume_val = max(volume_val - 2, 0)
    update_display("~ Volume", is_vol=True)
    keyboard.tap_key(KC.VOLD)

VOL_UP   = make_key(names=("VOL_UP_D",),   on_press=vol_up_press)
VOL_DOWN = make_key(names=("VOL_DOWN_D",), on_press=vol_down_press)

# =========================================================
# MEDIA KEYS  (Layer 1)
# =========================================================

def make_media_key(kc, name):
    """
    Wrap a native KMK media key with a display update.
    We chain into the key's existing on_press so the HID report
    is sent correctly through KMK's pipeline — no tap_key() needed.
    """
    key  = kc
    orig = key.on_press
    def on_press(key_obj, kb, *a, **kw):
        update_display("~ Media", name, flash=False)
        return orig(key_obj, kb, *a, **kw)
    key.on_press = on_press
    return key

PLAY_PAUSE  = make_media_key(KC.MPLY, "Play / Pause")
NEXT_TRACK  = make_media_key(KC.MEDIA_NEXT_TRACK, "Next Track")
PREV_TRACK  = make_media_key(KC.MEDIA_PREV_TRACK, "Prev Track")
MUTE_KEY    = make_media_key(KC.MUTE, "Mute")
STOP_KEY    = make_media_key(KC.MSTP, "Stop")
BRIGHT_UP   = make_media_key(KC.BRIU, "Bright +")
BRIGHT_DOWN = make_media_key(KC.BRID, "Bright -")

# =========================================================
# MACRO HELPERS
# =========================================================

def with_display(macro_key, header, label_text):
    orig_press = macro_key.on_press
    def on_press(key_obj, kb, *a, **kw):
        update_display(header, label_text, flash=True)
        return orig_press(key_obj, kb, *a, **kw)
    macro_key.on_press = on_press
    return macro_key

def win_run(cmd_string, header, label_text):
    key = KC.MACRO(
        Press(KC.LWIN),
        Tap(KC.R),
        Release(KC.LWIN),
        Delay(500),
        cmd_string,
        Tap(KC.ENTER),
        blocking=True,
    )
    return with_display(key, header, label_text)

# =========================================================
# SETTINGS MACROS  (Layer 3)
# =========================================================

LOCK_PC = with_display(
    KC.MACRO(Press(KC.LWIN), Tap(KC.L), Release(KC.LWIN)),
    "* Settings", "Lock PC"
)

SCREENSHOT = with_display(
    KC.MACRO(
        Press(KC.LWIN), Press(KC.LSFT),
        Tap(KC.S),
        Release(KC.LSFT), Release(KC.LWIN),
    ),
    "* Settings", "Screenshot"
)

TASK_MGR = with_display(
    KC.MACRO(
        Press(KC.LCTL), Press(KC.LSFT),
        Tap(KC.ESC),
        Release(KC.LSFT), Release(KC.LCTL),
    ),
    "* Settings", "Task Manager"
)

SLEEP_PC = with_display(
    KC.MACRO(
        Press(KC.LWIN), Tap(KC.X), Release(KC.LWIN),
        Delay(300),
        Tap(KC.U),
        Delay(150),
        Tap(KC.S),
    ),
    "* Settings", "Sleep..."
)

# =========================================================
# WEBSITE MACROS  (Layer 2)
# =========================================================

def open_url(url, name):
    return win_run(url, "@ Websites", name)

YT_M      = open_url("https://youtube.com",              "YouTube")
GMAIL_M   = open_url("https://gmail.com",                "Gmail")
GH_M      = open_url("https://github.com",               "GitHub")
DIS_WEB_M = open_url("https://discord.com/channels/@me", "Discord")
REDDIT_M  = open_url("https://reddit.com",               "Reddit")

# =========================================================
# GAMING MACROS  (Layer 4)
# =========================================================

def launch_app(cmd, name):
    return win_run(cmd, "+ Gaming", name)

DISCORD_APP = launch_app(r"C:\Users\Administrator\Desktop\Discord.lnk",  "Discord")
STEAM_APP   = launch_app(r"C:\Program Files (x86)\Steam\Steam.exe",    "Steam")
SPOTIFY_APP = launch_app(r"C:\Users\Administrator\Desktop\Spotify.lnk",  "Spotify")
TWITCH_M    = open_url(r"C:\Users\Administrator\Desktop\Playnite.lnk", "Playnite")

GAMEBAR = with_display(
    KC.MACRO(Press(KC.LWIN), Tap(KC.G), Release(KC.LWIN)),
    "+ Gaming", "Game Bar"
)

# =========================================================
# DEV TOOLS MACROS  (Layer 5)
# =========================================================

RIDER   = launch_app(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\JetBrains\JetBrains Rider 2025.1.5.lnk",       "Rider")
PYCHARM = launch_app(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\JetBrains\PyCharm 2025.2.lnk",         "PyCharm")
CMD      = launch_app("cmd",        "CMD")
PWSH     = launch_app("powershell", "PowerShell")

GIT_COMMIT = with_display(
    KC.MACRO(
        'git commit -m ""',
        Tap(KC.LEFT),
    ),
    "$ Dev Tools", "git commit"
)

keyboard.keymap = [

    [TO_MEDIA,    TO_WEBSITES,  TO_SETTINGS,
     TO_GAMING,   TO_DEVTOOLS,  KC.NO],

    [PREV_TRACK,  NEXT_TRACK,   PLAY_PAUSE,
     VOL_DOWN,    VOL_UP,       TO_MAIN],

    [YT_M,        GMAIL_M,      GH_M,
     DIS_WEB_M,   REDDIT_M,     TO_MAIN],

    [LOCK_PC,     BRIGHT_UP,    BRIGHT_DOWN,
     SLEEP_PC,    TASK_MGR,     TO_MAIN],

    [DISCORD_APP, STEAM_APP,    GAMEBAR,
     SPOTIFY_APP, TWITCH_M,     TO_MAIN],

    [RIDER,       PYCHARM,      CMD,
     PWSH,        GIT_COMMIT,   TO_MAIN],
]

if __name__ == "__main__":
    keyboard.go()
