from flask import request, session, jsonify
from flask_restx import Api, Resource, fields, Namespace
from werkzeug.exceptions import Unauthorized, NotFound, BadRequest
from app import app, db
from models import Admin, Student, Bus, Station, BusLocation, Notice
from utils import calculate_eta, get_station_status
from datetime import datetime

# Initialize Flask-RESTX
api = Api(
    app,
    version='1.0',
    title='School Bus Tracker API',
    description='API for managing school buses, students, and real-time tracking',
    doc='/docs/',
    prefix='/api'
)

# Define namespaces
auth_ns = api.namespace('auth', description='Authentication operations')
admin_ns = api.namespace('admin', description='Admin operations')
bus_ns = api.namespace('bus', description='Bus operations')
student_ns = api.namespace('student', description='Student operations')
notices_ns = api.namespace('notices', description='Notice operations')

# Models for request/response documentation
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

login_response = api.model('LoginResponse', {
    'success': fields.Boolean(description='Login success status'),
    'message': fields.String(description='Response message'),
    'user_type': fields.String(description='Type of user (admin/student)'),
    'user_id': fields.Integer(description='User ID'),
    'user_info': fields.Raw(description='Additional user information')
})

bus_location_model = api.model('BusLocation', {
    'latitude': fields.Float(required=True, description='GPS Latitude'),
    'longitude': fields.Float(required=True, description='GPS Longitude')
})

bus_info_model = api.model('BusInfo', {
    'bus_number': fields.String(description='Bus number'),
    'driver_name': fields.String(description='Driver name'),
    'driver_phone': fields.String(description='Driver phone'),
    'current_location': fields.Raw(description='Current GPS location')
})

station_model = api.model('Station', {
    'station_id': fields.Integer(description='Station ID'),
    'station_name': fields.String(description='Station name'),
    'latitude': fields.Float(description='Station latitude'),
    'longitude': fields.Float(description='Station longitude'),
    'order': fields.Integer(description='Order in route'),
    'status': fields.String(description='Station status (passed/approaching/upcoming)'),
    'eta': fields.String(description='Estimated time of arrival')
})

