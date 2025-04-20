from flask import Flask, request, jsonify
from flask_cors import CORS
from api.dct import (
    encode_message_from_base64,
    extract_message_from_base64,
    image_to_base64,
    base64_to_image
)
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/', methods=['GET'])
def health_check():
    """Simple endpoint to check if API is running"""
    return jsonify({
        'status': 'success',
        'message': 'API is running'
    })

@app.route('/encode', methods=['POST'])
def encode():
    """
    Endpoint untuk menyisipkan pesan ke dalam gambar menggunakan SVD
    
    Request:
    - image: File gambar (multipart/form-data)
    - message: Pesan yang akan disisipkan (form-data)
    
    Response:
    - encoded_image: Gambar hasil encoding dalam format base64
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
        print(f"Error in encode endpoint: {str(e)}")
        return jsonify({
            'error': 'Encoding failed',
            'message': str(e)
        }), 500

@app.route('/decode', methods=['POST'])
def decode():
    """
    Endpoint untuk mengekstrak pesan dari gambar yang telah disisipi
    
    Request:
    - image: File gambar yang telah disisipi pesan (multipart/form-data)
    
    Response:
    - message: Pesan yang berhasil diekstrak
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
        return jsonify({
            'error': 'Decoding failed',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
