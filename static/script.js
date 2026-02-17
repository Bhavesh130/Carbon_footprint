// Form validation and interactivity
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('carbonForm');
    
    // Real-time validation
    form.addEventListener('submit', function(e) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.style.borderColor = '#ff4444';
                showError(field, 'This field is required');
            } else {
                field.style.borderColor = '#4CAF50';
                hideError(field);
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            showNotification('Please fill in all required fields', 'error');
        }
    });
    
    // Number input validation
    const numberInputs = form.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            const min = parseFloat(this.min);
            const max = parseFloat(this.max);
            const value = parseFloat(this.value);
            
            if (value < min) {
                this.value = min;
                showError(this, `Minimum value is ${min}`);
            } else if (value > max) {
                this.value = max;
                showError(this, `Maximum value is ${max}`);
            } else {
                hideError(this);
                this.style.borderColor = '#4CAF50';
            }
        });
    });
    
    // Show loading state on submit
    form.addEventListener('submit', function() {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculating...';
            submitBtn.disabled = true;
        }
    });
    
    // Real-time carbon estimate (simplified)
    const estimateFields = form.querySelectorAll('input, select');
    estimateFields.forEach(field => {
        field.addEventListener('change', updateEstimate);
    });
    
    // Tooltips for form fields
    const tooltipFields = form.querySelectorAll('.form-group label');
    tooltipFields.forEach(label => {
        const fieldId = label.getAttribute('for');
        if (fieldId) {
            const tooltipText = getTooltipText(fieldId);
            if (tooltipText) {
                addTooltip(label, tooltipText);
            }
        }
    });
});

// Helper functions
function showError(field, message) {
    let errorElement = field.parentElement.querySelector('.error-message');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        field.parentElement.appendChild(errorElement);
    }
    errorElement.textContent = message;
    errorElement.style.color = '#ff4444';
    errorElement.style.fontSize = '0.85rem';
    errorElement.style.marginTop = '5px';
}

function hideError(field) {
    const errorElement = field.parentElement.querySelector('.error-message');
    if (errorElement) {
        errorElement.remove();
    }
}

function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    // Style notification
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '15px 20px',
        borderRadius: '8px',
        color: 'white',
        zIndex: '1000',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        minWidth: '300px',
        maxWidth: '400px',
        boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
    });
    
    // Set color based on type
    const colors = {
        'success': '#4CAF50',
        'error': '#ff4444',
        'info': '#2196F3',
        'warning': '#ff9800'
    };
    notification.style.background = colors[type] || colors.info;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function updateEstimate() {
    // This is a simplified estimation for demonstration
    // In a real application, you might make an API call for a quick estimate
    const form = document.getElementById('carbonForm');
    const estimateElement = document.getElementById('quickEstimate');
    
    if (!estimateElement) return;
    
    // Simple calculation based on key factors
    let estimate = 2000; // Base value
    
    const transport = form.querySelector('#Transport').value;
    const diet = form.querySelector('#Diet').value;
    const distance = parseFloat(form.querySelector('#Vehicle Monthly Distance Km').value) || 0;
    const airTravel = form.querySelector('#Frequency of Traveling by Air').value;
    
    // Adjust based on transport
    if (transport === 'walk/bicycle') estimate -= 500;
    else if (transport === 'public') estimate -= 300;
    else if (transport === 'private') estimate += distance * 0.2;
    
    // Adjust based on diet
    if (diet === 'vegan') estimate -= 300;
    else if (diet === 'vegetarian') estimate -= 200;
    else if (diet === 'pescatarian') estimate -= 100;
    
    // Adjust based on air travel
    const airTravelFactors = {
        'never': -200,
        'rarely': 0,
        'frequently': 500,
        'very frequently': 1000
    };
    estimate += airTravelFactors[airTravel] || 0;
    
    // Update estimate display
    estimateElement.textContent = Math.max(500, Math.min(estimate, 5000)).toFixed(0);
    estimateElement.style.color = getColorForEstimate(estimate);
}

function getColorForEstimate(estimate) {
    if (estimate < 1500) return '#4CAF50';
    if (estimate < 2500) return '#FF9800';
    if (estimate < 3500) return '#FF5722';
    return '#F44336';
}

function getTooltipText(fieldId) {
    const tooltips = {
        'Diet': 'Your dietary choices significantly impact carbon emissions.',
        'Transport': 'Primary mode of transportation affects emissions greatly.',
        'Vehicle Monthly Distance Km': 'Distance traveled by vehicle per month.',
        'Frequency of Traveling by Air': 'Air travel has high carbon impact.',
        'Heating Energy Source': 'Energy source used for home heating.',
        'Energy efficiency': 'How energy efficient are your appliances?',
        'Recycling': 'Recycling helps reduce waste-related emissions.',
        'Monthly Grocery Bill': 'Higher spending often correlates with higher emissions.'
    };
    return tooltips[fieldId];
}

function addTooltip(element, text) {
    element.style.position = 'relative';
    element.style.cursor = 'help';
    
    element.addEventListener('mouseenter', function(e) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        
        Object.assign(tooltip.style, {
            position: 'absolute',
            background: '#333',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '4px',
            fontSize: '0.85rem',
            zIndex: '1000',
            width: '200px',
            bottom: '100%',
            left: '50%',
            transform: 'translateX(-50%)',
            pointerEvents: 'none',
            opacity: '0',
            transition: 'opacity 0.3s ease'
        });
        
        element.appendChild(tooltip);
        
        // Trigger reflow for transition
        tooltip.offsetHeight;
        tooltip.style.opacity = '1';
    });
    
    element.addEventListener('mouseleave', function() {
        const tooltip = this.querySelector('.tooltip');
        if (tooltip) {
            tooltip.style.opacity = '0';
            setTimeout(() => tooltip.remove(), 300);
        }
    });
}

// Auto-save form data
function autoSaveForm() {
    const form = document.getElementById('carbonForm');
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        if (formData.getAll(key).length > 1) {
            data[key] = formData.getAll(key);
        } else {
            data[key] = value;
        }
    }
    
    localStorage.setItem('carbonFormData', JSON.stringify(data));
}

function loadSavedForm() {
    const savedData = localStorage.getItem('carbonFormData');
    if (!savedData) return;
    
    const data = JSON.parse(savedData);
    const form = document.getElementById('carbonForm');
    
    Object.keys(data).forEach(key => {
        const value = data[key];
        const element = form.querySelector(`[name="${key}"]`);
        
        if (element) {
            if (element.type === 'checkbox') {
                if (Array.isArray(value)) {
                    element.checked = value.includes(element.value);
                } else {
                    element.checked = value === element.value;
                }
            } else if (element.type === 'radio') {
                if (Array.isArray(value)) {
                    element.checked = value.includes(element.value);
                } else {
                    element.checked = value === element.value;
                }
            } else {
                element.value = Array.isArray(value) ? value[0] : value;
            }
        }
    });
}

// Initialize form with saved data
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(loadSavedForm, 100);
    
    // Auto-save on change
    const form = document.getElementById('carbonForm');
    form.addEventListener('change', autoSaveForm);
    form.addEventListener('input', autoSaveForm);
});
