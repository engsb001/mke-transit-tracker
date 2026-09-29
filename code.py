import os
import ssl
import wifi
import socketpool
import adafruit_requests
import time
import displayio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix

print("Getting Updates from MCTS Bus-time")

# --- Display Init ---
matrix = Matrix(width=128, height=32, bit_depth=3)
display = matrix.display
display.brightness = 1.0
display_font = bitmap_font.load_font("6x10.bdf")

# --- Config ---
api_key = os.getenv("BUS_API_KEY")
stop_id = os.getenv("BUS_STOP_ID")
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
base_url = "https://realtime.ridemcts.com/bustime/api/v3/"
prediction_url = (
    f"{base_url}getpredictions?key={api_key}&locale=en&format=json&stpid={stop_id}&tmres=s"
)

REFRESH_INTERVAL = 30       # seconds between API refreshes
CYCLE_INTERVAL = 7          # seconds between cycling the 3rd prediction slot
MAX_BACKOFF = 300           # cap retries at 5 minutes
DEST_MAX_CHARS = 15         # max chars before destination gets truncated
ROW_Y = [4, 15, 26]        # y-positions for the three prediction rows
requests = None  # initialized after wifi connect

#lookup table for MCTS Color numbers
DEFAULT_ROUTE_COLOR = 0xFFFFFF   
ROUTE_COLORS = {
    "11": 0x00B451,
    "12": 0x93D500,
    "14": 0x0055B8,
    "15": 0xFF8300,
    "18": 0x00B2E3,
    "19": 0xFFD600,
    "20": 0x93D500,
    "21": 0x00B2E3,
    "22": 0xEA0029,
    "24": 0xA87BC9,
    "28": 0xFFD600,
    "30": 0x00AF9A,
    "31": 0x00B451,
    "33": 0xFEBF10,
    "34": 0xA87BC9,
    "35": 0x863399,
    "51": 0xE50695,
    "52": 0x93D500,
    "53": 0x00B2E3,
    "54": 0xEA0029,
    "55": 0xEA0029,
    "56": 0x863399,
    "57": 0x0075C9,
    "58": 0xFF8300,
    "59": 0xA87BC9,
    "60": 0xFFD600,
    "63": 0x00B2E3,
    "66": 0x863399,
    "68": 0x93D500,
    "73": 0xA87BC9,
    "74": 0x00B451,
    "76": 0xB31983,
    "80": 0xE50695,
    "81": 0xFF8300,
    "82": 0x0075C9,
    "88": 0xFF8300,
    "92": 0xB31983,
    "BLU": 0x214080,
    "CN1": 0x389DD6,
    "GRE": 0x008D73,
    "HF1": 0x93D500,
    "HF2": 0x00AF9A,
    "PUR": 0x563896,
    "RED": 0xC23527,
    "RR1": 0x0066FF,
    "RR2": 0x0000CC,
    "RR3": 0x009900,
}
# Swapped GB channels
ROUTE_COLORS = {
    "11": 0x0051B4,
    "12": 0x9300D5,
    "14": 0x00B855,
    "15": 0xFF0083,
    "18": 0x00E3B2,
    "19": 0xFF00D6,
    "20": 0x9300D5,
    "21": 0x00E3B2,
    "22": 0xEA2900,
    "24": 0xA8C97B,
    "28": 0xFF00D6,
    "30": 0x009AAF,
    "31": 0x0051B4,
    "33": 0xFE10BF,
    "34": 0xA8C97B,
    "35": 0x869933,
    "51": 0xE59506,
    "52": 0x9300D5,
    "53": 0x00E3B2,
    "54": 0xEA2900,
    "55": 0xEA2900,
    "56": 0x869933,
    "57": 0x00C975,
    "58": 0xFF0083,
    "59": 0xA8C97B,
    "60": 0xFF00D6,
    "63": 0x00E3B2,
    "66": 0x869933,
    "68": 0x9300D5,
    "73": 0xA8C97B,
    "74": 0x0051B4,
    "76": 0xB38319,
    "80": 0xE59506,
    "81": 0xFF0083,
    "82": 0x00C975,
    "88": 0xFF0083,
    "92": 0xB38319,
    "BLU": 0x218040,
    "CN1": 0x38D69D,
    "GRE": 0x00738D,
    "HF1": 0x9300D5,
    "HF2": 0x009AAF,
    "PUR": 0x569638,
    "RED": 0xC22735,
    "RR1": 0x00FF66,
    "RR2": 0x00CC00,
    "RR3": 0x000099,
}



