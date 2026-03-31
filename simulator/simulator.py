import socket
import time
import random

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Starting GPS position (example: Cairo)
lat = 30.0444
lon = 31.2357

altitude = 0

while True:
    # Simulate movement
    lat += random.uniform(-0.05, 0.05)
    lon += random.uniform(-0.05, 0.05)

    altitude += random.uniform(-1, 2)
    altitude = max(0, altitude)

    speed = random.uniform(5, 15)
    battery = max(0, random.randint(20, 100))

    data = f"{altitude:.2f},{speed:.2f},{battery},{lat:.6f},{lon:.6f}"
    sock.sendto(data.encode(), ("127.0.0.1", 5000))

    print("Sent:", data)

    time.sleep(1)