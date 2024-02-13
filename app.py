from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import pandas as pd
from flask_cors import CORS
import joblib


app = Flask(__name__)
CORS(app)  # Enable CORS

# Path to the file containing the MongoDB password
password_file = '/home/pbilla/mysite/mongodb_password.txt'

# Read the password from the file
with open(password_file, 'r') as file:
    mongodb_password = file.read().strip()

# Load the trained model (update the path to where your model is stored)
model = joblib.load('/home/pbilla/mysite/model.pkl')

cluster = f"mongodb+srv://pbilla:{mongodb_password}@cluster0.n4it795.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(cluster)

db = client.airbnb
collection = db.predict

@app.route('/')
def index():
    # Render the index.html template
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    # Adjust handling for security_deposit
    has_security_deposit_YES = 1 if data.get('security_deposit') == True else 0
    # Adjust handling for cancellation_policy_no_refunds
    cancellation_policy_no_refunds = 1 if data.get('cancellation_policy') == True else 0

    # Prepare the input data to match the model's expected format
    input_data = {
        'property_category_condo': 1 if data.get('property_type') == 'condo' else 0,
        'property_category_hotel': 1 if data.get('property_type') == 'hotel' else 0,
        'property_category_house': 1 if data.get('property_type') == 'house' else 0,
        'bedrooms': float(data.get('bedrooms', 0)),
        'beds': float(data.get('beds', 0)),
        'bathrooms': float(data.get('bathrooms', 0)),
        'accommodates': int(data.get('accommodates', 0)),

        # Amenities
        'wifi': 1 if 'wifi' in data.get('amenities', []) else 0,
        'air': 1 if 'air' in data.get('amenities', []) else 0,
        'heat': 1 if 'heat' in data.get('amenities', []) else 0,
        'tv': 1 if 'tv' in data.get('amenities', []) else 0,
        'wheelchair': 1 if 'wheelchair' in data.get('amenities', []) else 0,
        'pet': 1 if 'pet' in data.get('amenities', []) else 0,
        'parking': 1 if 'parking' in data.get('amenities', []) else 0,
        'gym': 1 if 'gym' in data.get('amenities', []) else 0,

        'price': float(data.get('price', 0)),
        'cleaning_fee': float(data.get('cleaning_fee', 0)),
        'extra_people': float(data.get('extra_people', 0)),

        'has_security_deposit_YES': has_security_deposit_YES,
        'minimum_nights': int(data.get('min_nights', 0)),
        'maximum_nights': int(data.get('max_nights', 0)),
        'cancellation_policy_no_refunds': cancellation_policy_no_refunds

    }

    # Convert amenities into individual binary features
    amenities = data.get('amenities', [])
    for amenity in ['wifi', 'air', 'heat', 'tv', 'wheelchair', 'pet', 'parking', 'gym']:
        input_data[amenity] = 1 if amenity in amenities else 0

    # Convert the input data to DataFrame
    input_df = pd.DataFrame([input_data])

    # Make prediction
    prediction = model.predict(input_df)

    input_df['high_booking_rate'] = prediction[0]
    # Iterate over DataFrame rows as (index, Series) pairs
    for _, row in input_df.iterrows():
        # Convert the row to a dictionary and insert it into MongoDB
        row_dict = row.to_dict()
        collection.insert_one(row_dict)

    result = "High Booking Rate" if prediction[0] == 1 else "Not High Booking Rate"

    return jsonify({'prediction': result})

if __name__ == '__main__':
    app.run(debug=True)

