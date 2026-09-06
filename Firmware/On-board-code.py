import time
import board
import digitalio
import busio
import rotaryio
import usb_hid
import json
import supervisor
import os
import random
import math
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
import adafruit_ssd1306

# --- OVERCLOCKED FAST-I2C OLED INITIALIZATION ---
time.sleep(0.5)

init_sda = digitalio.DigitalInOut(board.GP16)
init_scl = digitalio.DigitalInOut(board.GP17)
init_sda.switch_to_input(pull=digitalio.Pull.UP)
init_scl.switch_to_input(pull=digitalio.Pull.UP)
time.sleep(0.1)
init_sda.deinit()
init_scl.deinit()

try:
    i2c = busio.I2C(board.GP17, board.GP16, frequency=1000000) 
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
except Exception as e:
    print("I2C Hardware Initialization Failed:", e)
    raise e

# --- EMBEDDED INTERNAL BITMAP FONT SYSTEM ---
FONT_5X8 = {
    'A': (0x7E, 0x11, 0x11, 0x11, 0x7E), 'B': (0x7F, 0x49, 0x49, 0x49, 0x36),
    'C': (0x3E, 0x41, 0x41, 0x41, 0x22), 'D': (0x7F, 0x41, 0x41, 0x22, 0x1C),
    'E': (0x7F, 0x49, 0x49, 0x49, 0x41), 'F': (0x7F, 0x09, 0x09, 0x09, 0x06),
    'G': (0x3E, 0x41, 0x49, 0x49, 0x7A), 'H': (0x7F, 0x08, 0x08, 0x08, 0x7F),
    'I': (0x41, 0x41, 0x7F, 0x41, 0x41), 'J': (0x20, 0x40, 0x41, 0x3F, 0x01),
    'K': (0x7F, 0x08, 0x14, 0x22, 0x41), 'L': (0x7F, 0x40, 0x40, 0x40, 0x40),
    'N': (0x7F, 0x04, 0x08, 0x10, 0x7F), 'O': (0x3E, 0x41, 0x41, 0x41, 0x3E), 
    'P': (0x7F, 0x09, 0x09, 0x09, 0x06), 'Q': (0x3E, 0x41, 0x51, 0x21, 0x5E), 
    'S': (0x46, 0x49, 0x49, 0x49, 0x31), 'T': (0x01, 0x01, 0x7F, 0x01, 0x01),
    'U': (0x3F, 0x40, 0x40, 0x40, 0x3F), 'W': (0x7F, 0x20, 0x18, 0x20, 0x7F), 
    'X': (0x63, 0x14, 0x08, 0x14, 0x63), 'Y': (0x07, 0x08, 0x70, 0x08, 0x07), 
    'Z': (0x61, 0x51, 0x49, 0x45, 0x43), '0': (0x3E, 0x51, 0x49, 0x45, 0x3E), 
    '1': (0x00, 0x42, 0x7F, 0x40, 0x00), '2': (0x42, 0x61, 0x51, 0x49, 0x46), 
    '4': (0x18, 0x14, 0x12, 0x7F, 0x10), '5': (0x27, 0x45, 0x45, 0x45, 0x39),
    '6': (0x3C, 0x4A, 0x49, 0x49, 0x30), '7': (0x01, 0x71, 0x09, 0x05, 0x03),
    '8': (0x36, 0x49, 0x49, 0x49, 0x36), '9': (0x06, 0x49, 0x29, 0x1E, 0x1E),
    ':': (0x00, 0x36, 0x36, 0x00, 0x00), '-': (0x08, 0x08, 0x08, 0x08, 0x08),
    '|': (0x00, 0x00, 0x7F, 0x00, 0x00), '_': (0x40, 0x40, 0x40, 0x40, 0x40),
    '/': (0x20, 0x10, 0x08, 0x04, 0x02), '+': (0x08, 0x08, 0x3E, 0x08, 0x08),
    '<': (0x08, 0x14, 0x22, 0x41, 0x00), '>': (0x00, 0x41, 0x22, 0x14, 0x08),
    '%': (0x32, 0x4C, 0x18, 0x32, 0x4C), ' ': (0x00, 0x00, 0x00, 0x00, 0x00),
    '3': (0x22, 0x41, 0x49, 0x49, 0x36), 'V': (0x1F, 0x20, 0x40, 0x20, 0x1F),
    'R': (0x7F, 0x09, 0x19, 0x29, 0x46), 'M': (0x7F, 0x02, 0x04, 0x02, 0x7F),
    '[': (0x00, 0x7F, 0x41, 0x41, 0x00), ']': (0x00, 0x41, 0x41, 0x7F, 0x00)
}

