# School Bus Tracker

## Overview

A web-based school bus tracking system built with Flask that enables real-time monitoring of school bus locations and provides separate interfaces for administrators and students. The system allows administrators to manage buses, routes, stations, and student assignments, while students can track their assigned bus location and get estimated arrival times at their pickup stations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask**: Chosen as the web framework for its simplicity and rapid development capabilities
- **SQLAlchemy**: Used as the ORM for database operations with declarative models
- **Session-based Authentication**: Implements separate authentication flows for admins and students using Flask sessions

### Database Design
- **PostgreSQL**: Primary database for production (with SQLite fallback for development)
- **Key Models**:
  - `Admin`: Stores admin credentials with password hashing
  - `Bus`: Contains bus information and driver details
  - `Station`: Represents pickup/drop-off points with GPS coordinates and route ordering
  - `Student`: User accounts linked to buses and pickup stations
  - `BusLocation`: Real-time GPS tracking data with timestamps

### Frontend Architecture
- **Server-side Rendered Templates**: Uses Jinja2 templating with Bootstrap for responsive design
- **Progressive Enhancement**: Basic functionality works without JavaScript, enhanced with client-side features
- **Dark Theme**: Implements Bootstrap dark theme for better user experience

### Authentication & Authorization
- **Role-based Access**: Separate login systems for administrators and students
- **Decorator-based Protection**: Uses `@admin_required` and `@student_required` decorators for route protection
- **Session Management**: Secure session handling with configurable secret keys

### Real-time Features
- **Auto-refresh Dashboard**: Student dashboard automatically refreshes bus location data every 30 seconds
- **ETA Calculations**: Haversine formula implementation for distance calculations and arrival time estimates
- **Location Tracking**: Timestamp-based GPS coordinate storage for bus movement history

### API Design Patterns
- **RESTful Routes**: Follows REST conventions for CRUD operations on buses, stations, and students
- **Form-based Interactions**: Traditional web forms for data entry and management
- **JSON Endpoints**: Prepared for future API expansion with structured data responses

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: Database ORM integration
- **Werkzeug**: Password hashing and WSGI utilities
- **SQLAlchemy**: Database toolkit and ORM

### Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI elements
- **Bootstrap JavaScript**: Interactive components and modals

### Database
- **PostgreSQL**: Production database system
- **psycopg2**: PostgreSQL adapter for Python (implied dependency)

### Development Tools
- **Python Logging**: Built-in logging for debugging and monitoring
- **ProxyFix**: Werkzeug middleware for handling proxy headers in deployment

### Optional Integrations
- **Environment Variables**: Configuration through environment variables for database URLs and session secrets
- **Real-time Location APIs**: Framework prepared for GPS tracking device integration
- **SMS/Email Services**: Architecture supports future notification features for bus arrival alerts