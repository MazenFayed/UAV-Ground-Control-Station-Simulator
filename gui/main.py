import sys
import time
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QGridLayout, QSpacerItem
)
from PySide6.QtNetwork import QUdpSocket, QHostAddress
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from PySide6.QtGui import QFont, QColor, QPainter


# ── Palette ────────────────────────────────────────────────
BG_DEEP   = "#0A0C10"
BG_PANEL  = "#0F1318"
BG_CARD   = "#141920"
BORDER    = "#1E2530"
ACCENT    = "#00D4FF"       # cyan
ACCENT2   = "#00FF88"       # green
WARNING   = "#FF8C00"
DANGER    = "#FF3B3B"
TEXT_PRI  = "#E8F0FA"
TEXT_SEC  = "#6B7A8D"
TEXT_DIM  = "#3A4555"


STYLESHEET = f"""
QWidget {{
    background-color: {BG_DEEP};
    color: {TEXT_PRI};
    font-family: "Consolas", "Courier New", monospace;
}}

/* ── Header ── */
#header {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
}}
#app_title {{
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 4px;
    color: {ACCENT};
}}
#clock_label {{
    font-size: 13px;
    color: {TEXT_SEC};
    letter-spacing: 2px;
}}

/* ── Metric card ── */
#metric_card {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
}}
#metric_label {{
    font-size: 10px;
    letter-spacing: 2px;
    color: {TEXT_SEC};
}}
#metric_value {{
    font-size: 22px;
    font-weight: bold;
    color: {ACCENT};
}}
#metric_unit {{
    font-size: 11px;
    color: {TEXT_DIM};
    letter-spacing: 1px;
}}

/* ── Status badge ── */
#status_badge {{
    font-size: 11px;
    letter-spacing: 2px;
    font-weight: bold;
    border-radius: 3px;
    padding: 3px 10px;
}}

/* ── Section titles ── */
#section_title {{
    font-size: 10px;
    letter-spacing: 3px;
    color: {TEXT_SEC};
    border-bottom: 1px solid {BORDER};
    padding-bottom: 6px;
    margin-bottom: 4px;
}}

/* ── Connect button ── */
#connect_btn {{
    font-size: 12px;
    letter-spacing: 2px;
    font-weight: bold;
    border-radius: 4px;
    padding: 10px 24px;
    border: 1px solid {ACCENT};
    color: {ACCENT};
    background-color: transparent;
}}
#connect_btn:hover {{
    background-color: rgba(0, 212, 255, 0.10);
}}
#connect_btn[connected="true"] {{
    border-color: {DANGER};
    color: {DANGER};
}}
#connect_btn[connected="true"]:hover {{
    background-color: rgba(255, 59, 59, 0.10);
}}

/* ── Chart ── */
QChartView {{
    background: transparent;
    border: none;
}}
"""


def separator(vertical=False):
    sep = QFrame()
    sep.setFrameShape(QFrame.VLine if vertical else QFrame.HLine)
    sep.setStyleSheet(f"color: {BORDER}; background: {BORDER};")
    sep.setFixedWidth(1) if vertical else sep.setFixedHeight(1)
    return sep


