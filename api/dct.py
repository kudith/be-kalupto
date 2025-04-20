import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import logging
import io
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def image_to_base64(image):
    """Convert numpy array image to base64 string"""
    pil_image = Image.fromarray(image)
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def base64_to_image(base64_string):
    """Convert base64 string to numpy array image"""
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


def encode_message_from_base64(base64_image, message):
    """
    Encode a message into a base64 image using enhanced DCT
    """
    try:
        logging.info(f"Starting enhanced DCT encoding: '{message}'")

        # Decode base64 to image
        image_data = base64.b64decode(base64_image)
        image = Image.open(BytesIO(image_data))

        # Convert to numpy array
        image_array = np.array(image)
        logging.info(f"Image shape: {image_array.shape}, dtype: {image_array.dtype}")

        # Extract blue channel
        if len(image_array.shape) == 3 and image_array.shape[2] >= 3:
            blue_channel = image_array[:, :, 0].astype(np.float64)  # Use blue channel (index 0 in BGR)
        else:
            blue_channel = np.array(image, dtype=np.float64)

        # Add checksum to message for validation
        checksum = hashlib.md5(message.encode()).hexdigest()[:8]
        message_with_checksum = f"{checksum}:{message}"

        # Prepare the message with length
        message_with_length = chr(len(message_with_checksum)) + message_with_checksum

        # Convert message to binary
        binary_data = ''.join(format(ord(char), '08b') for char in message_with_length)
        logging.info(f"Message in binary: {len(binary_data)} bits")

        # Process the channel for encoding
        h, w = blue_channel.shape

        # Ensure channel is padded to be divisible by 8x8 blocks
        h_pad = h + (8 - h % 8) if h % 8 != 0 else h
        w_pad = w + (8 - w % 8) if w % 8 != 0 else w

        padded_channel = np.zeros((h_pad, w_pad), dtype=np.float64)
        padded_channel[:h, :w] = blue_channel

        # Calculate capacity
        h_blocks = h_pad // 8
        w_blocks = w_pad // 8
        total_blocks = h_blocks * w_blocks

        # Use multiple coefficients per block for higher capacity
        dct_coeffs = [(4, 1), (3, 4), (5, 2), (2, 5)]
        bits_per_block = len(dct_coeffs)

        max_capacity = total_blocks * bits_per_block
        logging.info(f"Image capacity: {max_capacity} bits")

        if len(binary_data) > max_capacity:
            raise ValueError(f"Message too long. Maximum length is {max_capacity // 8 - 2} characters")

        # Set embedding parameters
        embedding_strength = 25.0

        # Process each 8x8 block
        bit_index = 0
        for i in range(0, h_pad, 8):
            for j in range(0, w_pad, 8):
                if bit_index >= len(binary_data):
                    break

                # Extract block
                block = padded_channel[i:i + 8, j:j + 8]

                # Apply DCT
                dct_block = cv2.dct(block)

                # Embed in multiple coefficients
                for coeff_idx, (ci, cj) in enumerate(dct_coeffs):
                    if bit_index + coeff_idx >= len(binary_data):
                        break

                    if binary_data[bit_index + coeff_idx] == '1':
                        dct_block[ci, cj] = abs(dct_block[ci, cj])
                        if dct_block[ci, cj] < embedding_strength:
                            dct_block[ci, cj] = embedding_strength
                    else:
                        dct_block[ci, cj] = -abs(dct_block[ci, cj])
                        if dct_block[ci, cj] > -embedding_strength:
                            dct_block[ci, cj] = -embedding_strength

                # Apply inverse DCT
                idct_block = cv2.idct(dct_block)

                # Replace block in channel
                padded_channel[i:i + 8, j:j + 8] = idct_block

                bit_index += bits_per_block

        # Crop back to original size
        encoded_channel = padded_channel[:h, :w]

        # Reconstruct the image
        result_image = image_array.copy()
        result_image[:, :, 0] = np.clip(encoded_channel, 0, 255).astype(np.uint8)

        # Convert to base64
        encoded_image_pil = Image.fromarray(result_image.astype(np.uint8))
        buffered = BytesIO()
        encoded_image_pil.save(buffered, format="PNG")
        encoded_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        logging.info("Enhanced DCT encoding completed successfully")
        return encoded_base64

    except Exception as e:
        logging.error(f"DCT encoding failed: {str(e)}")
        raise


