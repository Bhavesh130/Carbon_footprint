from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import joblib
import os
import traceback
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Global variables for model
model = None
scaler = None
label_encoders = None
feature_names = []

# Define expected feature names in correct order
expected_features = [
    'Body Type', 'Sex', 'Diet', 'How Often Shower', 
    'Heating Energy Source', 'Transport', 'Vehicle Type', 
    'Social Activity', 'Monthly Grocery Bill', 
    'Frequency of Traveling by Air', 'Vehicle Monthly Distance Km',
    'Waste Bag Size', 'Waste Bag Weekly Count', 
    'How Long TV PC Daily Hour', 'How Many New Clothes Monthly',
    'How Long Internet Daily Hour', 'Energy efficiency',
    'Recycling_Count', 'Recycles_Paper', 'Recycles_Plastic',
    'Recycles_Glass', 'Recycles_Metal', 'Cooking_Methods_Count',
    'Cooks_With_Stove', 'Cooks_With_Oven', 'Cooks_With_Microwave',
    'Cooks_With_Grill', 'Cooks_With_Airfryer'
]

def load_model():
    """Load the trained model and preprocessing objects"""
    global model, scaler, label_encoders, feature_names
    
    try:
        # Check if model files exist
        model_files = [
            'best_carbon_emission_model.pkl',
            'scaler.pkl', 
            'label_encoders.pkl'
        ]
        
        missing_files = []
        for file in model_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"Missing model files: {missing_files}")
            print("Please train the model first or place the files in the correct location.")
            return False
        
        # Load the model and preprocessing objects
        model = joblib.load('best_carbon_emission_model.pkl')
        scaler = joblib.load('scaler.pkl')
        label_encoders = joblib.load('label_encoders.pkl')
        
        print("=" * 60)
        print("MODEL LOADED SUCCESSFULLY!")
        print(f"Model type: {type(model).__name__}")
        print(f"Features expected: {len(expected_features)}")
        print("=" * 60)
        
        # Load or create feature names
        if os.path.exists('feature_names.pkl'):
            feature_names = joblib.load('feature_names.pkl')
        else:
            feature_names = expected_features
            joblib.dump(feature_names, 'feature_names.pkl')
            print("Created feature_names.pkl")
        
        return True
        
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        print(traceback.format_exc())
        return False

# Load model when app starts
model_loaded = load_model()

# Available options for dropdowns
CATEGORY_OPTIONS = {
    'Body Type': ['underweight', 'normal', 'overweight', 'obese'],
    'Sex': ['male', 'female'],
    'Diet': ['vegan', 'vegetarian', 'pescatarian', 'omnivore'],
    'How Often Shower': ['less frequently', 'daily', 'more frequently', 'twice a day'],
    'Heating Energy Source': ['coal', 'wood', 'natural gas', 'electricity'],
    'Transport': ['public', 'private', 'walk/bicycle'],
    'Vehicle Type': ['none', 'petrol', 'diesel', 'lpg', 'hybrid', 'electric'],
    'Social Activity': ['never', 'sometimes', 'often'],
    'Frequency of Traveling by Air': ['never', 'rarely', 'frequently', 'very frequently'],
    'Waste Bag Size': ['small', 'medium', 'large', 'extra large'],
    'Energy efficiency': ['No', 'Sometimes', 'Yes']
}