class MetricCard(QWidget):
    def __init__(self, label, value="--", unit=""):
        super().__init__()
        self.setObjectName("metric_card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(2)

        lbl = QLabel(label.upper())
        lbl.setObjectName("metric_label")

        self._val = QLabel(value)
        self._val.setObjectName("metric_value")

        unt = QLabel(unit.upper())
        unt.setObjectName("metric_unit")

        layout.addWidget(lbl)
        layout.addWidget(self._val)
        layout.addWidget(unt)

    def set_value(self, v, color=None):
        self._val.setText(str(v))
        if color:
            self._val.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
        else:
            self._val.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {ACCENT};")


class GroundStation(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UAV GROUND CONTROL STATION")
        self.setMinimumSize(1200, 780)
        self.connected = False
        self.x = 0
        self.last_received_time = time.time()

        self._build_ui()
        self._setup_socket()
        self._setup_timers()

    # ── Build UI ──────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addLayout(self._make_body(), stretch=1)

    def _make_header(self):
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(52)

        h = QHBoxLayout(header)
        h.setContentsMargins(20, 0, 20, 0)

        # Left: title
        title = QLabel("◈  UAV GCS")
        title.setObjectName("app_title")
        h.addWidget(title)

        h.addStretch()

        # Centre: status badge
        self.status_badge = QLabel("● DISCONNECTED")
        self.status_badge.setObjectName("status_badge")
        self.status_badge.setStyleSheet(
            f"font-size: 11px; letter-spacing: 2px; font-weight: bold; "
            f"border-radius: 3px; padding: 3px 10px; "
            f"color: {DANGER}; background: rgba(255,59,59,0.10); border: 1px solid rgba(255,59,59,0.30);"
        )
        h.addWidget(self.status_badge)

        h.addStretch()

        # Right: clock
        self.clock_label = QLabel()
        self.clock_label.setObjectName("clock_label")
        h.addWidget(self.clock_label)

        return header

    def _make_body(self):
        body = QHBoxLayout()
        body.setContentsMargins(12, 12, 12, 12)
        body.setSpacing(12)

        # ── Left panel (metrics + controls) ──────────────
        left = QVBoxLayout()
        left.setSpacing(10)

        lbl = QLabel("TELEMETRY")
        lbl.setObjectName("section_title")
        left.addWidget(lbl)

        # Metric cards
        self.card_alt  = MetricCard("Altitude",  "--",  "m")
        self.card_spd  = MetricCard("Speed",     "--",  "m/s")
        self.card_bat  = MetricCard("Battery",   "--",  "%")
        self.card_lat  = MetricCard("Latitude",  "--",  "deg")
        self.card_lon  = MetricCard("Longitude", "--",  "deg")

        for c in [self.card_alt, self.card_spd, self.card_bat, self.card_lat, self.card_lon]:
            left.addWidget(c)

        left.addSpacing(8)
        left.addWidget(separator())
        left.addSpacing(8)

        # Connect button
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.setObjectName("connect_btn")
        self.connect_btn.setProperty("connected", "false")
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.clicked.connect(self.toggle_connection)
        left.addWidget(self.connect_btn)

        left.addStretch()

        # ── Right panel (chart + map) ─────────────────────
        right = QVBoxLayout()
        right.setSpacing(12)

        # Chart
        chart_lbl = QLabel("ALTITUDE  ·  REAL-TIME")
        chart_lbl.setObjectName("section_title")
        right.addWidget(chart_lbl)
        right.addWidget(self._make_chart(), stretch=2)

        # Map
        map_lbl = QLabel("GPS  TRACKING  MAP")
        map_lbl.setObjectName("section_title")
        right.addWidget(map_lbl)
        right.addWidget(self._make_map(), stretch=3)

        # Assemble
        body.addLayout(left, stretch=0)
        body.addWidget(separator(vertical=True))
        body.addLayout(right, stretch=1)

        return body

    def _make_chart(self):
        self.series = QLineSeries()
        pen = self.series.pen()
        pen.setColor(QColor(ACCENT))
        pen.setWidth(2)
        self.series.setPen(pen)

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setBackgroundBrush(QColor(BG_CARD))
        self.chart.setPlotAreaBackgroundBrush(QColor(BG_CARD))
        self.chart.setPlotAreaBackgroundVisible(True)
        self.chart.legend().hide()
        self.chart.setMargins(__import__('PySide6.QtCore', fromlist=['QMargins']).QMargins(10, 10, 10, 10))
        self.chart.setTitle("")

        self.axis_x = QValueAxis()
        self.axis_x.setRange(0, 50)
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTitleText("Time (s)")
        self.axis_x.setLabelsColor(QColor(TEXT_SEC))
        self.axis_x.setTitleBrush(QColor(TEXT_SEC))
        self.axis_x.setGridLineColor(QColor(BORDER))
        self.axis_x.setLinePen(__import__('PySide6.QtGui', fromlist=['QPen']).QPen(QColor(BORDER)))

        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 100)
        self.axis_y.setTitleText("Altitude (m)")
        self.axis_y.setLabelsColor(QColor(TEXT_SEC))
        self.axis_y.setTitleBrush(QColor(TEXT_SEC))
        self.axis_y.setGridLineColor(QColor(BORDER))
        self.axis_y.setLinePen(__import__('PySide6.QtGui', fromlist=['QPen']).QPen(QColor(BORDER)))

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)

        view = QChartView(self.chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setMinimumHeight(200)
        return view

    def _make_map(self):
        self.map_view = QWebEngineView()
        self.map_view.setMinimumHeight(300)
        map_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "map.html")
        )
        self.map_view.setUrl(QUrl.fromLocalFile(map_path))
        return self.map_view

    # ── Socket & Timers ───────────────────────────────────
    def _setup_socket(self):
        self.socket = QUdpSocket()
        self.socket.readyRead.connect(self.receive_data)

    def _setup_timers(self):
        # Clock
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        # Connection watchdog
        self.watchdog = QTimer()
        self.watchdog.timeout.connect(self.check_connection)
        self.watchdog.start(1000)

    def _update_clock(self):
        now = QDateTime.currentDateTime().toString("yyyy-MM-dd  HH:mm:ss  UTC")
        self.clock_label.setText(now)

    # ── Data & Connection ─────────────────────────────────
    def receive_data(self):
        while self.socket.hasPendingDatagrams():
            datagram, _, _ = self.socket.readDatagram(
                self.socket.pendingDatagramSize()
            )
            self.last_received_time = time.time()

            data = datagram.data().decode()
            parts = data.split(",")

            if len(parts) == 5:
                altitude, speed, battery, lat, lon = parts
                battery_i = int(battery)
                alt_f = float(altitude)

                self.card_alt.set_value(f"{alt_f:.1f}")
                self.card_spd.set_value(f"{float(speed):.1f}")
                self.card_lat.set_value(f"{float(lat):.4f}", color=ACCENT2)
                self.card_lon.set_value(f"{float(lon):.4f}", color=ACCENT2)

                bat_color = DANGER if battery_i < 20 else WARNING if battery_i < 30 else ACCENT2
                self.card_bat.set_value(battery_i, color=bat_color)

                # Chart
                self.series.append(self.x, alt_f)
                self.x += 1
                if self.x > 50:
                    self.axis_x.setRange(self.x - 50, self.x)

                # Auto-scale altitude axis
                if alt_f > self.axis_y.max() * 0.9:
                    self.axis_y.setRange(0, self.axis_y.max() * 1.5)

                # Map
                self.map_view.page().runJavaScript(
                    f"updateMarker({lat}, {lon});"
                )

    def check_connection(self):
        if self.connected and time.time() - self.last_received_time > 3:
            self._set_status("● SIGNAL LOST", DANGER, "rgba(255,59,59,0.10)", "rgba(255,59,59,0.30)")

    def toggle_connection(self):
        if not self.connected:
            self.socket.bind(QHostAddress.LocalHost, 5000)
            self.connected = True
            self.last_received_time = time.time()
            self._set_status("● CONNECTED", ACCENT2, "rgba(0,255,136,0.08)", "rgba(0,255,136,0.25)")
            self.connect_btn.setText("DISCONNECT")
            self.connect_btn.setProperty("connected", "true")
        else:
            self.socket.close()
            self.connected = False
            self._set_status("● DISCONNECTED", DANGER, "rgba(255,59,59,0.10)", "rgba(255,59,59,0.30)")
            self.connect_btn.setText("CONNECT")
            self.connect_btn.setProperty("connected", "false")

        # Force style refresh for dynamic property
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)

    def _set_status(self, text, color, bg, border_color):
        self.status_badge.setText(text)
        self.status_badge.setStyleSheet(
            f"font-size: 11px; letter-spacing: 2px; font-weight: bold; "
            f"border-radius: 3px; padding: 3px 10px; "
            f"color: {color}; background: {bg}; border: 1px solid {border_color};"
        )


# ── Run ────────────────────────────────────────────────────
app = QApplication(sys.argv)
app.setStyleSheet(STYLESHEET)
window = GroundStation()
window.show()
app.exec()