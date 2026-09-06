import os
import json
import serial
import serial.tools.list_ports
from flask import Flask, render_template, request, jsonify, render_template_string

app = Flask(__name__)

# --- AUTOMATIC DRIVE DETECTION ---
PICO_DRIVE = "E:/"
FALLBACK_CONFIG = "config_backup.json"

def get_config_path():
    if os.path.exists(PICO_DRIVE):
        return os.path.join(PICO_DRIVE, "config.json")
    return FALLBACK_CONFIG

DEFAULT_MAP = {
    "matrix": [
        ["MOUSE_LEFT", "A", "MOUSE_CLICK"],
        ["W", "S", "Space"],
        ["MOUSE_RIGHT", "D", "Ctrl"],
        ["VOL_DOWN", "VOL_UP", "MUTE", "SCROLL_DOWN", "SCROLL_UP", "MOUSE_CLICK"]
    ],
    "idle_timeout_min": 2,
    "idle_animation": "matrix",
    "custom_line1": "3vKRM",
    "custom_line2": "READY"
}

def load_config():
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return DEFAULT_MAP
    try:
        with open(config_path, 'r') as f:
            cfg = json.load(f)
            if "matrix" not in cfg:
                cfg["matrix"] = DEFAULT_MAP["matrix"]
            if "custom_line1" not in cfg:
                cfg["custom_line1"] = "3vKRM"
            if "custom_line2" not in cfg:
                cfg["custom_line2"] = "READY"
            return cfg
    except Exception:
        return DEFAULT_MAP

def save_config(cfg):
    config_path = get_config_path()
    try:
        with open(config_path, 'w') as f:
            json.dump(cfg, f, indent=4)
        return True
    except Exception:
        return False

def send_serial_reload_signal():
    """Finds the Raspberry Pi Pico serial port and pushes an explicit reload tag."""
    try:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # CircuitPython boards typically present under these description signatures
            if "CircuitPython" in port.description or "Raspberry Pi" in port.description or "Pico" in port.description:
                with serial.Serial(port.device, 115200, timeout=0.5) as ser:
                    ser.write(b"[RELOAD]\n")
                return True
    except Exception as e:
        print(f"Serial communication interface event warning: {e}")
    return False