def draw_string_faded(text_str, x_start, y_start, pass_mask=0xFF):
    current_x = x_start
    for char in text_str.upper():
        bitmap = FONT_5X8.get(char, FONT_5X8[' '])
        for col_idx in range(5):
            col_data = bitmap[col_idx]
            for bit_idx in range(8):
                if (col_data >> bit_idx) & 1:
                    if ((col_idx + bit_idx) & pass_mask) == 0:
                        continue
                    if (current_x + col_idx) < 128 and (y_start + bit_idx) < 64:
                        oled.pixel(current_x + col_idx, y_start + bit_idx, 1)
        current_x += 6

def draw_string(text_str, x_start, y_start):
    draw_string_faded(text_str, x_start, y_start, pass_mask=0xFF)

def draw_string_vertical_90(text_str, x_start, y_start):
    current_y = y_start
    for char in text_str.upper():
        bitmap = FONT_5X8.get(char, FONT_5X8[' '])
        for col_idx in range(5):
            col_data = bitmap[col_idx]
            for bit_idx in range(8):
                if (col_data >> bit_idx) & 1:
                    px = x_start - bit_idx
                    py = current_y + col_idx
                    if 0 <= px < 128 and 0 <= py < 64:
                        oled.pixel(px, py, 1)
        current_y += 6

# --- INITIALIZE USB HID DEVICES ---
kbd = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

# --- MATRICES PINS CONFIGURATION ---
ROW_PINS = [board.GP6, board.GP7, board.GP8]   
COL_PINS = [board.GP10, board.GP11, board.GP12]

rows = [digitalio.DigitalInOut(pin) for pin in ROW_PINS]
for row in rows:
    row.direction = digitalio.Direction.OUTPUT
    row.value = True

cols = [digitalio.DigitalInOut(pin) for pin in COL_PINS]
for col in cols:
    col.direction = digitalio.Direction.INPUT
    col.pull = digitalio.Pull.UP

# --- ROTARY ENCODERS ---
enc1 = rotaryio.IncrementalEncoder(board.GP5, board.GP4)
sw1 = digitalio.DigitalInOut(board.GP3)
sw1.direction = digitalio.Direction.INPUT
sw1.pull = digitalio.Pull.UP

enc2 = rotaryio.IncrementalEncoder(board.GP2, board.GP1)
sw2 = digitalio.DigitalInOut(board.GP0)
sw2.direction = digitalio.Direction.INPUT
sw2.pull = digitalio.Pull.UP

last_raw_positions = [enc1.position, enc2.position]
last_sw_states = [sw1.value, sw2.value]

# --- DYNAMIC CONFIG & TIMERS ---
IDLE_TIMEOUT_MS = 120000  
idle_animation = "matrix"
custom_gif_frames = []
gif_w, gif_h = 0, 0
current_frame_index = 0

# Swapped out date and time stamps for global string variables
custom_text_l1 = "3vKRM"
custom_text_l2 = "READY"

last_activity_time = supervisor.ticks_ms()
is_idle = False
last_anim_frame_time = 0
last_file_check_time = 0
last_file_mtime = 0

# --- STATIC NOTIFIER SYSTEM ---
ko_text = ""
ko_y = 52
ko_state = 0  
ko_timer = 0

