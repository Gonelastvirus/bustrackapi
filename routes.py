from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app, db
from models import Admin, Bus, Station, Student, BusLocation, Notice
from auth import admin_required, student_required, logout_admin, logout_student
from utils import calculate_eta, get_station_status
from datetime import datetime

@app.route('/')
def index():
    return render_template("index.html",session=session)

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    logout_admin()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    bus_count = Bus.query.count()
    station_count = Station.query.count()
    student_count = Student.query.count()
    notice_count = Notice.query.filter_by(is_active=True).count()
    
    return render_template('admin/dashboard.html', 
                         bus_count=bus_count, 
                         station_count=station_count,
                         student_count=student_count,
                         notice_count=notice_count)

@app.route('/admin/buses')
@admin_required
def manage_buses():
    buses = Bus.query.all()
    return render_template('admin/manage_buses.html', buses=buses)

@app.route('/admin/buses/add', methods=['POST'])
@admin_required
def add_bus():
    bus_number = request.form['bus_number']
    driver_name = request.form['driver_name']
    driver_phone = request.form['driver_phone']
    
    # Check if bus number already exists
    existing_bus = Bus.query.filter_by(bus_number=bus_number).first()
    if existing_bus:
        flash('Bus number already exists', 'error')
        return redirect(url_for('manage_buses'))
    
    bus = Bus(
        bus_number=bus_number,
        driver_name=driver_name,
        driver_phone=driver_phone
    )
    db.session.add(bus)
    db.session.commit()
    flash('Bus added successfully', 'success')
    return redirect(url_for('manage_buses'))