# --- ENGINE INTERFACE STYLING BLOCKS ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Macropad Studio Pro</title>
    <style>
        body { 
            background-color: #0b0f17; 
            color: #8fa0b5; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0; 
            padding: 25px; 
            display: flex; 
            justify-content: center;
            align-items: flex-start;
        }
        
        .workspace-container {
            display: grid;
            grid-template-columns: 980px 400px;
            gap: 24px;
            max-width: 1440px;
            width: 100%;
        }

        .studio-card {
            background-color: #111622;
            border-radius: 24px;
            padding: 35px 40px;
            box-shadow: 0 24px 70px rgba(0,0,0,0.7);
            border: 1px solid #1a2232;
            box-sizing: border-box;
        }
        
        .macro-options-tool {
            background-color: #111622;
            border-radius: 24px;
            padding: 30px 24px;
            box-shadow: 0 24px 70px rgba(0,0,0,0.7);
            border: 1px solid #1a2232;
            box-sizing: border-box;
            position: sticky;
            top: 25px;
            display: flex;
            flex-direction: column;
            height: 780px;
        }

        .header-section {
            text-align: center;
            margin-bottom: 35px;
        }
        .header-section h1 {
            color: #ffffff;
            margin: 0;
            font-size: 30px;
            font-weight: 700;
            letter-spacing: 0.5px;
            }
        .header-section p {
            color: #526882;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            margin: 6px 0 0 0;
            text-transform: uppercase;
        }
        
        .top-modules-row {
            display: grid;
            grid-template-columns: 1.1fr 1.1fr 0.8fr;
            gap: 16px;
            margin-bottom: 35px;
            align-items: stretch;
        }
        .module-panel {
            background-color: #171f2c;
            border-radius: 16px;
            padding: 16px;
            border: 1px solid #222d3e;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            box-sizing: border-box;
        }
        .panel-headline {
            color: #ffffff;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 15px;
            width: 100%;
            text-align: center;
        }
        .hardware-dial-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            width: 100%;
        }
        .side-val-field {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 75px;
            gap: 4px;
        }
        .side-val-field label {
            font-size: 9px;
            font-weight: 800;
            color: #526882;
            text-transform: uppercase;
        }
        .side-val-field input {
            width: 100%;
            background-color: #0d121c;
            border: 1px solid #28354a;
            border-radius: 6px;
            padding: 6px 4px;
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            text-align: center;
            box-sizing: border-box;
        }
        
        .knob-wheel {
            width: 95px;
            height: 95px;
            border-radius: 50%;
            background: radial-gradient(circle, #253145 0%, #151c27 80%);
            border: 4px solid #1d2636;
            box-shadow: inset 0 4px 10px rgba(0,0,0,0.6), 0 6px 15px rgba(0,0,0,0.5);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            gap: 2px;
        }
        .knob-wheel::before {
            content: '';
            position: absolute;
            top: 6px;
            width: 3px;
            height: 8px;
            background-color: #526882;
            border-radius: 2px;
        }
        .knob-click-label {
            font-size: 9px;
            font-weight: 800;
            color: #526882;
            text-transform: uppercase;
            margin-top: 8px;
        }
        .knob-center-input {
            background: transparent;
            border: none;
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            text-align: center;
            width: 80px;
        }
        .knob-center-input:focus, .side-val-field input:focus, .macro-key-node input:focus {
            outline: none;
            border-color: #38bdf8;
            color: #38bdf8;
        }

        .oled-system-monitor {
            background-color: #070b11;
            border-radius: 12px;
            padding: 14px;
            width: 100%;
            height: 106px;
            border: 1px solid #1e2836;
            box-sizing: border-box;
            font-family: SFMono-Regular, Consolas, monospace;
            font-size: 11px;
            line-height: 1.5;
        }
        .oled-row-blue { color: #38bdf8; }
        .oled-row-dim { color: #384a61; }

        .grid-header-label {
            font-size: 11px;
            font-weight: 800;
            color: #00f0ff;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 20px;
            border-bottom: 1px solid #1f293a;
            padding-bottom: 10px;
            width: 100%;
        }
        .grid-matrix-layout {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 35px;
        }
        .macro-key-node {
            background-color: #171f2c;
            border: 1px solid #222d3e;
            border-radius: 14px;
            padding: 14px 16px;
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }
        .macro-key-node:focus-within {
            border-color: #38bdf8;
            box-shadow: 0 0 12px rgba(56,189,248,0.15);
        }
        .key-meta-label {
            font-size: 10px;
            font-weight: 700;
            color: #526882;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .input-inline-flex {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
        }
        .input-inline-flex input {
            background: transparent;
            border: none;
            color: #ffffff;
            font-size: 14px;
            font-weight: 700;
            width: 75%;
            padding: 0;
        }
        
        .rec-tag-indicator {
            font-size: 9px;
            font-weight: 900;
            color: #38bdf8;
            background-color: rgba(56,189,248,0.1);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 2px 6px;
            border-radius: 4px;
            cursor: pointer;
            user-select: none;
            transition: all 0.15s ease;
            border: 1px solid rgba(56,189,248,0.2);
        }
        .rec-tag-indicator:hover {
            background-color: #38bdf8;
            color: #070b11;
        }
        .rec-tag-indicator.recording-active {
            background-color: #ef4444 !important;
            color: #ffffff !important;
            border-color: #f87171 !important;
            animation: pulse-border 1.5s infinite;
        }
        @keyframes pulse-border {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .twin-config-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 35px;
        }
        .config-block-card {
            background-color: #171f2c;
            border-radius: 16px;
            padding: 22px 20px;
            border: 1px solid #222d3e;
        }
        .config-inline-fields {
            display: flex;
            gap: 15px;
        }
        .field-flex-cell {
            flex: 1;
        }
        .config-block-card label {
            display: block;
            font-size: 11px;
            font-weight: 700;
            color: #526882;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        .config-block-card select, .config-block-card input {
            width: 100%;
            background-color: #0d121c;
            border: 1px solid #28354a;
            border-radius: 8px;
            padding: 12px;
            color: #ffffff;
            font-size: 13px;
            font-weight: 600;
            box-sizing: border-box;
        }

        .master-sync-btn {
            background-color: #38bdf8;
            color: #070b11;
            border: none;
            width: 100%;
            padding: 16px;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 4px 25px rgba(56,189,248,0.25);
            transition: all 0.2s ease;
        }
        .master-sync-btn:hover {
            background-color: #58cafc;
        }
        .toast-status-log {
            text-align: center;
            margin-top: 15px;
            font-size: 12px;
            font-weight: 700;
            color: #00f0ff;
            min-height: 16px;
        }

        .tool-title {
            font-size: 16px;
            font-weight: 800;
            color: #00f0ff;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .tool-desc {
            font-size: 11px;
            line-height: 1.4;
            color: #526882;
            margin-bottom: 20px;
        }
        
        .tabs-menu-header {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 6px;
            margin-bottom: 16px;
        }
        .tabs-menu-header button {
            background-color: #171f2c;
            border: 1px solid #222d3e;
            color: #8fa0b5;
            padding: 8px 4px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .tabs-menu-header button.active-tab {
            background-color: rgba(56,189,248,0.15);
            border-color: #38bdf8;
            color: #ffffff;
        }
        
        .tab-view-pane {
            display: none;
            flex-direction: column;
            overflow-y: auto;
            flex: 1;
            padding-right: 4px;
        }
        .tab-view-pane.active-pane {
            display: flex;
        }
        .tab-view-pane::-webkit-scrollbar {
            width: 4px;
        }
        .tab-view-pane::-webkit-scrollbar-thumb {
            background: #222d3e;
            border-radius: 2px;
        }
        
        .macro-buttons-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        .macro-option-btn {
            background-color: #171f2c;
            border: 1px solid #222d3e;
            color: #ffffff;
            border-radius: 6px;
            padding: 10px 8px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            transition: all 0.1s ease;
        }
        .macro-option-btn:hover {
            border-color: #38bdf8;
            background-color: #1e293b;
        }
    </style>
</head>
<body>

    <div class="workspace-container">
        
        <div class="studio-card">
            <div class="header-section">
                <h1>Macropad Studio</h1>
                <p>Hardware Mapping & Macro Suite</p>
            </div>

            <div class="top-modules-row">
                <div class="module-panel">
                    <div class="panel-headline">Encoder Knob 2</div>
                    <div class="hardware-dial-row">
                        <div class="side-val-field">
                            <label>CCW</label>
                            <input type="text" id="node-3-3" onfocus="setActiveField(3,3)">
                            <span class="rec-tag-indicator" id="rec-3-3" onclick="triggerRecSelection(3,3)">Rec</span>
                        </div>
                        <div class="knob-wheel">
                            <div class="knob-click-label">Click</div>
                            <input type="text" class="knob-center-input" id="node-3-5" onfocus="setActiveField(3,5)">
                            <span class="rec-tag-indicator" id="rec-3-5" onclick="triggerRecSelection(3,5)">Rec</span>
                        </div>
                        <div class="side-val-field">
                            <label>CW</label>
                            <input type="text" id="node-3-4" onfocus="setActiveField(3,4)">
                            <span class="rec-tag-indicator" id="rec-3-4" onclick="triggerRecSelection(3,4)">Rec</span>
                        </div>
                    </div>
                </div>

                <div class="module-panel">
                    <div class="panel-headline">Encoder Knob 1</div>
                    <div class="hardware-dial-row">
                        <div class="side-val-field">
                            <label>CCW</label>
                            <input type="text" id="node-3-0" onfocus="setActiveField(3,0)">
                            <span class="rec-tag-indicator" id="rec-3-0" onclick="triggerRecSelection(3,0)">Rec</span>
                        </div>
                        <div class="knob-wheel">
                            <div class="knob-click-label">Click</div>
                            <input type="text" class="knob-center-input" id="node-3-2" onfocus="setActiveField(3,2)">
                            <span class="rec-tag-indicator" id="rec-3-2" onclick="triggerRecSelection(3,2)">Rec</span>
                        </div>
                        <div class="side-val-field">
                            <label>CW</label>
                            <input type="text" id="node-3-1" onfocus="setActiveField(3,1)">
                            <span class="rec-tag-indicator" id="rec-3-1" onclick="triggerRecSelection(3,1)">Rec</span>
                        </div>
                    </div>
                </div>

                <div class="module-panel" style="align-items:flex-start;">
                    <div class="panel-headline" style="text-align:left; color:#38bdf8;">SSD1306 OLED System</div>
                    <div class="oled-system-monitor">
                        <div class="oled-row-blue">&gt; Macropad online</div>
                        <div class="oled-row-blue">&gt; USB HID active</div>
                        <div class="oled-row-blue">&gt; Encoder Grid Layout Swapped</div>
                        <div class="oled-row-dim">&gt; Ready for input...</div>
                    </div>
                </div>
            </div>

            <div class="grid-header-label">Tactile Key Matrix (3x3 Grid)</div>
            <div class="grid-matrix-layout">
                <div class="macro-key-node">
                    <div class="key-meta-label">Button R1 - C1</div>
                    <div class="input-inline-flex">
                        <input type="text" id="node-0-0" onfocus="setActiveField(0,0)">
                        <span class="rec-tag-indicator" id="rec-0-0" onclick="triggerRecSelection(0,0)">Rec</span>
                    </div>
                </div>
                <div class="macro-key-node">
                    <div class="key-meta-label">Button R1 - C2</div>
                    <div class="input-inline-flex">
                        <input type="text" id="node-0-1" onfocus="setActiveField(0,1)">
                        <span class="rec-tag-indicator" id="rec-0-1" onclick="triggerRecSelection(0,1)">Rec</span>
                    </div>
                </div>
                <div class="macro-key-node">
                    <div class="key-meta-label">Button R1 - C3</div>
                    <div class="input-inline-flex">
                        <input type="text" id="node-0-2" onfocus="setActiveField(0,2)">
                        <span class="rec-tag-indicator" id="rec-0-2" onclick="triggerRecSelection(0,2)">Rec</span>
                    </div>
                </div>

                <div class="macro-key-node">
                    <div class="key-meta-label">Button R2 - C1</div>
                    <div class="input-inline-flex">
                        <input type="text" id="node-1-0" onfocus="setActiveField(1,0)">
                        <span class="rec-tag-indicator" id="rec-1-0" onclick="triggerRecSelection(1,0)">Rec</span>
                    </div>
                </div>
                <div class="macro-key-node">
                    <div class="key-meta-label">Button R2 - C2</div>
                    <div class="input-inline-flex">
                        <input type="text" id="node-1-1" onfocus="setActiveField(1,1)">
                        <span class="rec-tag-indicator" id="rec-1-1" onclick="triggerRecSelection(1,1)">Rec</span>
                    </div>
                </div>
                <div class="macro-key-node">
                    <div class="key-meta-label">Button R2 - C3</div>
                    <div class="input-inline-flex">
                        <input type="text" id="node-1-2" onfocus="setActiveField(1,2)">
                        <span class="rec-tag-indicator" id="rec-1-2" onclick="triggerRecSelection(1,2)">Rec</span>
                    </div>
                </div>

                <div class="macro-key-node">
                    <div class="key-meta-label">Button R3 - C1</div>
                    <div class="input-inline-flex">
                        <input type="text" id="node-2-0" onfocus="setActiveField(2,0)">
                        <span class="rec-tag-indicator" id="rec-2-0" onclick="triggerRecSelection(2,0)">Rec</span>
                    </div>
                </div>
                <div class="macro-key-node">
                    <div class="key-meta-label">Button R3 - C2</div>
                    <div class="input-inline-flex">
                        <input type="text" id="node-2-1" onfocus="setActiveField(2,1)">
                        <span class="rec-tag-indicator" id="rec-2-1" onclick="triggerRecSelection(2,1)">Rec</span>
                    </div>
                </div>
                <div class="macro-key-node">
                    <div class="key-meta-label">Button R3 - C3</div>
                    <div class="input-inline-flex">
                        <input type="text" id="node-2-2" onfocus="setActiveField(2,2)">
                        <span class="rec-tag-indicator" id="rec-2-2" onclick="triggerRecSelection(2,2)">Rec</span>
                    </div>
                </div>
            </div>

            <div class="twin-config-container">
                <div class="config-block-card">
                    <div class="panel-headline" style="text-align:left; color:#00f0ff; margin-bottom:18px;">OLED Screen Sidebar Strings</div>
                    <div class="config-inline-fields">
                        <div class="field-flex-cell">
                            <label>Sidebar Line 1 (Max 8 Chars)</label>
                            <input type="text" id="sidebar-l1" maxlength="8" placeholder="3vKRM">
                        </div>
                        <div class="field-flex-cell">
                            <label>Sidebar Line 2 (Max 8 Chars)</label>
                            <input type="text" id="sidebar-l2" maxlength="8" placeholder="READY">
                        </div>
                    </div>
                </div>

                <div class="config-block-card">
                    <div class="panel-headline" style="text-align:left; color:#00f0ff; margin-bottom:18px;">Screensaver Timeout Monitor</div>
                    <div class="config-inline-fields">
                        <div class="field-flex-cell">
                            <label>Idle Delay Interval</label>
                            <select id="timeout-select">
                                <option value="1">1 Minute</option>
                                <option value="2">2 Minutes</option>
                                <option value="5">5 Minutes</option>
                                <option value="10">10 Minutes</option>
                            </select>
                        </div>
                        <div class="field-flex-cell">
                            <label>Idle Render Pattern</label>
                            <select id="anim-select">
                                <option value="matrix">Matrix Rain</option>
                                <option value="starwars">Star Wars Vector</option>
                                <option value="off">Display Sleep (Off)</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <button class="master-sync-btn" onclick="saveConfiguration()">Sync Settings To Flash Memory</button>
            <div class="toast-status-log" id="status-alert"></div>
        </div>

        <div class="macro-options-tool">
            <div class="tool-title">Macro Options Tool</div>
            <div class="tool-desc">Click an input box or a "Rec" button, then choose any value below or press your keys one-by-one to build a combination.</div>
            
            <div class="tabs-menu-header">
                <button class="active-tab" id="btn-tab-macros" onclick="switchMenuTab('macros')">Macros</button>
                <button id="btn-tab-system" onclick="switchMenuTab('system')">System Keys</button>
                <button id="btn-tab-letters" onclick="switchMenuTab('letters')">Letters</button>
                <button id="btn-tab-symbols" onclick="switchMenuTab('symbols')">Symbols</button>
                <button id="btn-tab-function" onclick="switchMenuTab('function')">Function</button>
                <button id="btn-tab-media" onclick="switchMenuTab('media')">Media</button>
                <button id="btn-tab-mouse" onclick="switchMenuTab('mouse')">Mouse</button>
            </div>
            
            <div class="tab-view-pane active-pane" id="pane-macros">
                <div class="macro-buttons-grid">
                    <button class="macro-option-btn" onclick="injectMacro('Ctrl+C')">Copy</button>
                    <button class="macro-option-btn" onclick="injectMacro('Ctrl+V')">Paste</button>
                    <button class="macro-option-btn" onclick="injectMacro('Ctrl+Z')">Undo</button>
                    <button class="macro-option-btn" onclick="injectMacro('Ctrl+A')">Select All</button>
                    <button class="macro-option-btn" onclick="injectMacro('Ctrl+T')">New Tab</button>
                    <button class="macro-option-btn" onclick="injectMacro('Ctrl+W')">Close Tab</button>
                    <button class="macro-option-btn" onclick="injectMacro('Ctrl+Shift+T')">Reopen Tab</button>
                    <button class="macro-option-btn" onclick="injectMacro('Alt+Tab')">Switch App</button>
                </div>
            </div>

            <div class="tab-view-pane" id="pane-system">
                <div class="macro-buttons-grid">
                    <button class="macro-option-btn" onclick="injectMacro('Escape')">Escape (ESC)</button>
                    <button class="macro-option-btn" onclick="injectMacro('Enter')">Enter</button>
                    <button class="macro-option-btn" onclick="injectMacro('Backspace')">Backspace</button>
                    <button class="macro-option-btn" onclick="injectMacro('Delete')">Delete</button>
                    <button class="macro-option-btn" onclick="injectMacro('Tab')">Tab</button>
                    <button class="macro-option-btn" onclick="injectMacro('Space')">Spacebar</button>
                    <button class="macro-option-btn" onclick="injectMacro('Ctrl')">Control (Ctrl)</button>
                    <button class="macro-option-btn" onclick="injectMacro('Shift')">Shift</button>
                    <button class="macro-option-btn" onclick="injectMacro('Alt')">Alt / Option</button>
                    <button class="macro-option-btn" onclick="injectMacro('GUI')">Windows / Command</button>
                    <button class="macro-option-btn" onclick="injectMacro('Caps_Lock')">Caps Lock</button>
                    <button class="macro-option-btn" onclick="injectMacro('Print_Screen')">Print Screen</button>
                    <button class="macro-option-btn" onclick="injectMacro('Home')">Home</button>
                    <button class="macro-option-btn" onclick="injectMacro('End')">End</button>
                    <button class="macro-option-btn" onclick="injectMacro('Page_Up')">Page Up</button>
                    <button class="macro-option-btn" onclick="injectMacro('Page_Down')">Page Down</button>
                </div>
            </div>

            <div class="tab-view-pane" id="pane-letters">
                <div class="macro-buttons-grid">
                    <script>
                        const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
                        alphabet.forEach(letter => {
                            document.write(`<button class="macro-option-btn" onclick="injectMacro('${letter}')">Key ${letter}</button>`);
                        });
                    </script>
                </div>
            </div>

            <div class="tab-view-pane" id="pane-symbols">
                <div class="macro-buttons-grid">
                    <script>
                        for(let i=0; i<=9; i++){
                            document.write(`<button class="macro-option-btn" onclick="injectMacro('${i}')">Num ${i}</button>`);
                        }
                    </script>
                    <button class="macro-option-btn" onclick="injectMacro('-')">Minus (-)</button>
                    <button class="macro-option-btn" onclick="injectMacro('=')">Equals (=)</button>
                    <button class="macro-option-btn" onclick="injectMacro('[')">Bracket [</button>
                    <button class="macro-option-btn" onclick="injectMacro(']')">Bracket ]</button>
                    <button class="macro-option-btn" onclick="injectMacro(';')">Semicolon ;</button>
                    <button class="macro-option-btn" onclick="injectMacro('/')">Slash /</button>
                </div>
            </div>

            <div class="tab-view-pane" id="pane-function">
                <div class="macro-buttons-grid">
                    <script>
                        for(let f=1; f<=12; f++){
                            document.write(`<button class="macro-option-btn" onclick="injectMacro('F${f}')">F${f}</button>`);
                        }
                    </script>
                </div>
            </div>

            <div class="tab-view-pane" id="pane-media">
                <div class="macro-buttons-grid">
                    <button class="macro-option-btn" onclick="injectMacro('VOL_UP')">Volume Up</button>
                    <button class="macro-option-btn" onclick="injectMacro('VOL_DOWN')">Volume Down</button>
                    <button class="macro-option-btn" onclick="injectMacro('MUTE')">Mute Audio</button>
                    <button class="macro-option-btn" onclick="injectMacro('PLAY_PAUSE')">Play / Pause</button>
                    <button class="macro-option-btn" onclick="injectMacro('MEDIA_NEXT')">Next Track</button>
                    <button class="macro-option-btn" onclick="injectMacro('MEDIA_PREV')">Prev Track</button>
                    <button class="macro-option-btn" onclick="injectMacro('BRIGHTNESS_UP')">Bright Up</button>
                    <button class="macro-option-btn" onclick="injectMacro('BRIGHTNESS_DOWN')">Bright Down</button>
                </div>
            </div>

            <div class="tab-view-pane" id="pane-mouse">
                <div class="macro-buttons-grid">
                    <button class="macro-option-btn" onclick="injectMacro('MOUSE_LEFT')">Mouse Left</button>
                    <button class="macro-option-btn" onclick="injectMacro('MOUSE_RIGHT')">Mouse Right</button>
                    <button class="macro-option-btn" onclick="injectMacro('MOUSE_CLICK')">Mouse Click</button>
                    <button class="macro-option-btn" onclick="injectMacro('MOUSE_UP')">Mouse Up</button>
                    <button class="macro-option-btn" onclick="injectMacro('MOUSE_DOWN')">Mouse Down</button>
                    <button class="macro-option-btn" onclick="injectMacro('SCROLL_UP')">Scroll Up</button>
                    <button class="macro-option-btn" onclick="injectMacro('SCROLL_DOWN')">Scroll Down</button>
                </div>
            </div>
        </div>

    </div>

    <script>
        let configData = {};
        let lastFocusedRow = 0;
        let lastFocusedCol = 0;
        let isRecordingSequence = false;

        function switchMenuTab(targetId) {
            document.querySelectorAll('.tabs-menu-header button').forEach(btn => {
                btn.classList.remove('active-tab');
            });
            document.querySelectorAll('.tab-view-pane').forEach(pane => {
                pane.classList.remove('active-pane');
            });
            
            document.getElementById(`btn-tab-${targetId}`).classList.add('active-tab');
            document.getElementById(`pane-${targetId}`).classList.add('active-pane');
        }

        function updateRecButtonUI() {
            document.querySelectorAll('.rec-tag-indicator').forEach(el => {
                el.classList.remove('recording-active');
            });
            const activeRecBtn = document.getElementById(`rec-${lastFocusedRow}-${lastFocusedCol}`);
            if (activeRecBtn) {
                activeRecBtn.classList.add('recording-active');
            }
        }

        function triggerRecSelection(row, col) {
            setActiveField(row, col);
            const targetInput = document.getElementById(`node-${row}-${col}`);
            if (targetInput) {
                targetInput.value = ""; 
                isRecordingSequence = true;
                targetInput.focus();
            }
        }

        function setActiveField(row, col) {
            lastFocusedRow = row;
            lastFocusedCol = col;
            updateRecButtonUI();
        }

        window.addEventListener('keydown', function(e) {
            if (document.activeElement && document.activeElement.id.startsWith('node-')) {
                
                e.preventDefault();
                e.stopPropagation();

                let coreKey = e.key;
                
                switch(coreKey) {
                    case "Control": coreKey = "Ctrl"; break;
                    case "Shift": coreKey = "Shift"; break;
                    case "Alt": coreKey = "Alt"; break;
                    case "Meta": coreKey = "GUI"; break;
                    case "Escape": coreKey = "Escape"; break;
                    case "Backspace": coreKey = "Backspace"; break;
                    case "Delete": coreKey = "Delete"; break;
                    case "Tab": coreKey = "Tab"; break;
                    case " ": coreKey = "Space"; break;
                    case "CapsLock": coreKey = "Caps_Lock"; break;
                    case "PrintScreen": coreKey = "Print_Screen"; break;
                    case "PageUp": coreKey = "Page_Up"; break;
                    case "PageDown": coreKey = "Page_Down"; break;
                    case "Home": coreKey = "Home"; break;
                    case "End": coreKey = "End"; break;
                    case "Enter": 
                        isRecordingSequence = false;
                        document.activeElement.blur();
                        return;
                    default:
                        if(coreKey.length === 1) {
                            coreKey = coreKey.toUpperCase();
                        }
                        break;
                }

                let currentVal = document.activeElement.value;
                if (currentVal === "") {
                    document.activeElement.value = coreKey;
                } else {
                    let existingKeys = currentVal.split("+");
                    if (!existingKeys.includes(coreKey)) {
                        document.activeElement.value = currentVal + "+" + coreKey;
                    }
                }
                
                pushValue(lastFocusedRow, lastFocusedCol);
            }
        }, true);

        async function fetchConfig() {
            const resp = await fetch('/get_config');
            configData = await resp.json();
            
            document.getElementById('timeout-select').value = configData.idle_timeout_min || 2;
            document.getElementById('anim-select').value = configData.idle_animation || 'matrix';
            document.getElementById('sidebar-l1').value = configData.custom_line1 || '3vKRM';
            document.getElementById('sidebar-l2').value = configData.custom_line2 || 'READY';
            
            for (let r = 0; r < 4; r++) {
                let colsLimit = (r === 3) ? 6 : 3;
                for (let c = 0; c < colsLimit; c++) {
                    const el = document.getElementById(`node-${r}-${c}`);
                    if (el && configData.matrix[r] && configData.matrix[r][c] !== undefined) {
                        el.value = configData.matrix[r][c];
                    }
                }
            }
            updateRecButtonUI();
        }

        function injectMacro(macroString) {
            const el = document.getElementById(`node-${lastFocusedRow}-${lastFocusedCol}`);
            if (el) {
                el.value = macroString;
                pushValue(lastFocusedRow, lastFocusedCol);
                el.focus();
            }
        }

        function pushValue(row, col) {
            const val = document.getElementById(`node-${row}-${col}`).value;
            if(!configData.matrix[row]) configData.matrix[row] = [];
            configData.matrix[row][col] = val;
        }

        async function saveConfiguration() {
            const alertBox = document.getElementById('status-alert');
            alertBox.innerText = "Syncing profiles to system storage...";
            
            configData.idle_timeout_min = parseInt(document.getElementById('timeout-select').value);
            configData.idle_animation = document.getElementById('anim-select').value;
            configData.custom_line1 = document.getElementById('sidebar-l1').value.toUpperCase();
            configData.custom_line2 = document.getElementById('sidebar-l2').value.toUpperCase();

            const resp = await fetch('/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData)
            });
            const res = await resp.json();
            if(res.success) {
                alertBox.innerText = "MacroPad Successfully Synchronized!";
                setTimeout(() => { alertBox.innerText = ""; }, 3500);
            } else {
                alertBox.innerText = "Write Failure: " + res.error;
            }
        }

        window.onload = fetchConfig;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_config')
def get_config():
    return jsonify(load_config())

@app.route('/save', methods=['POST'])
def save():
    try:
        new_data = request.json
        if not new_data or "matrix" not in new_data:
            return jsonify({"success": False, "error": "Invalid structure map context data"}), 400
            
        current_cfg = load_config()
        current_cfg["matrix"] = new_data["matrix"]
        current_cfg["idle_timeout_min"] = new_data.get("idle_timeout_min", 2)
        current_cfg["idle_animation"] = new_data.get("idle_animation", "matrix")
        current_cfg["custom_line1"] = new_data.get("custom_line1", "3vKRM").upper()
        current_cfg["custom_line2"] = new_data.get("custom_line2", "READY").upper()
        
        if save_config(current_cfg):
            # Tell the hardware directly over serial to reset its storage cache layer
            send_serial_reload_signal()
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Could not execute flash memory update action"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )
