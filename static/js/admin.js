// Admin panel JavaScript functionality

// Edit Bus Modal
function editBus(busId, busNumber, driverName, driverPhone) {
    document.getElementById('edit_bus_number').value = busNumber;
    document.getElementById('edit_driver_name').value = driverName;
    document.getElementById('edit_driver_phone').value = driverPhone;
    document.getElementById('editBusForm').action = `/admin/buses/${busId}/edit`;
    
    const modal = new bootstrap.Modal(document.getElementById('editBusModal'));
    modal.show();
}

// Edit Station Modal
function editStation(stationId, stationName, latitude, longitude, busId, order) {
    document.getElementById('edit_station_name').value = stationName;
    document.getElementById('edit_latitude').value = latitude;
    document.getElementById('edit_longitude').value = longitude;
    document.getElementById('edit_bus_id').value = busId;
    document.getElementById('edit_order').value = order;
    document.getElementById('editStationForm').action = `/admin/stations/${stationId}/edit`;
    
    const modal = new bootstrap.Modal(document.getElementById('editStationModal'));
    modal.show();
}

// Edit Student Modal
function editStudent(studentId, username, name, stationId, busId) {
    document.getElementById('edit_username').value = username;
    document.getElementById('edit_name').value = name;
    document.getElementById('edit_bus_select').value = busId;
    document.getElementById('editStudentForm').action = `/admin/students/${studentId}/edit`;
    
    // Load stations for the selected bus
    loadStations(busId, 'edit_station_select', stationId);
    
    const modal = new bootstrap.Modal(document.getElementById('editStudentModal'));
    modal.show();
}

// Load stations based on selected bus
function loadStations(busId, selectElementId, selectedStationId = null) {
    const stationSelect = document.getElementById(selectElementId);
    
    if (!busId) {
        stationSelect.innerHTML = '<option value="">Select a station</option>';
        return;
    }
    
    // Show loading
    stationSelect.innerHTML = '<option value="">Loading stations...</option>';
    
    fetch(`/admin/get-stations/${busId}`)
        .then(response => response.json())
        .then(stations => {
            stationSelect.innerHTML = '<option value="">Select a station</option>';
            stations.forEach(station => {
                const option = document.createElement('option');
                option.value = station.station_id;
                option.textContent = station.station_name;
                if (selectedStationId && station.station_id == selectedStationId) {
                    option.selected = true;
                }
                stationSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading stations:', error);
            stationSelect.innerHTML = '<option value="">Error loading stations</option>';
        });
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Bus selection change for add student modal
    const addBusSelect = document.getElementById('add_bus_select');
    if (addBusSelect) {
        addBusSelect.addEventListener('change', function() {
            loadStations(this.value, 'add_station_select');
        });
    }
    
    // Bus selection change for edit student modal
    const editBusSelect = document.getElementById('edit_bus_select');
    if (editBusSelect) {
        editBusSelect.addEventListener('change', function() {
            loadStations(this.value, 'edit_station_select');
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('form[data-validation="true"]');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('form[action*="/delete"] button[type="submit"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                event.preventDefault();
            }
        });
    });
});

// Utility function to show loading state
function showLoading(element) {
    element.classList.add('loading');
    element.setAttribute('disabled', true);
}

// Utility function to hide loading state
function hideLoading(element) {
    element.classList.remove('loading');
    element.removeAttribute('disabled');
}

// GPS coordinate validation
function validateCoordinates(latitude, longitude) {
    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);
    
    if (isNaN(lat) || isNaN(lng)) {
        return { valid: false, message: 'Coordinates must be valid numbers' };
    }
    
    if (lat < -90 || lat > 90) {
        return { valid: false, message: 'Latitude must be between -90 and 90' };
    }
    
    if (lng < -180 || lng > 180) {
        return { valid: false, message: 'Longitude must be between -180 and 180' };
    }
    
    return { valid: true };
}

// Add coordinate validation to station forms
document.addEventListener('DOMContentLoaded', function() {
    const latitudeInputs = document.querySelectorAll('input[name="latitude"]');
    const longitudeInputs = document.querySelectorAll('input[name="longitude"]');
    
    [...latitudeInputs, ...longitudeInputs].forEach(input => {
        input.addEventListener('blur', function() {
            const latitude = this.form.querySelector('input[name="latitude"]').value;
            const longitude = this.form.querySelector('input[name="longitude"]').value;
            
            if (latitude && longitude) {
                const validation = validateCoordinates(latitude, longitude);
                if (!validation.valid) {
                    this.setCustomValidity(validation.message);
                } else {
                    this.setCustomValidity('');
                }
            }
        });
    });
});