@app.route('/admin/buses/<int:bus_id>/edit', methods=['POST'])
@admin_required
def edit_bus(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    
    bus.bus_number = request.form['bus_number']
    bus.driver_name = request.form['driver_name']
    bus.driver_phone = request.form['driver_phone']
    
    db.session.commit()
    flash('Bus updated successfully', 'success')
    return redirect(url_for('manage_buses'))

@app.route('/admin/buses/<int:bus_id>/delete', methods=['POST'])
@admin_required
def delete_bus(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    db.session.delete(bus)
    db.session.commit()
    flash('Bus deleted successfully', 'success')
    return redirect(url_for('manage_buses'))

@app.route('/admin/stations')
@admin_required
def manage_stations():
    stations = Station.query.join(Bus).all()
    buses = Bus.query.all()
    return render_template('admin/manage_stations.html', stations=stations, buses=buses)

@app.route('/admin/stations/add', methods=['POST'])
@admin_required
def add_station():
    station_name = request.form['station_name']
    latitude = float(request.form['latitude'])
    longitude = float(request.form['longitude'])
    bus_id = int(request.form['bus_id'])
    order = int(request.form['order'])
    
    station = Station(
        station_name=station_name,
        latitude=latitude,
        longitude=longitude,
        bus_id=bus_id,
        order=order
    )
    db.session.add(station)
    db.session.commit()
    flash('Station added successfully', 'success')
    return redirect(url_for('manage_stations'))

@app.route('/admin/stations/<int:station_id>/edit', methods=['POST'])
@admin_required
def edit_station(station_id):
    station = Station.query.get_or_404(station_id)
    
    station.station_name = request.form['station_name']
    station.latitude = float(request.form['latitude'])
    station.longitude = float(request.form['longitude'])
    station.bus_id = int(request.form['bus_id'])
    station.order = int(request.form['order'])
    
    db.session.commit()
    flash('Station updated successfully', 'success')
    return redirect(url_for('manage_stations'))

@app.route('/admin/stations/<int:station_id>/delete', methods=['POST'])
@admin_required
def delete_station(station_id):
    station = Station.query.get_or_404(station_id)
    db.session.delete(station)
    db.session.commit()
    flash('Station deleted successfully', 'success')
    return redirect(url_for('manage_stations'))

@app.route('/admin/students')
@admin_required
def manage_students():
    students = Student.query.join(Bus).join(Station).all()
    buses = Bus.query.all()
    stations = Station.query.all()
    return render_template('admin/manage_students.html', students=students, buses=buses, stations=stations)

@app.route('/admin/students/add', methods=['POST'])
@admin_required
def add_student():
    username = request.form['username']
    password = request.form['password']
    name = request.form['name']
    station_id = int(request.form['station_id'])
    bus_id = int(request.form['bus_id'])
    
    # Check if username already exists
    existing_student = Student.query.filter_by(username=username).first()
    if existing_student:
        flash('Username already exists', 'error')
        return redirect(url_for('manage_students'))
    
    student = Student(
        username=username,
        name=name,
        station_id=station_id,
        bus_id=bus_id
    )
    student.set_password(password)
    db.session.add(student)
    db.session.commit()
    flash('Student added successfully', 'success')
    return redirect(url_for('manage_students'))

@app.route('/admin/students/<int:student_id>/edit', methods=['POST'])
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    student.username = request.form['username']
    student.name = request.form['name']
    student.station_id = int(request.form['station_id'])
    student.bus_id = int(request.form['bus_id'])
    
    # Update password if provided
    if request.form['password']:
        student.set_password(request.form['password'])
    
    db.session.commit()
    flash('Student updated successfully', 'success')
    return redirect(url_for('manage_students'))

@app.route('/admin/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully', 'success')
    return redirect(url_for('manage_students'))

@app.route('/admin/settings')
@admin_required
def admin_settings():
    return render_template('admin/settings.html')

@app.route('/admin/change-password', methods=['POST'])
@admin_required
def change_admin_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    admin = Admin.query.get(session['admin_id'])
    
    if not admin.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('admin_settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('admin_settings'))
    
    admin.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully', 'success')
    return redirect(url_for('admin_settings'))

# Student Routes
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        student = Student.query.filter_by(username=username).first()
        if student and student.check_password(password):
            session['student_id'] = student.student_id
            session['student_username'] = student.username
            session['student_name'] = student.name
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('student/login.html')

@app.route('/student/logout')
def student_logout():
    logout_student()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    student = Student.query.get(session['student_id'])
    bus = Bus.query.get(student.bus_id)
    pickup_station = Station.query.get(student.station_id)
    
    # Get latest bus location
    latest_location = BusLocation.query.filter_by(bus_id=student.bus_id).order_by(BusLocation.timestamp.desc()).first()
    
    # Get all stations for the bus
    stations = Station.query.filter_by(bus_id=student.bus_id).order_by(Station.order).all()
    
    # Add status and ETA to each station
    station_info = []
    for station in stations:
        status = get_station_status(student.bus_id, station.station_id)
        eta = calculate_eta(student.bus_id, station.station_id)
        station_info.append({
            'station': station,
            'status': status,
            'eta': eta
        })
    
    # Get active notices
    now = datetime.utcnow()
    notices = Notice.query.filter(
        Notice.is_active == True,
        db.or_(Notice.expires_at.is_(None), Notice.expires_at > now)
    ).order_by(Notice.created_at.desc()).all()
    
    return render_template('student/dashboard.html', 
                         student=student,
                         bus=bus,
                         pickup_station=pickup_station,
                         latest_location=latest_location,
                         station_info=station_info,
                         notices=notices)

# API Routes for GPS Updates
@app.route('/bus/<int:bus_id>/location', methods=['POST'])
def update_bus_location(bus_id):
    try:
        data = request.get_json() or request.form
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        
        # Verify bus exists
        bus = Bus.query.get(bus_id)
        if not bus:
            return jsonify({'error': 'Bus not found'}), 404
        
        # Create new location record
        location = BusLocation(
            bus_id=bus_id,
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.utcnow()
        )
        db.session.add(location)
        db.session.commit()
        
        return jsonify({'message': 'Location updated successfully'}), 200
        
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid latitude or longitude'}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# API Routes for Student App
@app.route('/student/my-bus')
@student_required
def get_my_bus():
    student = Student.query.get(session['student_id'])
    bus = Bus.query.get(student.bus_id)
    latest_location = BusLocation.query.filter_by(bus_id=student.bus_id).order_by(BusLocation.timestamp.desc()).first()
    
    bus_info = {
        'bus_number': bus.bus_number,
        'driver_name': bus.driver_name,
        'driver_phone': bus.driver_phone,
        'current_location': {
            'latitude': latest_location.latitude if latest_location else None,
            'longitude': latest_location.longitude if latest_location else None,
            'timestamp': latest_location.timestamp.isoformat() if latest_location else None
        }
    }
    
    return jsonify(bus_info)

@app.route('/student/my-bus/stations')
@student_required
def get_my_bus_stations():
    student = Student.query.get(session['student_id'])
    stations = Station.query.filter_by(bus_id=student.bus_id).order_by(Station.order).all()
    
    stations_info = []
    for station in stations:
        status = get_station_status(student.bus_id, station.station_id)
        eta = calculate_eta(student.bus_id, station.station_id)
        
        stations_info.append({
            'station_id': station.station_id,
            'station_name': station.station_name,
            'latitude': station.latitude,
            'longitude': station.longitude,
            'order': station.order,
            'status': status,
            'eta': eta
        })
    
    return jsonify(stations_info)

@app.route('/admin/get-stations/<int:bus_id>')
@admin_required
def get_stations_by_bus(bus_id):
    stations = Station.query.filter_by(bus_id=bus_id).order_by(Station.order).all()
    station_list = [{'station_id': s.station_id, 'station_name': s.station_name} for s in stations]
    return jsonify(station_list)

# Notice Management Routes
@app.route('/admin/notices')
@admin_required
def manage_notices():
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template('admin/manage_notices.html', notices=notices)

@app.route('/admin/notices/add', methods=['POST'])
@admin_required
def add_notice():
    title = request.form['title']
    message = request.form['message']
    notice_type = request.form['notice_type']
    expires_at_str = request.form.get('expires_at')
    
    # Parse expiration date if provided
    expires_at = None
    if expires_at_str:
        try:
            expires_at = datetime.strptime(expires_at_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid expiration date format', 'error')
            return redirect(url_for('manage_notices'))
    
    notice = Notice()
    notice.title = title
    notice.message = message
    notice.notice_type = notice_type
    notice.created_by = session['admin_id']
    notice.expires_at = expires_at
    
    db.session.add(notice)
    db.session.commit()
    flash('Notice added successfully', 'success')
    return redirect(url_for('manage_notices'))

@app.route('/admin/notices/<int:notice_id>/toggle', methods=['POST'])
@admin_required
def toggle_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    notice.is_active = not notice.is_active
    db.session.commit()
    
    status = "activated" if notice.is_active else "deactivated"
    flash(f'Notice {status} successfully', 'success')
    return redirect(url_for('manage_notices'))

@app.route('/admin/notices/<int:notice_id>/delete', methods=['POST'])
@admin_required
def delete_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    db.session.delete(notice)
    db.session.commit()
    flash('Notice deleted successfully', 'success')
    return redirect(url_for('manage_notices'))

# Map View Routes
@app.route('/student/map')
@student_required
def student_map():
    student = Student.query.get(session['student_id'])
    bus = Bus.query.get(student.bus_id)
    pickup_station = Station.query.get(student.station_id)
    return render_template('student/map.html', 
                         student=student, 
                         bus=bus, 
                         pickup_station=pickup_station)

@app.route('/admin/map')
@admin_required
def admin_map():
    buses = Bus.query.all()
    return render_template('admin/map.html', buses=buses)