STRING_TO_KEYCODE = {
    "A": Keycode.A, "B": Keycode.B, "C": Keycode.C, "D": Keycode.D, "E": Keycode.E,
    "F": Keycode.F, "G": Keycode.G, "H": Keycode.H, "I": Keycode.I, "J": Keycode.J,
    "K": Keycode.K, "L": Keycode.L, "M": Keycode.M, "N": Keycode.N, "O": Keycode.O,
    "P": Keycode.P, "Q": Keycode.Q, "R": Keycode.R, "S": Keycode.S, "T": Keycode.T,
    "U": Keycode.U, "V": Keycode.V, "W": Keycode.W, "X": Keycode.X, "Y": Keycode.Y, "Z": Keycode.Z,
    "1": Keycode.ONE, "2": Keycode.TWO, "3": Keycode.THREE, "4": Keycode.FOUR, "5": Keycode.FIVE,
    "6": Keycode.SIX, "7": Keycode.SEVEN, "8": Keycode.EIGHT, "9": Keycode.NINE, "0": Keycode.ZERO,
    "Ctrl": Keycode.CONTROL, "Shift": Keycode.SHIFT, "Alt": Keycode.ALT, "Win": Keycode.GUI,
    "Space": Keycode.SPACE, "Enter": Keycode.ENTER, "Backspace": Keycode.BACKSPACE, "Tab": Keycode.TAB,
    
    # Escape mappings (Added)
    "Esc": Keycode.ESCAPE,
    "Escape": Keycode.ESCAPE,
    
    # Arrow mappings (Supports both short and long naming styles)
    
    "ArrowUp": Keycode.UP_ARROW,
    "ArrowDown": Keycode.DOWN_ARROW,
    "ArrowLeft": Keycode.LEFT_ARROW,
    "ArrowRight": Keycode.RIGHT_ARROW
}

def get_file_mtime():
    try:
        return os.stat("config.json")[8]
    except Exception:
        return 0

def load_config(trigger_alert=False):
    global key_mapping, last_file_mtime, IDLE_TIMEOUT_MS, idle_animation, custom_gif_frames, gif_w, gif_h, custom_text_l1, custom_text_l2
    if trigger_alert:
        try:
            oled.fill(0)
            oled.rect(4, 18, 120, 28, 1)
            draw_string("CONFIG SYNCED", 26, 28)
            oled.show()
            time.sleep(0.6)
        except:
            pass

    try:
        with open("config.json", "r") as f:
            raw_data = json.load(f)
        
        if isinstance(raw_data, dict) and "matrix" in raw_data:
            key_mapping = raw_data["matrix"]
            IDLE_TIMEOUT_MS = int(raw_data.get("idle_timeout_min", 2)) * 60000
            idle_animation = raw_data.get("idle_animation", "matrix")
            custom_gif_frames = raw_data.get("custom_gif_frames", [])
            gif_w = raw_data.get("gif_width", 0)
            gif_h = raw_data.get("gif_height", 0)
            
            # Map custom properties from JSON payload fields
            if "custom_line1" in raw_data:
                custom_text_l1 = raw_data["custom_line1"]
            if "custom_line2" in raw_data:
                custom_text_l2 = raw_data["custom_line2"]
        else:
            key_mapping = raw_data
            IDLE_TIMEOUT_MS = 120000
            idle_animation = "matrix"
            custom_gif_frames = []
    except Exception:
        key_mapping = [
            ["MOUSE_LEFT", "W", "MOUSE_RIGHT"],
            ["A", "S", "D"],
            ["MOUSE_CLICK", "Space", "Ctrl"],
            ["VOL_DOWN", "VOL_UP", "MUTE", "SCROLL_DOWN", "SCROLL_UP", "MOUSE_CLICK"]
        ]
        IDLE_TIMEOUT_MS = 120000
        idle_animation = "matrix"
        custom_gif_frames = []
    last_file_mtime = get_file_mtime()

load_config(trigger_alert=False)

def get_key_codes(action_str):
    if not action_str or "MOUSE" in action_str or "VOL" in action_str or "SCROLL" in action_str or "MUTE" in action_str or "BRIGHTNESS" in action_str:
        return []
    if action_str in STRING_TO_KEYCODE:
        return [STRING_TO_KEYCODE[action_str]]
    return [STRING_TO_KEYCODE.get(p.strip()) for p in action_str.split("+") if STRING_TO_KEYCODE.get(p.strip())]

