# MKE Transit Tracker

A DIY real-time bus arrival display built around an Adafruit Matrix Portal S3 and a pair of 128x32 RGB LED matrix panels. Inspired by (and largely adopted from) the [Eastside Urbanism Transit Tracker](https://transit-tracker.eastsideurbanism.org/), with a few additions — including the ability to set your own MCTS API key and bus stop numbers via a simple config file over USB.

**Note:** Eastside Urbanism's tracker is publicly available and updated a little more frequently than this one. If you just want a working display without any customization, their hosted version is a great starting point.

---

## What's in this repo

- `code.py` — the main logic. Connects to WiFi, fetches predictions from the MCTS Bustime API, and drives the display.
- `settings.example.toml` — a template for your credentials and stop configuration. **Rename this to `settings.toml` and fill it in before use.**

---

## Hardware

- Adafruit Matrix Portal S3
- Two 64x32 RGB LED matrix panels (mounted side by side for a 128x32 display)
- 5V USB power source (a charger brick at 2A+ is ideal; a laptop USB port works for setup)
- 3D printed enclosure (files included)
- Provided power wiring harness (red/black, comes with the LED panels)

---

## Assembly

### Wiring the panels

1. Open both LED panels and locate the red/black power wiring harness included in the box.
2. Plug one end into both displays.
3. On the Matrix Portal, you'll find two threaded holes labeled **5V** and **GND**. Use the fork ends of the harness and the two included screws to secure them — black to GND, red to 5V.
4. Align the panels side by side. The backs of the panels have arrows showing the direction of data flow — the Matrix Portal should plug into the first panel, which chains into the second in the direction of the arrow.

### Putting it in the enclosure

1. Loosely place both LED panels into the two-piece 3D printed enclosure.
2. The power cables will need to be bundled together to fit through the wireway. The Matrix Portal has a dedicated cutout it slides through.
3. Work the cables into place and push the two enclosure halves together until everything is snug.
4. Flip the assembly over so the back is facing up. Thread screws through the enclosure into the LED panel mounting holes — start with the two center overlap screws and leave them loose so you can align the panels.
5. Once the panels are straight, tighten everything down and add the remaining screws. Done.

> **Tip:** Set up the Portal and test your code before final assembly. It's much easier to troubleshoot before the screws are in.

---

## Software Setup

### 1. Flash CircuitPython

The Matrix Portal S3 doesn't ship with CircuitPython — you'll need to flash it first.

1. Plug the Matrix Portal into your computer via USB.
2. Download the latest CircuitPython `.UF2` file for the Matrix Portal S3 from [circuitpython.org](https://circuitpython.org/board/adafruit_matrixportal_s3) or via [Adafruit's guide](https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython).
3. Double-tap the reset button on the Portal fairly quickly — the LED should turn green and a drive called `MATRXS3BOOT` should appear on your computer.
4. Drag and drop the `.UF2` file onto that drive. It'll flash automatically, reboot, and reappear as a drive called `CIRCUITPY`.

### 2. Install required libraries

Download the [CircuitPython Library Bundle](https://circuitpython.org/libraries) matching your CircuitPython version (check `boot_out.txt` on the CIRCUITPY drive if unsure). Copy the following into the `lib/` folder on your CIRCUITPY drive:

- `adafruit_requests.mpy`
- `adafruit_connection_manager.mpy`

### 3. Configure your settings

1. Clone or download this repository.
2. Rename `settings.example.toml` to `settings.toml`.
3. Open it and fill in your details:

```toml
# This is where you store the credentials necessary for your code.
# The transit tracker includes Wifi Credentials, a bus API key, and a comma separated bus stop ID.
# A free Bus API key can be created by registering at:
# https://realtime.ridemcts.com/bustime/home.jsp

CIRCUITPY_WIFI_SSID = "your_wifi_network"
CIRCUITPY_WIFI_PASSWORD = "your_wifi_password"
BUS_API_KEY = "your_mcts_api_key"
BUS_STOP_ID = "your_stop_id"
```

A free API key can be created at [realtime.ridemcts.com/bustime/home.jsp](https://realtime.ridemcts.com/bustime/home.jsp) — create an account, log in, click "My API" in the top header bar, and request a key. Stop IDs can be found on the MCTS website or via the API directly.

### 4. Copy files to the device

Copy the contents of this repository onto the CIRCUITPY drive. The Portal will automatically reboot when files are saved or changed — this is normal behavior.

On reboot, the display should flash to life and begin connecting to WiFi. If a valid stop ID is configured, predictions will start showing shortly after.

> **Note:** The device will reboot any time you modify and save files on the CIRCUITPY drive — including `settings.toml`. This makes reconfiguring stops or credentials quick and easy without any special tools.

---

## Troubleshooting

- **Display doesn't light up** — check that the power harness is connected correctly (black to GND, red to 5V) and that your USB power source is at least 2A.
- **WiFi won't connect** — double check your SSID and password in `settings.toml`. The network must be 2.4GHz; the Matrix Portal S3 does not support 5GHz.
- **No predictions showing** — verify your API key and stop ID are correct. You can test the API directly in a browser: `https://realtime.ridemcts.com/bustime/api/v3/getpredictions?key=YOUR_KEY&stpid=YOUR_STOP&format=json`
- **`settings.toml` not found error** — make sure you renamed `settings.example.toml` to `settings.toml` (not just edited the example file).
- **Missing library error** — copy the missing `.mpy` file from the CircuitPython library bundle into the `lib/` folder on CIRCUITPY.

---

## Credits

Based on the [Eastside Urbanism Transit Tracker](https://transit-board.eastsideurbanism.org/). Thanks to their team for the original concept and open approach that made this possible.