def extract_message_from_base64(encoded_image_base64):
    """
    Extract a message from a base64 encoded image using enhanced DCT
    """
    try:
        logging.info("Starting enhanced DCT extraction...")

        # Decode base64 to image
        image_data = base64.b64decode(encoded_image_base64)
        image = Image.open(BytesIO(image_data))

        # Convert to numpy array
        image_array = np.array(image)

        # Extract blue channel - same as encoding
        if len(image_array.shape) == 3 and image_array.shape[2] >= 3:
            blue_channel = image_array[:, :, 0].astype(np.float64)  # Use blue channel (index 0 in BGR)
        else:
            blue_channel = np.array(image, dtype=np.float64)

        logging.info(f"Image shape: {blue_channel.shape}, dtype: {blue_channel.dtype}")

        # Ensure image is padded to be divisible by 8x8 blocks
        h, w = blue_channel.shape
        h_pad = h + (8 - h % 8) if h % 8 != 0 else h
        w_pad = w + (8 - w % 8) if w % 8 != 0 else w

        padded_image = np.zeros((h_pad, w_pad), dtype=np.float64)
        padded_image[:h, :w] = blue_channel

        # Use same coefficients as encoding
        dct_coeffs = [(4, 1), (3, 4), (5, 2), (2, 5)]
        bits_per_block = len(dct_coeffs)

        # Process each 8x8 block to extract bits
        extracted_bits = []

        for i in range(0, h_pad, 8):
            for j in range(0, w_pad, 8):
                # Extract block
                block = padded_image[i:i + 8, j:j + 8]

                # Apply DCT
                dct_block = cv2.dct(block)

                # Extract from multiple coefficients
                for ci, cj in dct_coeffs:
                    mid_freq_value = dct_block[ci, cj]
                    bit = '1' if mid_freq_value >= 0 else '0'
                    extracted_bits.append(bit)

                # First check if we have enough bits to get the length byte
                if len(extracted_bits) >= 8 and len(extracted_bits) == 8:
                    # First byte is length
                    length_byte = ''.join(extracted_bits[:8])
                    message_length = int(length_byte, 2)

                    # Calculate total bits needed
                    total_bits = 8 + (message_length * 8)
                    logging.info(f"Message length detected: {message_length} chars ({total_bits} bits)")

                # If we have enough bits, stop
                if len(extracted_bits) >= 8:
                    length_byte = ''.join(extracted_bits[:8])
                    message_length = int(length_byte, 2)
                    total_bits = 8 + (message_length * 8)

                    if len(extracted_bits) >= total_bits:
                        extracted_bits = extracted_bits[:total_bits]
                        break

        # Convert binary to text
        binary_message = ''.join(extracted_bits)
        message = ""

        # Extract message length from first byte
        length_byte = binary_message[:8]
        message_length = int(length_byte, 2)

        # Extract rest of message
        for i in range(8, len(binary_message), 8):
            if i + 8 <= len(binary_message):
                byte = binary_message[i:i + 8]
                try:
                    char = chr(int(byte, 2))
                    message += char
                except ValueError:
                    logging.warning(f"Invalid byte: {byte}")

        # Validate checksum and extract actual message
        try:
            checksum, actual_message = message.split(':', 1)
            calculated_checksum = hashlib.md5(actual_message.encode()).hexdigest()[:8]

            if checksum != calculated_checksum:
                logging.warning(f"Checksum validation failed! Expected {checksum}, got {calculated_checksum}")
                return "ERROR: Message extraction failed - corruption detected"

            logging.info(f"Enhanced DCT extraction completed: '{actual_message}'")
            return actual_message
        except ValueError:
            logging.warning("Could not split message with checksum - likely corrupted")
            return message

    except Exception as e:
        logging.error(f"DCT extraction failed: {str(e)}")
        raise