# Helper function to prepare input data
def prepare_input_data(form_data):
    """Convert form data to model input format"""
    
    # Create a dictionary with all expected features
    input_dict = {}
    
    # Initialize all features with default values
    for feature in expected_features:
        input_dict[feature] = 0
    
    # Handle list-like features (checkbox groups)
    recycling_materials = form_data.get('Recycling', [])
    if isinstance(recycling_materials, str):
        recycling_materials = [recycling_materials]
    
    cooking_methods = form_data.get('Cooking_With', [])
    if isinstance(cooking_methods, str):
        cooking_methods = [cooking_methods]
    
    # Set recycling features
    input_dict['Recycling_Count'] = len(recycling_materials)
    for material in ['Paper', 'Plastic', 'Glass', 'Metal']:
        input_dict[f'Recycles_{material}'] = 1 if material in recycling_materials else 0
    
    # Set cooking features
    input_dict['Cooking_Methods_Count'] = len(cooking_methods)
    for method in ['Stove', 'Oven', 'Microwave', 'Grill', 'Airfryer']:
        input_dict[f'Cooks_With_{method}'] = 1 if method in cooking_methods else 0
    
    # Handle categorical features
    for feature in ['Body Type', 'Sex', 'Diet', 'How Often Shower', 
                    'Heating Energy Source', 'Transport', 'Vehicle Type',
                    'Social Activity', 'Frequency of Traveling by Air',
                    'Waste Bag Size', 'Energy efficiency']:
        
        value = form_data.get(feature, '')
        
        # Special handling for Vehicle Type
        if feature == 'Vehicle Type':
            transport = form_data.get('Transport', '')
            if transport == 'walk/bicycle':
                value = 'none'
            elif not value and transport == 'private':
                value = 'petrol'  # default for private transport
        
        if feature in label_encoders and value:
            try:
                # Check if value exists in label encoder
                if value in label_encoders[feature].classes_:
                    input_dict[feature] = label_encoders[feature].transform([value])[0]
                else:
                    # Use the first class as default
                    input_dict[feature] = 0
            except Exception as e:
                print(f"Error encoding {feature} with value '{value}': {e}")
                input_dict[feature] = 0
    
    # Handle numeric features
    numeric_features = {
        'Monthly Grocery Bill': form_data.get('Monthly Grocery Bill', '0'),
        'Vehicle Monthly Distance Km': form_data.get('Vehicle Monthly Distance Km', '0'),
        'Waste Bag Weekly Count': form_data.get('Waste Bag Weekly Count', '0'),
        'How Long TV PC Daily Hour': form_data.get('How Long TV PC Daily Hour', '0'),
        'How Many New Clothes Monthly': form_data.get('How Many New Clothes Monthly', '0'),
        'How Long Internet Daily Hour': form_data.get('How Long Internet Daily Hour', '0')
    }
    
    for feature, value in numeric_features.items():
        try:
            input_dict[feature] = float(value) if value else 0.0
        except:
            input_dict[feature] = 0.0
    
    # Create DataFrame with correct column order
    input_df = pd.DataFrame([input_dict])
    
    # Ensure all columns are present in correct order
    for col in expected_features:
        if col not in input_df.columns:
            input_df[col] = 0
    
    # Reorder columns
    input_df = input_df[expected_features]
    
    return input_df

# Routes
@app.route('/')
def home():
    """Render the home page with input form"""
    if not model_loaded:
        return render_template('error.html', 
                             error="Model not loaded. Please check if model files exist.",
                             details="Required files: best_carbon_emission_model.pkl, scaler.pkl, label_encoders.pkl")
    
    return render_template('index.html', 
                         category_options=CATEGORY_OPTIONS,
                         feature_names=expected_features)

@app.route('/predict', methods=['POST'])
def predict():
    """Handle prediction requests"""
    if not model_loaded:
        return render_template('error.html', 
                             error="Model not loaded. Cannot make predictions.",
                             details="Please check if model files are in the correct location.")
    
    try:
        # Get form data
        form_data = request.form.to_dict()
        
        # Get checkbox groups
        form_data['Recycling'] = request.form.getlist('Recycling')
        form_data['Cooking_With'] = request.form.getlist('Cooking_With')
        
        # Debug: print received form data
        print("\n" + "="*60)
        print("FORM DATA RECEIVED:")
        for key, value in form_data.items():
            if key not in ['Recycling', 'Cooking_With']:
                print(f"{key}: {value}")
        print(f"Recycling: {form_data['Recycling']}")
        print(f"Cooking_With: {form_data['Cooking_With']}")
        print("="*60 + "\n")
        
        # Prepare input data
        input_df = prepare_input_data(form_data)
        
        print("PREPARED INPUT DATA:")
        print(input_df.head())
        print(f"Shape: {input_df.shape}")
        print("="*60 + "\n")
        
        # Scale the data
        input_scaled = scaler.transform(input_df)
        
        # Make prediction
        prediction = model.predict(input_scaled)[0]
        
        print(f"PREDICTION MADE: {prediction}")
        
        # Color mapping based on prediction value
        color_map = {
            "Excellent": "#4CAF50",      # Green
            "Good": "#8BC34A",           # Light Green
            "Average": "#FF9800",        # Orange
            "High": "#FF5722",           # Deep Orange
            "Very High": "#F44336"       # Red
        }
        
        # Determine rating and color
        if prediction < 1000:
            rating = "Excellent"
            percentile = 10
        elif prediction < 2000:
            rating = "Good"
            percentile = 40
        elif prediction < 3000:
            rating = "Average"
            percentile = 60
        elif prediction < 4000:
            rating = "High"
            percentile = 80
        else:
            rating = "Very High"
            percentile = 95
        
        color = color_map.get(rating, "#FF9800")
        
        # Create response
        response = {
            'prediction': round(prediction, 2),
            'rating': rating,
            'color': color,
            'percentile': percentile,
            'input_summary': {
                'Diet': form_data.get('Diet', 'Unknown'),
                'Transport': form_data.get('Transport', 'Unknown'),
                'Vehicle_Distance': form_data.get('Vehicle Monthly Distance Km', '0'),
                'Air_Travel': form_data.get('Frequency of Traveling by Air', 'Unknown'),
                'Energy_Source': form_data.get('Heating Energy Source', 'Unknown')
            }
        }
        
        print(f"RESPONSE: {response}")
        print("="*60 + "\n")
        
        return render_template('result.html', result=response)
    
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        print(traceback.format_exc())
        return render_template('error.html', 
                             error=f"Prediction error: {str(e)}",
                             details="Please check your input values and try again.")

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """API endpoint for predictions"""
    if not model_loaded:
        return jsonify({'error': 'Model not loaded', 'status': 'error'}), 500
    
    try:
        data = request.json
        form_data = data.get('data', {})
        
        # Prepare input data
        input_df = prepare_input_data(form_data)
        
        # Scale the data
        input_scaled = scaler.transform(input_df)
        
        # Make prediction
        prediction = model.predict(input_scaled)[0]
        
        return jsonify({
            'prediction': round(prediction, 2),
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 400

@app.route('/api/features', methods=['GET'])
def get_features():
    """Get available features and options"""
    return jsonify({
        'features': expected_features,
        'categories': CATEGORY_OPTIONS,
        'model_loaded': model_loaded
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = 'healthy' if model_loaded else 'unhealthy'
    details = {
        'model_loaded': model_loaded,
        'model_type': type(model).__name__ if model_loaded else None,
        'features_count': len(expected_features)
    }
    return jsonify({'status': status, 'details': details})

@app.route('/debug/model', methods=['GET'])
def debug_model():
    """Debug endpoint to check model status"""
    if model_loaded:
        return jsonify({
            'status': 'loaded',
            'model_type': type(model).__name__,
            'features': expected_features,
            'files_present': {
                'model': os.path.exists('best_carbon_emission_model.pkl'),
                'scaler': os.path.exists('scaler.pkl'),
                'encoders': os.path.exists('label_encoders.pkl')
            }
        })
    else:
        return jsonify({
            'status': 'not_loaded',
            'files_present': {
                'model': os.path.exists('best_carbon_emission_model.pkl'),
                'scaler': os.path.exists('scaler.pkl'),
                'encoders': os.path.exists('label_encoders.pkl')
            }
        }), 500

# Create error.html template if it doesn't exist
error_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - Carbon Footprint Calculator</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&amp;display=swap">
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <i class="fas fa-exclamation-triangle">&#8203;</i>
                <h1>Error</h1>
            </div>
            <a href="/" class="btn-back">
                <i class="fas fa-arrow-left">&#8203;</i> Back to Calculator
            </a>
        </div>
        
        <div class="error-container">
            <div class="error-card">
                <h2><i class="fas fa-bug">&#8203;</i> An Error Occurred</h2>
                <div class="error-message">
                    <p><strong>{{ error }}</strong></p>
                    {% if details %}
                    <p class="error-details">{{ details }}</p>
                    {% endif %}
                </div>
                
                <div class="troubleshooting">
                    <h3><i class="fas fa-wrench">&#8203;</i> Troubleshooting Steps:</h3>
                    <ol>
                        <li>Ensure all model files are in the same directory as app.py</li>
                        <li>Check if model files exist: best_carbon_emission_model.pkl, scaler.pkl, label_encoders.pkl</li>
                        <li>Verify you have the required permissions to read the files</li>
                        <li>Try training the model again if files are missing</li>
                    </ol>
                </div>
                
                <div class="action-buttons">
                    <a href="/debug/model" class="btn btn-info" target="_blank">
                        <i class="fas fa-search">&#8203;</i> Check Model Status
                    </a>
                    <a href="/" class="btn btn-primary">
                        <i class="fas fa-home">&#8203;</i> Return Home
                    </a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

# Create error.html if it doesn't exist
if not os.path.exists('templates/error.html'):
    os.makedirs('templates', exist_ok=True)
    with open('templates/error.html', 'w') as f:
        f.write(error_template)
    print("Created error.html template")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("STARTING CARBON FOOTPRINT CALCULATOR")
    print("="*60)
    
    if model_loaded:
        print("✓ Model loaded successfully")
        print("✓ Starting Flask application...")
        print("✓ Open http://localhost:5000 in your browser")
    else:
        print("✗ Model failed to load")
        print("✗ Please check if model files exist:")
        print("  - best_carbon_emission_model.pkl")
        print("  - scaler.pkl")
        print("  - label_encoders.pkl")
        print("\nYou can train the model using the provided training script.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)