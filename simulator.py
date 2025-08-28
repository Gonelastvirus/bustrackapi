import time
import requests

API_BASE = "https://bustrackapi.onrender.com"
BUS_ID = "1"

# Station coordinates in order
stations = [
    (27.670631, 84.440116),  # parasbuspark
    (27.676613, 84.438805),  # sajha petrolpump
    (27.682233, 84.430120),  # chaubiskothi
]

def send_location(bus_id, lat, lon):
    url = f"{API_BASE}/bus/{bus_id}/location"
    data = {"latitude": lat, "longitude": lon}
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ Sent location: {lat}, {lon}")
        else:
            print(f"⚠️ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def interpolate_points(start, end, steps):
    """Generate intermediate lat/lon points between two coordinates"""
    lat1, lon1 = start
    lat2, lon2 = end
    for i in range(steps + 1):  # include end
        lat = lat1 + (lat2 - lat1) * (i / steps)
        lon = lon1 + (lon2 - lon1) * (i / steps)
        yield (lat, lon)

def main():
    interval = 3   # send update every 10 sec
    steps = 18      # so each station-to-station trip takes ~3 minutes (18*10 sec)

    while True:
        for i in range(len(stations) - 1):
            start = stations[i]
            end = stations[i + 1]

            for point in interpolate_points(start, end, steps):
                send_location(BUS_ID, point[0], point[1])
                time.sleep(interval)

        print("🔄 Route completed. Restarting...\n")

if __name__ == "__main__":
    main()

