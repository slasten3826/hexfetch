#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HEXFETCH v2.5 (ProcessLang Edition)
RESTORED: The cool ASCII Block Logo.
FEATURES: Config, Options Menu, Smart Wrap.
"""

import sys
import os
import time
import json
import random
import hashlib
import argparse
import unicodedata
import glob

# Пытаемся импортировать curses
try:
    import curses
except ImportError:
    pass

# ==============================================================================
# [ BLOCK: CONFIGURATION ]
# ==============================================================================
# START CONFIG
VERSION = "v2.5"

# Символы линий
YANG_CHAR = "━"
YIN_CHAR  = "━"

# --- НАСТРОЙКИ ВНЕШНЕГО ВИДА ---
CLI_WIDTH = 12
CLI_GAP   = 4
TUI_WIDTH = 20
TUI_GAP   = 6

# Операторы ProcessLang
TRIGRAM_NAMES = {
    (1,1,1): "CONNECT",  (0,0,0): "DISSOLVE",
    (1,0,0): "CHOOSE",   (0,1,0): "ENCODE",
    (0,0,1): "LOGIC",    (0,1,1): "OBSERVE",
    (1,0,1): "CYCLE",    (1,1,0): "RUNTIME",
}

# Таблица King Wen
BIN_TO_ID = {
    "111111": "1",  "000000": "2",  "100010": "3",  "010001": "4",
    "111010": "5",  "010111": "6",  "010000": "7",  "000010": "8",
    "111011": "9",  "110111": "10", "111000": "11", "000111": "12",
    "101111": "13", "111101": "14", "001000": "15", "000100": "16",
    "100110": "17", "011001": "18", "110000": "19", "000011": "20",
    "100101": "21", "101001": "22", "000001": "23", "100000": "24",
    "100111": "25", "111001": "26", "100001": "27", "011110": "28",
    "010010": "29", "101101": "30", "001110": "31", "011100": "32",
    "001111": "33", "111100": "34", "000101": "35", "101000": "36",
    "101011": "37", "110101": "38", "001010": "39", "010100": "40",
    "110001": "41", "100011": "42", "111110": "43", "011111": "44",
    "000110": "45", "011000": "46", "010110": "47", "011010": "48",
    "101110": "49", "011101": "50", "100100": "51", "001001": "52",
    "001011": "53", "110100": "54", "101100": "55", "001101": "56",
    "011011": "57", "110110": "58", "010011": "59", "110010": "60",
    "110011": "61", "001100": "62", "101010": "63", "010101": "64"
}
# END CONFIG

# ==============================================================================
# [ BLOCK: CONFIG MANAGER ]
# ==============================================================================
# START CONFIG MGR
CONFIG_DIR = os.path.expanduser("~/.config/hexfetch")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def load_user_config():
    if not os.path.exists(CONFIG_FILE): return {}
    try:
        with open(CONFIG_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_user_config(config_data):
    if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        with open(CONFIG_FILE, 'w') as f: json.dump(config_data, f, indent=2)
        return True
    except: return False

def get_available_decks():
    decks = {"default": "Standard Deck (data.json)"}
    search_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__))),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks"),
        "/usr/share/hexfetch", "/usr/share/hexfetch/decks",
        os.path.expanduser("~/.config/hexfetch"),
    ]
    for path in search_paths:
        if not os.path.exists(path): continue
        files = glob.glob(os.path.join(path, "data_*.json"))
        for f in files:
            filename = os.path.basename(f)
            deck_id = filename.replace("data_", "").replace(".json", "")
            decks[deck_id] = f"{deck_id.upper()} Deck ({filename})"
    return decks
# END CONFIG MGR

# ==============================================================================
# [ BLOCK: LOGIC & DATA ]
# ==============================================================================
def find_data_file(deck_name=None):
    if not deck_name:
        conf = load_user_config()
        deck_name = conf.get("default_deck")
    filename = "data.json"
    if deck_name and deck_name != "default": filename = f"data_{deck_name}.json"
    search_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__))),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks"),
        "/usr/share/hexfetch", "/usr/share/hexfetch/decks",
        os.path.expanduser("~/.config/hexfetch"),
    ]
    for path in search_paths:
        full_path = os.path.join(path, filename)
        if os.path.exists(full_path): return full_path
    if deck_name: return find_data_file(None)
    return None

def load_db(deck_name=None):
    path = find_data_file(deck_name)
    default_data = {
        "ui": {"prompt_running": ">> FLUX RUNNING <<", "prompt_paused": "[SPACE] RESTART [Q] QUIT", "header_prefix": "HEXAGRAM:"},
        "error": True
    }
    if not path: return default_data
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f); data["error"] = False; return data
    except: return default_data

def get_entropy():
    try:
        seed = os.urandom(32) + str(time.time_ns()).encode()
        h = hashlib.sha256(seed).digest()
        val = int.from_bytes(h[:1], 'big')
        return [(val >> i) & 1 for i in range(6)]
    except: return [random.randint(0, 1) for _ in range(6)]

def cast_hexagram(lines=None):
    if lines is None: lines = get_entropy()
    binary_str = "".join(str(b) for b in reversed(lines))
    hex_id = BIN_TO_ID.get(binary_str, "?")
    return {"lines": lines, "id": hex_id,
            "upper_tri": TRIGRAM_NAMES.get(tuple(lines[3:6]), "UNK"),
            "lower_tri": TRIGRAM_NAMES.get(tuple(lines[0:3]), "UNK")}

def get_char_width(char):
    if unicodedata.east_asian_width(char) in ('W', 'F'): return 2
    return 1

def smart_wrap(text, width):
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph: lines.append(""); continue
        current_line = ""; current_width = 0; last_space_idx = -1
        i = 0
        while i < len(paragraph):
            char = paragraph[i]; char_w = get_char_width(char)
            if current_width + char_w > width:
                if last_space_idx != -1 and char_w == 1:
                    lines.append(current_line[:last_space_idx])
                    current_line = current_line[last_space_idx+1:] + char
                    current_width = sum(get_char_width(c) for c in current_line)
                    last_space_idx = -1
                else:
                    lines.append(current_line)
                    current_line = char; current_width = char_w; last_space_idx = -1
            else:
                if char == ' ': last_space_idx = len(current_line)
                current_line += char; current_width += char_w
            i += 1
        if current_line: lines.append(current_line)
    return lines

# ==============================================================================
# [ BLOCK: OPTIONS MENU ]
# ==============================================================================
def run_options_menu(stdscr):
    curses.curs_set(0)
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

    decks = get_available_decks()
    deck_ids = list(decks.keys())
    conf = load_user_config()
    current_default = conf.get("default_deck", "default")
    selection_idx = 0
    if current_default in deck_ids: selection_idx = deck_ids.index(current_default)

    while True:
        stdscr.erase(); h, w = stdscr.getmaxyx()
        box_w = 50; box_h = len(deck_ids) + 6
        start_y = max(0, (h // 2) - (box_h // 2))
        start_x = max(0, (w // 2) - (box_w // 2))

        stdscr.addstr(start_y, start_x + (box_w - 22)//2, " HEXFETCH CONFIGURATION ", curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(start_y + 2, start_x + 2, "Select Default Deck:", curses.color_pair(2))

        for i, deck_id in enumerate(deck_ids):
            label = decks[deck_id]; is_sel = (i == selection_idx); is_act = (deck_id == current_default)
            prefix = " [*] " if is_act else " [ ] "
            style = (curses.color_pair(3) | curses.A_BOLD | curses.A_REVERSE) if is_sel else curses.color_pair(2)
            line_str = f"{prefix}{label}"
            if len(line_str) > box_w - 4: line_str = line_str[:box_w-7] + "..."
            stdscr.addstr(start_y + 4 + i, start_x + 2, line_str, style)

        stdscr.addstr(start_y + box_h - 1, start_x + (box_w - 30)//2, "[ENTER] Save & Exit   [Q] Cancel", curses.color_pair(1))

        key = stdscr.getch()
        if key == ord('q'): return
        elif key == curses.KEY_UP: selection_idx = max(0, selection_idx - 1)
        elif key == curses.KEY_DOWN: selection_idx = min(len(deck_ids) - 1, selection_idx + 1)
        elif key == 10:
            save_user_config({"default_deck": deck_ids[selection_idx]})
            stdscr.addstr(start_y + box_h + 1, start_x + (box_w - 8)//2, " SAVED! ", curses.color_pair(3) | curses.A_BOLD)
            stdscr.refresh(); time.sleep(1); return

# ==============================================================================
# [ BLOCK: CLI MODE ]
# ==============================================================================
def run_cli_mode(db):
    result = cast_hexagram()
    hex_data = db.get(result['id'], {})
    name = hex_data.get('name', 'UNKNOWN'); meaning = hex_data.get('meaning', 'Data missing.')
    print(f"\n \033[96mHEXAGRAM #{result['id']}: {name}\033[0m")
    print("-" * 30)
    for i in range(5, -1, -1):
        if result['lines'][i] == 1: print(f"   {YANG_CHAR * CLI_WIDTH} ")
        else: sl = (CLI_WIDTH - CLI_GAP) // 2; print(f"   {YIN_CHAR * sl}{' '*CLI_GAP}{YIN_CHAR * sl} ")
    print("-" * 30)
    print(f" Upper: {result['upper_tri']}\n Lower: {result['lower_tri']}")
    print("-" * 30)
    print(meaning)
    print("-" * 30)

# ==============================================================================
# [ BLOCK: TUI MODE ]
# ==============================================================================
def draw_splash_screen(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(False)
    # RESTORED BIG LOGO
    logo = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║                                                              ║",
        "║   █   █  █████  ██   ██  █████  █████  █████  █████  █   █   ║",
        "║   █   █  █       ██ ██   █      █        █    █      █   █   ║",
        "║   █████  ████     ███    ████   ████     █    █      █████   ║",
        "║   █   █  █       ██ ██   █      █        █    █      █   █   ║",
        "║   █   █  █████  ██   ██  █      █████    █    █████  █   █   ║",
        "║                                                              ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║         [  P R O C E S S L A N G   O R A C L E  ]            ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║                                                              ║",
        "║   COMMANDS:                                                  ║",
        "║                                                              ║",
        "║   [ SPACE ] ....... CAST HEXAGRAM / PAUSE STREAM             ║",
        "║   [ ↑ / ↓ ] ....... SCROLL INTERPRETATION                    ║",
        "║   [   Q   ] ....... TERMINATE SESSION                        ║",
        f"║                                                    {VERSION}      ║",
        "╚══════════════════════════════════════════════════════════════╝",
    ]
    prompt = "[ PRESS ANY KEY TO INITIALIZE ]"
    h, w = stdscr.getmaxyx()
    start_y = max(0, (h // 2) - (len(logo) // 2))
    stdscr.clear()

    if curses.has_colors():
        c_frm = curses.color_pair(5); c_txt = curses.color_pair(2)
        c_logo = curses.color_pair(1) | curses.A_BOLD
        c_keys = curses.color_pair(4) | curses.A_BOLD
        c_ver = curses.color_pair(3)
    else: c_frm = c_txt = c_logo = c_keys = c_ver = curses.A_NORMAL

    for i, line in enumerate(logo):
        start_x = max(0, (w // 2) - (len(line) // 2))
        for j, char in enumerate(line):
            color = c_txt
            if char in "╔╗╚╝║═╠╣": color = c_frm
            elif char in "█": color = c_logo
            elif char in "[]": color = c_keys
            elif VERSION in line and j > len(line) - 10: color = c_ver
            try: stdscr.addch(start_y + i, start_x + j, char, color)
            except: pass

    try: stdscr.addstr(start_y + len(logo) + 1, max(0, (w // 2) - (len(prompt) // 2)), prompt, c_txt | curses.A_BLINK)
    except: pass
    stdscr.refresh(); stdscr.getch(); stdscr.clear()

def draw_hexagram(stdscr, y, x, lines, color_pair, width, gap):
    current_y = y
    for bit in reversed(lines):
        if bit == 1: line_str = YANG_CHAR * width
        else: sl = (width - gap) // 2; line_str = (YIN_CHAR * sl) + (" " * gap) + (YIN_CHAR * sl)
        stdscr.addstr(current_y, x, line_str, color_pair | curses.A_BOLD)
        current_y += 2

def run_tui_mode(stdscr, db):
    curses.curs_set(0)
    if curses.has_colors():
        curses.start_color()
        for i, c in enumerate([curses.COLOR_CYAN, curses.COLOR_WHITE, curses.COLOR_MAGENTA, curses.COLOR_YELLOW, curses.COLOR_BLUE], 1):
            curses.init_pair(i, c, curses.COLOR_BLACK)

    draw_splash_screen(stdscr)
    stdscr.nodelay(True); stdscr.timeout(0)
    ui_conf = db.get("ui", {})
    paused = False; current_lines = [0]*6; current_info = {}; current_hex_id = "?"
    scroll_offset = 0; wrapped_text = []

    while True:
        try: key = stdscr.getch()
        except: key = -1
        if key == ord('q') or key == 27: break
        elif key == ord(' '):
            paused = not paused
            if not paused: scroll_offset = 0; wrapped_text = []

        if paused:
            if key == curses.KEY_UP: scroll_offset = max(0, scroll_offset - 1)
            elif key == curses.KEY_DOWN:
                if len(wrapped_text) > 0: scroll_offset = min(len(wrapped_text) - 5, scroll_offset + 1)
            elif key == curses.KEY_PPAGE: scroll_offset = max(0, scroll_offset - 10)
            elif key == curses.KEY_NPAGE: scroll_offset = max(0, scroll_offset + 10)

        if not paused:
            current_lines = get_entropy()
            res = cast_hexagram(current_lines)
            current_hex_id = res["id"]
            hex_data = db.get(current_hex_id)
            current_info = hex_data if hex_data else {"name": "UNKNOWN", "meaning": "Data missing."}

        stdscr.erase(); h, w = stdscr.getmaxyx()
        hex_y = max(0, (h // 2) - 5 - 2); hex_x = 4
        draw_hexagram(stdscr, hex_y, hex_x, current_lines, curses.color_pair(1), TUI_WIDTH, TUI_GAP)

        text_x = hex_x + TUI_WIDTH + 6; text_w = w - text_x - 2

        if not paused:
            # RUNNING
            stdscr.addstr(hex_y, text_x, f"▲ {TRIGRAM_NAMES.get(tuple(current_lines[3:6]), '')}", curses.color_pair(5))
            stdscr.addstr(hex_y + 10, text_x, f"▼ {TRIGRAM_NAMES.get(tuple(current_lines[0:3]), '')}", curses.color_pair(5))
            prompt = ui_conf.get("prompt_running", ">> FLUX RUNNING <<")
            try: stdscr.addstr(h - 2, max(0, (w - len(prompt))//2), prompt, curses.color_pair(3) | curses.A_BLINK)
            except: pass
        else:
            # PAUSED
            title = f"HEXAGRAM #{current_hex_id}: {current_info.get('name', 'UNK')}"
            stdscr.addstr(hex_y, text_x, title, curses.color_pair(1) | curses.A_BOLD)
            stdscr.addstr(hex_y + 2, text_x, f"Up: {TRIGRAM_NAMES.get(tuple(current_lines[3:6]), 'UNK')}", curses.color_pair(2))
            stdscr.addstr(hex_y + 3, text_x, f"Low: {TRIGRAM_NAMES.get(tuple(current_lines[0:3]), 'UNK')}", curses.color_pair(2))

            if not wrapped_text: wrapped_text = smart_wrap(current_info.get('meaning', 'No text.'), text_w)

            view_y = hex_y + 5; max_lines = h - view_y - 4
            if max_lines > 0:
                for i, line in enumerate(wrapped_text[scroll_offset : scroll_offset + max_lines]):
                    try: stdscr.addstr(view_y + i, text_x, line, curses.color_pair(2))
                    except: pass
                if len(wrapped_text) > max_lines:
                    sb = f"[ SCROLL {int((scroll_offset / (len(wrapped_text) - max_lines)) * 100)}% ]"
                    try: stdscr.addstr(view_y - 1, w - len(sb) - 2, sb, curses.color_pair(4))
                    except: pass

            prompt = ui_conf.get("prompt_paused", "[SPACE] AGAIN")
            try: stdscr.addstr(h - 2, max(0, (w - len(prompt))//2), prompt, curses.color_pair(3) | curses.A_BOLD)
            except: pass

        stdscr.refresh()
        if paused: time.sleep(0.05)

# ==============================================================================
# [ BLOCK: MAIN ]
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HexFetch: ProcessLang Oracle")
    parser.add_argument("-t", "--text", action="store_true", help="Run in text mode (CLI)")
    parser.add_argument("-d", "--deck", type=str, help="Temporarily use specific deck")
    parser.add_argument("-o", "--options", action="store_true", help="Open configuration menu")
    args = parser.parse_args()

    if args.options:
        try: curses.wrapper(run_options_menu)
        except Exception as e: print(f"Error in menu: {e}")
        sys.exit(0)

    db = load_db(args.deck)

    if args.text: run_cli_mode(db)
    else:
        try: curses.wrapper(lambda stdscr: run_tui_mode(stdscr, db))
        except KeyboardInterrupt: pass
        except Exception as e:
            try: curses.endwin()
            except: pass
            print(f"CRITICAL ERROR: {e}"); import traceback; traceback.print_exc()
