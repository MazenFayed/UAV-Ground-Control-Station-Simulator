# ◈ UAV Ground Control Station

A real-time UAV (drone) ground control station built with **Python** and **PySide6**, featuring live telemetry display, an altitude chart, and an interactive GPS map — paired with a UDP flight simulator for testing without real hardware.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-6.x-brightgreen?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## Screenshots

> _Run the simulator alongside the GCS to see it in action._
<img width="1918" height="1012" alt="uav gcs" src="https://github.com/user-attachments/assets/930e7085-514b-4b33-bb98-ef94b5602de8" />

---

## Features

- **Live telemetry** — altitude, speed, battery level, and GPS coordinates updated in real time
- **Altitude chart** — scrolling real-time line graph powered by Qt Charts
- **Interactive GPS map** — Leaflet.js map embedded via QWebEngineView, with a live-tracking marker and flight trail
- **Connection management** — one-click connect/disconnect with a live status badge and automatic signal-loss detection
- **Battery warnings** — color-coded indicator (green → orange → red) as battery drops
- **Dark military UI** — monospace font, cyan accent palette, clean panel layout
- **Flight simulator** — standalone UDP sender that mimics a flying drone for development and testing

---

## Project Structure

```
UAV-Ground-Control-Station/
│
├── gui/
│   ├── main.py          # Ground Control Station application
│   └── map.html         # Leaflet.js map page (loaded inside the app)
│
├── simulator/
│   └── simulator.py     # UDP flight data simulator
│
└── README.md
```

---

## How It Works

```
┌─────────────────────┐        UDP :5000        ┌──────────────────────┐
│   simulator.py      │  ──────────────────────▶ │     main.py (GCS)    │
│                     │   altitude,speed,        │                      │
│  Simulates a UAV    │   battery,lat,lon        │  Displays telemetry  │
│  sending telemetry  │                          │  chart & map         │
└─────────────────────┘                          └──────────────────────┘
```

The simulator sends a UDP datagram every second containing comma-separated telemetry values. The GCS binds to port `5000`, parses each packet, and updates the UI in real time.

**Packet format:**
```
altitude,speed,battery,latitude,longitude
30.42,9.81,87,30.052100,31.248300
```

---

## Requirements

- Python 3.10 or newer
- pip packages:

```
PySide6
PySide6-WebEngine
```

Install with:

```bash
pip install PySide6 PySide6-WebEngine
```

> **Note:** `PySide6-WebEngine` is required for the embedded map. On some systems it is bundled with PySide6; on others it must be installed separately.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/uav-ground-control-station.git
cd uav-ground-control-station
```

### 2. Install dependencies

```bash
pip install PySide6 PySide6-WebEngine
```

### 3. Launch the Ground Control Station

```bash
cd gui
python main.py
```

### 4. Launch the simulator (in a separate terminal)

```bash
cd simulator
python simulator.py
```

### 5. Connect

Click the **CONNECT** button in the GCS window. Telemetry data will begin flowing immediately.

---

## Map Setup

The map uses [Leaflet.js](https://leafletjs.com/) loaded from CDN inside a `QWebEngineView`. An internet connection is required for the map tiles to render.

If tiles appear blank or the map is black, this is usually caused by Qt's web engine blocking external URLs. Fix it by adding the following lines to `main.py` before `window = GroundStation()`:

```python
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile

QWebEngineProfile.defaultProfile().settings().setAttribute(
    QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
)
```

Alternatively, download Leaflet locally and update the `<link>` and `<script>` tags in `map.html` to point to the local files:

```bash
# Run inside the gui/ folder
curl -L "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" -o leaflet.css
curl -L "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"  -o leaflet.js
```

Then in `map.html`, replace the CDN links:
```html
<link rel="stylesheet" href="leaflet.css" />
<script src="leaflet.js"></script>
```

---

## Configuration

| Setting | Location | Default |
|---|---|---|
| UDP port | `gui/main.py` → `toggle_connection()` | `5000` |
| UDP port | `simulator/simulator.py` | `5000` |
| Starting GPS position | `simulator/simulator.py` | Cairo, Egypt (`30.0444, 31.2357`) |
| Map start position | `gui/map.html` | Cairo, Egypt |
| Signal-loss timeout | `gui/main.py` → `check_connection()` | `3 seconds` |
| Battery warning threshold | `gui/main.py` → `receive_data()` | `< 30%` (orange), `< 20%` (red) |

---

## Tech Stack

| Component | Technology |
|---|---|
| GUI framework | [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python) |
| Charts | Qt Charts (`PySide6.QtCharts`) |
| Embedded map | [Leaflet.js](https://leafletjs.com/) via `QWebEngineView` |
| Map tiles | [OpenStreetMap](https://www.openstreetmap.org/) / [CartoDB](https://carto.com/) |
| Networking | UDP sockets (`PySide6.QtNetwork.QUdpSocket`) |
| Simulator | Python standard library `socket` module |

---

## Roadmap

- [ ] Waypoint planning on the map (click-to-set)
- [ ] Flight data logging to CSV
- [ ] Multi-UAV support
- [ ] Offline map tile caching
- [ ] Serial/MAVLink protocol support (real hardware)
- [ ] Heads-up display (HUD) widget

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