# --- Helpers ---

def truncate(text, max_chars):
    return text if len(text) <= max_chars else text[:max_chars - 1] + "~"


def make_error_group(line1, line2=None):
    """Show a red error message, optionally with a second line."""
    group = displayio.Group()
    group.append(label.Label(display_font, text=line1, color=0xFF0000, x=1, y=8))
    if line2:
        group.append(label.Label(display_font, text=line2, color=0xFF4400, x=1, y=20))
    return group


def make_prediction_row(prediction, y):
    """Return a list of Labels for a single prediction row."""
    route = prediction["rt"]
    destination = truncate(prediction["des"], DEST_MAX_CHARS)
    countdown = prediction["prdctdn"]

    route_color = ROUTE_COLORS.get(route, DEFAULT_ROUTE_COLOR)

    if countdown != "DUE":
        countdown = countdown + "m"

    return [
        label.Label(display_font, text=route, color=route_color, x=1, y=y),
        label.Label(display_font, text=destination, color=0x00FF00, x=19, y=y),
        label.Label(display_font, text=countdown, color=0x00BFFF, x=110, y=y),
    ]

def build_display_group(predictions, cycle_index):
    group = displayio.Group()

    if not predictions:
        group.append(label.Label(display_font, text="No predictions", color=0xFFFF00, x=1, y=14))
        return group

    # Rows 1 and 2 are always static (predictions 0 and 1)
    for i, y in enumerate(ROW_Y[:2]):
        if i < len(predictions):
            for lbl in make_prediction_row(predictions[i], y):
                group.append(lbl)

    # Row 3: static if exactly 3 predictions, cycles through extras if 4+
    if len(predictions) >= 3:
        extras = predictions[2:]
        cycle_pred = extras[cycle_index % len(extras)]
        for lbl in make_prediction_row(cycle_pred, ROW_Y[2]):
            group.append(lbl)

    return group

# --- WiFi ---

def connect_wifi():
    global requests
    backoff = 2
    while True:
        try:
            print(f"Connecting to {ssid}...")
            display.root_group = make_error_group(f"Connecting to", ssid[:16])
            wifi.radio.connect(ssid, password)
            pool = socketpool.SocketPool(wifi.radio)
            requests = adafruit_requests.Session(pool, ssl.create_default_context())
            print(f"Connected! IP: {wifi.radio.ipv4_address}")
            return
        except Exception as e:
            print(f"WiFi failed: {e}, retrying in {backoff}s")
            display.root_group = make_error_group("Cannot connect to", ssid[:16])
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)


# --- API Fetch ---

def fetch_predictions():
    """Fetch predictions, returns list or None on failure."""
    backoff = 2
    while True:
        try:
            response = requests.get(prediction_url)
            data = response.json()
            response.close()
            predictions = data["bustime-response"].get("prd", [])
            print(f"Got {len(predictions)} predictions")
            return predictions
        except Exception as e:
            print(f"API error: {e}, retrying in {backoff}s")
            display.root_group = make_error_group("Cannot reach", "MCTS Bus API")
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)
            # Check if wifi dropped and reconnect if needed
            if not wifi.radio.connected:
                connect_wifi()


# --- Main ---

connect_wifi()
predictions = fetch_predictions()
last_refresh = time.monotonic()
last_cycle = time.monotonic()
cycle_index = 0

display.root_group = build_display_group(predictions, cycle_index)

while True:
    now = time.monotonic()

    # Refresh predictions from API
    if now - last_refresh >= REFRESH_INTERVAL:
        new_predictions = fetch_predictions()
        if new_predictions is not None:
            predictions = new_predictions
        last_refresh = time.monotonic()

    # Cycle the third slot
    if len(predictions) > 2 and now - last_cycle >= CYCLE_INTERVAL:
        cycle_index += 1
        last_cycle = time.monotonic()
        display.root_group = build_display_group(predictions, cycle_index)

    time.sleep(0.5)