def press_action_physical(action_str):
    global ko_text, ko_y, ko_state, ko_timer
    if not action_str:
        return
    
    ko_text = f"RUN: {action_str[:12]}"
    ko_y = 52
    ko_state = 1
    ko_timer = supervisor.ticks_ms()
    
    # OS-Bypassing Keyboard Hotkeys for Brightness
    if action_str == "BRIGHTNESS_UP":
        cc.send(0x006F) # Raw USB HID usage ID for Brightness Increment
        return
    if action_str == "BRIGHTNESS_DOWN":
        cc.send(0x0070) # Raw USB HID usage ID for Brightness Decrement
        return
        
    if action_str == "VOL_UP":
        cc.send(ConsumerControlCode.VOLUME_INCREMENT)
        return
    if action_str == "VOL_DOWN":
        cc.send(ConsumerControlCode.VOLUME_DECREMENT)
        return
    if action_str == "MUTE":
        cc.send(ConsumerControlCode.MUTE)
        return

    if action_str == "MOUSE_CLICK":
        mouse.click(Mouse.LEFT_BUTTON)
        return
    if action_str == "MOUSE_UP":
        mouse.move(y=-15)
        return
    if action_str == "MOUSE_DOWN":
        mouse.move(y=15)
        return
    if action_str == "MOUSE_LEFT":
        mouse.move(x=-15)
        return
    if action_str == "MOUSE_RIGHT":
        mouse.move(x=15)
        return
    if action_str == "SCROLL_UP":
        mouse.move(wheel=1)
        return
    if action_str == "SCROLL_DOWN":
        mouse.move(wheel=-1)
        return
        
    codes = get_key_codes(action_str)
    for c in codes:
        kbd.press(c)

def release_action_physical(action_str):
    if not action_str or "MOUSE" in action_str or "SCROLL" in action_str or "VOL" in action_str or action_str == "MUTE" or "BRIGHTNESS" in action_str:
        return
        
    codes = get_key_codes(action_str)
    for c in codes:
        kbd.release(c)

def draw_active_dashboard():
    oled.fill(0)
    
    # Transposed Matrix coordinates mapping print rendering updates
    draw_string(f"{key_mapping[0][0][:4]}  {key_mapping[0][1][:4]}  {key_mapping[0][2][:4]}", 4, 3)
    draw_string(f"{key_mapping[1][0][:4]}  {key_mapping[1][1][:4]}  {key_mapping[1][2][:4]}", 4, 17)
    draw_string(f"{key_mapping[2][0][:4]}  {key_mapping[2][1][:4]}  {key_mapping[2][2][:4]}", 4, 31)
    
    oled.line(102, 0, 102, 64, 1)  
    oled.line(0, 44, 102, 44, 1)   
    
    # Render customized web text inputs into the 90-degree sidebar slice layout
    draw_string_vertical_90(custom_text_l1[:8], 120, 2)
    draw_string_vertical_90(custom_text_l2[:8], 112, 34)
    
    if ko_state == 1:
        draw_string_faded(ko_text, 4, ko_y, pass_mask=0xFF)
    elif ko_state == 2:
        draw_string_faded(ko_text, 4, ko_y, pass_mask=0x55)
    elif ko_state == 3:
        draw_string_faded(ko_text, 4, ko_y, pass_mask=0x11)
        
    oled.show()

def draw_buffer_bitmap(bitmap, ox, oy, width, height):
    bytes_per_row = (width + 7) // 8
    for r in range(height):
        for c in range(bytes_per_row):
            b = bitmap[r * bytes_per_row + c]
            for bit in range(8):
                if (b >> (7 - bit)) & 1:
                    px = ox + (c * 8) + bit
                    py = oy + r
                    if 0 <= px < 128 and 0 <= py < 64:
                        oled.pixel(px, py, 1)

