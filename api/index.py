from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
from dct import (
    encode_message_from_base64,
    extract_message_from_base64,
    image_to_base64,
    base64_to_image
)
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
# Configure CORS more securely for production
CORS(app, resources={r"/*": {"origins": os.environ.get("ALLOWED_ORIGINS", "*")}})


@app.route('/', methods=['GET'])
def home():
    return 'Hello, this is api for dct stegano by adty!'

@app.route('/encode', methods=['POST'])
def encode():
    """
    Endpoint untuk menyisipkan pesan ke dalam gambar menggunakan SVD
    
    Request:
    - image: File gambar (multipart/form-data)
    - message: Pesan yang akan disisipkan (form-data)
    """
    try:
        # Cek apakah file gambar dan pesan ada dalam request
        if 'image' not in request.files or 'message' not in request.form:
            return jsonify({
                'error': 'Missing required fields',
                'message': 'Image file and message are required'
            }), 400
        
        # Ambil file gambar dan pesan dari request
        image_file = request.files['image']
        message = request.form['message']
        
        # Baca gambar dan konversi ke base64
        image = Image.open(image_file)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Encode pesan ke dalam gambar
        encoded_image = encode_message_from_base64(image_base64, message)
        
        return jsonify({
            'status': 'success',
            'encoded_image': encoded_image
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in encode endpoint: {error_msg}")
        return jsonify({
            'error': 'Encoding failed',
            'message': error_msg
        }), 500

@app.route('/decode', methods=['POST'])
def decode():
    """
    Endpoint untuk mengekstrak pesan dari gambar yang telah disisipi
    """
    try:
        # Cek apakah file gambar ada dalam request
        if 'image' not in request.files:
            return jsonify({
                'error': 'Missing required field',
                'message': 'Image file is required'
            }), 400
        
        # Ambil file gambar dari request
        image_file = request.files['image']
        
        # Baca gambar dan konversi ke base64
        image = Image.open(image_file)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Ekstrak pesan dari gambar
        message = extract_message_from_base64(image_base64)
        
        return jsonify({
            'status': 'success',
            'message': message
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in decode endpoint: {error_msg}")
        return jsonify({
            'error': 'Decoding failed',
            'message': error_msg
        }), 500

# This is the crucial part for Vercel serverless deployment
def handler(request):
    """WSGI handler for Vercel"""
    return app(request)

# Add this line to make the app compatible with Vercel serverless
from flask import request as flask_request
@app.before_request
def log_request_info():
    """Log request info for debugging"""
    print('Headers: %s', flask_request.headers)
    print('Body: %s', flask_request.get_data())

# For local development
if __name__ == '__main__':
    app.run(debug=True)