notice_model = api.model('Notice', {
    'notice_id': fields.Integer(description='Notice ID'),
    'title': fields.String(description='Notice title'),
    'message': fields.String(description='Notice message'),
    'notice_type': fields.String(description='Notice type (general/delay/emergency)'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'expires_at': fields.DateTime(description='Expiration timestamp')
})

error_model = api.model('Error', {
    'error': fields.String(description='Error message'),
    'code': fields.Integer(description='Error code')
})

# Authentication endpoints
@auth_ns.route('/admin/login')
class AdminLogin(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(login_response)
    @auth_ns.response(200, 'Success')
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        """Admin login endpoint"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            return {
                'success': True,
                'message': 'Login successful',
                'user_type': 'admin',
                'user_id': admin.id,
                'user_info': {
                    'username': admin.username,
                    'created_at': admin.created_at.isoformat()
                }
            }
        else:
            return {'success': False, 'message': 'Invalid credentials'}, 401

@auth_ns.route('/student/login')
class StudentLogin(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(login_response)
    @auth_ns.response(200, 'Success')
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        """Student login endpoint"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        student = Student.query.filter_by(username=username).first()
        if student and student.check_password(password):
            session['student_id'] = student.student_id
            session['student_username'] = student.username
            session['student_name'] = student.name
            return {
                'success': True,
                'message': 'Login successful',
                'user_type': 'student',
                'user_id': student.student_id,
                'user_info': {
                    'name': student.name,
                    'username': student.username,
                    'bus_id': student.bus_id,
                    'station_id': student.station_id
                }
            }
        else:
            return {'success': False, 'message': 'Invalid credentials'}, 401

# Bus GPS update endpoint
@bus_ns.route('/<int:bus_id>/location')
class BusLocationUpdate(Resource):
    @bus_ns.expect(bus_location_model)
    @bus_ns.response(200, 'Location updated successfully')
    @bus_ns.response(404, 'Bus not found')
    @bus_ns.response(400, 'Invalid coordinates')
    def post(self, bus_id):
        """Update bus GPS location"""
        try:
            data = request.get_json() or request.form
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if latitude is None or longitude is None:
                return {'error': 'Missing latitude or longitude'}, 400
                
            latitude = float(latitude)
            longitude = float(longitude)
            
            # Verify bus exists
            bus = Bus.query.get(bus_id)
            if not bus:
                return {'error': 'Bus not found'}, 404
            
            # Create new location record
            location = BusLocation()
            location.bus_id = bus_id
            location.latitude = latitude
            location.longitude = longitude
            location.timestamp = datetime.utcnow()
            db.session.add(location)
            db.session.commit()
            
            return {'message': 'Location updated successfully'}, 200
            
        except (ValueError, TypeError):
            return {'error': 'Invalid latitude or longitude'}, 400
        except Exception as e:
            return {'error': 'Internal server error'}, 500

# Student endpoints
@student_ns.route('/my-bus')
class MyBus(Resource):
    @student_ns.marshal_with(bus_info_model)
    @student_ns.response(200, 'Success')
    @student_ns.response(401, 'Authentication required')
    def get(self):
        """Get student's assigned bus information"""
        if 'student_id' not in session:
            return {'error': 'Authentication required'}, 401
            
        student = Student.query.get(session['student_id'])
        if not student:
            return {'error': 'Student not found'}, 404
            
        bus = Bus.query.get(student.bus_id)
        if not bus:
            return {'error': 'Bus not found'}, 404
            
        latest_location = BusLocation.query.filter_by(bus_id=student.bus_id).order_by(BusLocation.timestamp.desc()).first()
        
        return {
            'bus_number': bus.bus_number,
            'driver_name': bus.driver_name,
            'driver_phone': bus.driver_phone,
            'current_location': {
                'latitude': latest_location.latitude if latest_location else None,
                'longitude': latest_location.longitude if latest_location else None,
                'timestamp': latest_location.timestamp.isoformat() if latest_location else None
            }
        }

@student_ns.route('/my-bus/stations')
class MyBusStations(Resource):
    @student_ns.marshal_list_with(station_model)
    @student_ns.response(200, 'Success')
    @student_ns.response(401, 'Authentication required')
    def get(self):
        """Get ordered list of stations for student's bus with status and ETA"""
        if 'student_id' not in session:
            return {'error': 'Authentication required'}, 401
            
        student = Student.query.get(session['student_id'])
        if not student:
            return {'error': 'Student not found'}, 404
            
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
        
        return stations_info

# Notice endpoints
@notices_ns.route('/active')
class ActiveNotices(Resource):
    @notices_ns.marshal_list_with(notice_model)
    @notices_ns.response(200, 'Success')
    def get(self):
        """Get all active notices"""
        now = datetime.utcnow()
        notices = Notice.query.filter(
            Notice.is_active == True,
            db.or_(Notice.expires_at.is_(None), Notice.expires_at > now)
        ).order_by(Notice.created_at.desc()).all()
        
        return [{
            'notice_id': notice.notice_id,
            'title': notice.title,
            'message': notice.message,
            'notice_type': notice.notice_type,
            'created_at': notice.created_at.isoformat(),
            'expires_at': notice.expires_at.isoformat() if notice.expires_at else None
        } for notice in notices]

@notices_ns.route('/student')
class StudentNotices(Resource):
    @notices_ns.marshal_list_with(notice_model)
    @notices_ns.response(200, 'Success')
    @notices_ns.response(401, 'Authentication required')
    def get(self):
        """Get active notices for logged-in student"""
        if 'student_id' not in session:
            return {'error': 'Authentication required'}, 401
            
        now = datetime.utcnow()
        notices = Notice.query.filter(
            Notice.is_active == True,
            db.or_(Notice.expires_at.is_(None), Notice.expires_at > now)
        ).order_by(Notice.created_at.desc()).all()
        
        return [{
            'notice_id': notice.notice_id,
            'title': notice.title,
            'message': notice.message,
            'notice_type': notice.notice_type,
            'created_at': notice.created_at.isoformat(),
            'expires_at': notice.expires_at.isoformat() if notice.expires_at else None
        } for notice in notices]

# Admin endpoints for managing notices
create_notice_model = api.model('CreateNotice', {
    'title': fields.String(required=True, description='Notice title'),
    'message': fields.String(required=True, description='Notice message'),
    'notice_type': fields.String(description='Notice type (general/delay/emergency)', default='general'),
    'expires_at': fields.DateTime(description='Expiration date (optional)')
})

@admin_ns.route('/notices')
class AdminNotices(Resource):
    @admin_ns.marshal_list_with(notice_model)
    @admin_ns.response(200, 'Success')
    @admin_ns.response(401, 'Authentication required')
    def get(self):
        """Get all notices (admin only)"""
        if 'admin_id' not in session:
            return {'error': 'Admin authentication required'}, 401
            
        notices = Notice.query.order_by(Notice.created_at.desc()).all()
        return [{
            'notice_id': notice.notice_id,
            'title': notice.title,
            'message': notice.message,
            'notice_type': notice.notice_type,
            'created_at': notice.created_at.isoformat(),
            'expires_at': notice.expires_at.isoformat() if notice.expires_at else None
        } for notice in notices]
    
    @admin_ns.expect(create_notice_model)
    @admin_ns.response(201, 'Notice created successfully')
    @admin_ns.response(401, 'Authentication required')
    def post(self):
        """Create a new notice (admin only)"""
        if 'admin_id' not in session:
            return {'error': 'Admin authentication required'}, 401
            
        data = request.get_json()
        
        notice = Notice()
        notice.title = data['title']
        notice.message = data['message']
        notice.notice_type = data.get('notice_type', 'general')
        notice.created_by = session['admin_id']
        notice.expires_at = datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        
        db.session.add(notice)
        db.session.commit()
        
        return {'message': 'Notice created successfully', 'notice_id': notice.notice_id}, 201

@admin_ns.route('/notices/<int:notice_id>')
class AdminNoticeDetail(Resource):
    @admin_ns.response(200, 'Notice deactivated successfully')
    @admin_ns.response(401, 'Authentication required')
    @admin_ns.response(404, 'Notice not found')
    def delete(self, notice_id):
        """Deactivate a notice (admin only)"""
        if 'admin_id' not in session:
            return {'error': 'Admin authentication required'}, 401
            
        notice = Notice.query.get_or_404(notice_id)
        notice.is_active = False
        db.session.commit()
        
        return {'message': 'Notice deactivated successfully'}

# Real-time map endpoints
map_ns = api.namespace('map', description='Real-time map operations')

bus_location_response = api.model('BusLocationResponse', {
    'bus_id': fields.Integer(description='Bus ID'),
    'bus_number': fields.String(description='Bus number'),
    'latitude': fields.Float(description='Current latitude'),
    'longitude': fields.Float(description='Current longitude'),
    'timestamp': fields.DateTime(description='Last update timestamp'),
    'driver_name': fields.String(description='Driver name')
})

@map_ns.route('/student/bus-location')
class StudentBusLocation(Resource):
    @map_ns.marshal_with(bus_location_response)
    @map_ns.response(200, 'Success')
    @map_ns.response(401, 'Authentication required')
    def get(self):
        """Get real-time location of student's assigned bus"""
        if 'student_id' not in session:
            return {'error': 'Authentication required'}, 401
            
        student = Student.query.get(session['student_id'])
        if not student:
            return {'error': 'Student not found'}, 404
            
        bus = Bus.query.get(student.bus_id)
        latest_location = BusLocation.query.filter_by(bus_id=student.bus_id).order_by(BusLocation.timestamp.desc()).first()
        
        if not latest_location:
            return {'error': 'Bus location not available'}, 404
            
        return {
            'bus_id': bus.bus_id,
            'bus_number': bus.bus_number,
            'latitude': latest_location.latitude,
            'longitude': latest_location.longitude,
            'timestamp': latest_location.timestamp.isoformat(),
            'driver_name': bus.driver_name
        }

@map_ns.route('/admin/all-buses')
class AllBusesLocation(Resource):
    @map_ns.marshal_list_with(bus_location_response)
    @map_ns.response(200, 'Success')
    @map_ns.response(401, 'Authentication required')
    def get(self):
        """Get real-time locations of all buses (admin only)"""
        if 'admin_id' not in session:
            return {'error': 'Admin authentication required'}, 401
            
        buses = Bus.query.all()
        bus_locations = []
        
        for bus in buses:
            latest_location = BusLocation.query.filter_by(bus_id=bus.bus_id).order_by(BusLocation.timestamp.desc()).first()
            if latest_location:
                bus_locations.append({
                    'bus_id': bus.bus_id,
                    'bus_number': bus.bus_number,
                    'latitude': latest_location.latitude,
                    'longitude': latest_location.longitude,
                    'timestamp': latest_location.timestamp.isoformat(),
                    'driver_name': bus.driver_name
                })
        
        return bus_locations

station_location_model = api.model('StationLocation', {
    'station_id': fields.Integer(description='Station ID'),
    'station_name': fields.String(description='Station name'),
    'latitude': fields.Float(description='Station latitude'),
    'longitude': fields.Float(description='Station longitude'),
    'order': fields.Integer(description='Order in route'),
    'is_pickup_station': fields.Boolean(description='Is this the student pickup station')
})

@map_ns.route('/student/route-stations')
class StudentRouteStations(Resource):
    @map_ns.marshal_list_with(station_location_model)
    @map_ns.response(200, 'Success')
    @map_ns.response(401, 'Authentication required')
    def get(self):
        """Get all stations on student's bus route for map display"""
        if 'student_id' not in session:
            return {'error': 'Authentication required'}, 401
            
        student = Student.query.get(session['student_id'])
        if not student:
            return {'error': 'Student not found'}, 404
            
        stations = Station.query.filter_by(bus_id=student.bus_id).order_by(Station.order).all()
        
        stations_data = []
        for station in stations:
            stations_data.append({
                'station_id': station.station_id,
                'station_name': station.station_name,
                'latitude': station.latitude,
                'longitude': station.longitude,
                'order': station.order,
                'is_pickup_station': station.station_id == student.station_id
            })
        
        return stations_data