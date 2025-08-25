import math
from datetime import datetime
from models import BusLocation, Station

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def calculate_eta(bus_id, target_station_id):
    """Calculate estimated time of arrival to target station"""
    # Get latest bus location
    latest_location = BusLocation.query.filter_by(bus_id=bus_id).order_by(BusLocation.timestamp.desc()).first()
    
    if not latest_location:
        return "Location not available"
    
    # Get target station
    target_station = Station.query.get(target_station_id)
    if not target_station:
        return "Station not found"
    
    # Calculate distance
    distance = calculate_distance(
        latest_location.latitude, 
        latest_location.longitude,
        target_station.latitude, 
        target_station.longitude
    )
    
    # Assume average speed of 30 km/h in city traffic
    avg_speed = 30  # km/h
    eta_hours = distance / avg_speed
    eta_minutes = int(eta_hours * 60)
    
    if eta_minutes < 1:
        return "Arriving soon"
    elif eta_minutes < 60:
        return f"{eta_minutes} minutes"
    else:
        hours = eta_minutes // 60
        minutes = eta_minutes % 60
        return f"{hours}h {minutes}m"

def get_station_status(bus_id, station_id):
    """Determine if station is passed, approaching, or yet to come"""
    latest_location = BusLocation.query.filter_by(bus_id=bus_id).order_by(BusLocation.timestamp.desc()).first()
    
    if not latest_location:
        return "unknown"
    
    station = Station.query.get(station_id)
    if not station:
        return "unknown"
    
    # Get all stations for this bus ordered by sequence
    all_stations = Station.query.filter_by(bus_id=bus_id).order_by(Station.order).all()
    
    # Find closest station to current bus location
    min_distance = float('inf')
    closest_station_order = None
    
    for st in all_stations:
        distance = calculate_distance(
            latest_location.latitude, 
            latest_location.longitude,
            st.latitude, 
            st.longitude
        )
        if distance < min_distance:
            min_distance = distance
            closest_station_order = st.order
    
    # Determine status based on order
    if station.order < closest_station_order:
        return "passed"
    elif station.order == closest_station_order and min_distance < 0.5:  # Within 500m
        return "approaching"
    else:
        return "upcoming"
