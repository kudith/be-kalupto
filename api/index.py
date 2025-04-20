from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
from io import BytesIO
from PIL import Image
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Import locally but handle potential import errors
try:
    from api.dct import (
        encode_message_from_base64,
        extract_message_from_base64,
        image_to_base64,
        base64_to_image
    )
except ImportError:
    try:
        from .dct import (
            encode_message_from_base64,
            extract_message_from_base64,
            image_to_base64,
            base64_to_image
        )
    except ImportError:
        # Fallback to direct import for local development
        from dct import (
            encode_message_from_base64,
            extract_message_from_base64,
            image_to_base64,
            base64_to_image
        )

app = Flask(__name__)
# Configure CORS
CORS(app, resources={r"/*": {"origins": os.environ.get("ALLOWED_ORIGINS", "*")}})

@app.route('/', methods=['GET'])
def home():
    return 'Hello, this is api for dct stegano by adty!'

@app.route('/encode', methods=['POST'])
def encode():
    """
    Endpoint untuk menyisipkan pesan ke dalam gambar menggunakan DCT
    
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
        app.logger.error(f"Error in encode endpoint: {error_msg}")
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
        app.logger.error(f"Error in decode endpoint: {error_msg}")
        return jsonify({
            'error': 'Decoding failed',
            'message': error_msg
        }), 500

# For local development
if __name__ == '__main__':
    app.run(debug=True)

# The Flask app object is what Vercel will use
# No special handler function is needed