def draw_hex_string_bitmap(hex_str, width, height):
    try:
        bytes_per_row = (width + 7) // 8
        ox = (128 - width) // 2
        oy = (64 - height) // 2
        for r in range(height):
            for c in range(bytes_per_row):
                idx = (r * bytes_per_row + c) * 2
                b = int(hex_str[idx:idx+2], 16)
                for bit in range(8):
                    if (b >> (7 - bit)) & 1:
                        px = ox + (c * 8) + bit
                        py = oy + r
                        if 0 <= px < 128 and 0 <= py < 64:
                            oled.pixel(px, py, 1)
    except:
        pass

# --- ANIMATION STATE ASSETS ---
NUM_STARS = 12
star_x = [random.randint(0, 127) for _ in range(NUM_STARS)]
star_y = [random.randint(0, 63) for _ in range(NUM_STARS)]
star_layer = [random.choice([1, 2]) for _ in range(NUM_STARS)]

STAR_DESTROYER = [
    0x00, 0x03, 0xC0, 0x00, 0x00, 0x07, 0xE0, 0x00, 0x00, 0x0F, 0xF0, 0x00,
    0x00, 0x1F, 0xF8, 0x00, 0x00, 0x3F, 0xFC, 0x00, 0x00, 0x7F, 0xFE, 0x00,
    0x00, 0xFF, 0xFF, 0x00, 0x01, 0xFF, 0xFF, 0x80, 0x03, 0xFF, 0xFF, 0xC0,
    0x07, 0xFF, 0xFF, 0xE0, 0x0F, 0xFF, 0xFF, 0xF0, 0x1F, 0xFC, 0x3F, 0xF8,
    0x3F, 0xF0, 0x0F, 0xFC, 0x7F, 0xC0, 0x03, 0xFE
]
TIE_FIGHTER = [0x99, 0x99, 0x99, 0x7E, 0x3C, 0x7E, 0x99, 0x99]
tie_x, tie_y = 130, 45

NUM_DROPS = 8
matrix_x = [random.randint(0, 120) for _ in range(NUM_DROPS)]
matrix_y = [random.randint(-30, 0) for _ in range(NUM_DROPS)]
matrix_speed = [random.randint(2, 4) for _ in range(NUM_DROPS)]

anim_frame_counter = 0

# --- CLEAN 3vKRM STARTUP SEQUENCE ---
for frame in range(24):
    oled.fill(0)
    for r_idx in range(3):
        for c_idx in range(3):
            x_base = 24 + c_idx * 34
            y_base = 14 + r_idx * 16
            oled.rect(x_base, y_base, 22, 12, 1)
            if ((frame + r_idx + c_idx) % 6) < 2:
                oled.fill_rect(x_base + 4, y_base + 3, 14, 6, 1)
    oled.show()
    time.sleep(0.05)

# --- BADASS 3vKRM TEXT ANIMATION ---
target_text = "3vKRM "
for i in range(len(target_text) + 1):
    for flash in range(2):  
        oled.fill(0)
        oled.rect(10, 16, 108, 32, 1)
        oled.rect(12, 18, 104, 28, 1)
        current_build = target_text[:i]
        if flash == 0 and i < len(target_text):
            current_build += "_"
        draw_string(current_build, 44, 28)
        oled.show()
        time.sleep(0.06)

draw_active_dashboard()
key_states = [[False, False, False] for _ in range(3)]

# --- MAIN RUN LOOP ---
while True:
    current_time = supervisor.ticks_ms()
    activity_detected = False
    refresh_ui = False

    # --- RELIABLE FLAG CHECK SYSTEM ---
    if (current_time - last_file_check_time) > 1000:  # Check every 1 second
        last_file_check_time = current_time
        try:
            # Check if web panel created the update flag
            if "update.flag" in os.listdir("/"):
                # Delete flag first to avoid infinite loops if reload hits exceptions
                os.remove("/update.flag")
                
                # Fire the sync script and animation!
                load_config(trigger_alert=True)
                last_activity_time = current_time
                is_idle = False
                refresh_ui = True
        except Exception as e:
            pass

    if ko_state == 1 and (current_time - ko_timer) > 300:  
        ko_state = 2; ko_timer = current_time; refresh_ui = True
    elif ko_state == 2 and (current_time - ko_timer) > 150:  
        ko_state = 3; ko_timer = current_time; refresh_ui = True
    elif ko_state == 3 and (current_time - ko_timer) > 150:  
        ko_state = 0; refresh_ui = True

    # Transposed Matrix Keys Scan Logic
    for r in range(3):
        rows[r].value = False  
        for c in range(3):
            is_pressed = not cols[c].value 
            if is_pressed and not key_states[r][c]:
                press_action_physical(key_mapping[c][r])
                activity_detected = True
                key_states[r][c] = True
            elif not is_pressed and key_states[r][c]:
                release_action_physical(key_mapping[c][r])
                key_states[r][c] = False
                refresh_ui = True
        rows[r].value = True   

    # Encoders Tick Tracking
    raw_pos1 = enc1.position
    if raw_pos1 != last_raw_positions[0]:
        delta1 = raw_pos1 - last_raw_positions[0]
        for _ in range(abs(delta1)):
            act = key_mapping[3][1] if delta1 > 0 else key_mapping[3][0]
            press_action_physical(act); release_action_physical(act)
        last_raw_positions[0] = raw_pos1
        activity_detected = True

    sw1_val = sw1.value
    if sw1_val != last_sw_states[0]:
        if not sw1_val: press_action_physical(key_mapping[3][2]); activity_detected = True
        else: release_action_physical(key_mapping[3][2])
        last_sw_states[0] = sw1_val

    raw_pos2 = enc2.position
    if raw_pos2 != last_raw_positions[1]:
        delta2 = raw_pos2 - last_raw_positions[1]
        for _ in range(abs(delta2)):
            act = key_mapping[3][4] if delta2 > 0 else key_mapping[3][3]
            press_action_physical(act); release_action_physical(act)
        last_raw_positions[1] = raw_pos2
        activity_detected = True

    sw2_val = sw2.value
    if sw2_val != last_sw_states[1]:
        if not sw2_val: press_action_physical(key_mapping[3][5]); activity_detected = True
        else: release_action_physical(key_mapping[3][5])
        last_sw_states[1] = sw2_val

    if activity_detected:
        last_activity_time = current_time
        is_idle = False
        draw_active_dashboard()
    elif refresh_ui and not is_idle:
        draw_active_dashboard()

    # --- SCREENSAVER RENDERING ---
    if (current_time - last_activity_time) > IDLE_TIMEOUT_MS:
        if not is_idle:
            is_idle = True

        if (current_time - last_anim_frame_time) > 50: 
            last_anim_frame_time = current_time
            anim_frame_counter += 1
            oled.fill(0)
            
            if idle_animation == "matrix":
                for i in range(NUM_DROPS):
                    matrix_y[i] += matrix_speed[i]
                    if matrix_y[i] > 64:
                        matrix_y[i] = random.randint(-20, 0)
                        matrix_x[i] = random.randint(0, 120)
                    oled.line(matrix_x[i], max(0, matrix_y[i]-8), matrix_x[i], min(63, matrix_y[i]), 1)
                    
            elif idle_animation == "starwars":
                for i in range(NUM_STARS):
                    star_x[i] -= star_layer[i]
                    if star_x[i] < 0:
                        star_x[i] = 128; star_y[i] = random.randint(0, 63)
                    oled.pixel(star_x[i], star_y[i], 1)
                tie_x -= 2
                if tie_x < -20: tie_x = 135; tie_y = random.randint(32, 52)
                draw_buffer_bitmap(TIE_FIGHTER, tie_x, tie_y, 8, 8)
                draw_buffer_bitmap(STAR_DESTROYER, 12, 6, 32, 14)

            elif idle_animation == "custom_gif" and custom_gif_frames:
                current_frame_index = anim_frame_counter % len(custom_gif_frames)
                draw_image_hex = custom_gif_frames[current_frame_index]
                draw_hex_string_bitmap(draw_image_hex, gif_w, gif_h)

            elif idle_animation == "off":
                pass

            oled.show()

    time.sleep(0.001)