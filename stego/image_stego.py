import cv2
import numpy as np
from PIL import Image
from scipy.fft import dct, idct
from utils.crypto import text_to_binary, binary_to_text, encrypt, decrypt

def hide_message_in_image_lsb(image_path: str, message: str, password: str, output_path: str) -> None:
    encrypted_message = encrypt(message, password)
    binary_message = text_to_binary(encrypted_message)
    binary_message += '1111111111111110'
    
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    width, height = img.size
    pixels = img.load()
    
    max_bytes = (width * height * 3) // 8
    if len(binary_message) > max_bytes * 8:
        raise ValueError(f"Message too large to hide in this image. Max size: {max_bytes} bytes")
    
    idx = 0
    for y in range(height):
        for x in range(width):
            if idx < len(binary_message):
                r, g, b = pixels[x, y]
                
                if idx < len(binary_message):
                    r = r & ~1 | int(binary_message[idx])
                    idx += 1
                
                if idx < len(binary_message):
                    g = g & ~1 | int(binary_message[idx])
                    idx += 1
                    
                if idx < len(binary_message):
                    b = b & ~1 | int(binary_message[idx])
                    idx += 1
                
                pixels[x, y] = (r, g, b)
    
    img.save(output_path, 'PNG')
    print(f"Message successfully hidden in {output_path}")

def extract_message_from_image_lsb(image_path: str, password: str) -> str:
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    width, height = img.size
    pixels = img.load()
    
    binary_message = ''
    delimiter = '1111111111111110'
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            binary_message += str(r & 1)
            binary_message += str(g & 1)
            binary_message += str(b & 1)
            
            if len(binary_message) >= len(delimiter) and binary_message[-len(delimiter):] == delimiter:
                binary_message = binary_message[:-len(delimiter)]
                try:
                    padding = 8 - (len(binary_message) % 8) if len(binary_message) % 8 != 0 else 0
                    binary_message += '0' * padding
                    encrypted_message = binary_to_text(binary_message)
                    return decrypt(encrypted_message, password)
                except Exception as e:
                    return f"Failed to extract message: {str(e)}"
    
    return "No hidden message found"

def hide_message_in_image_dct(image_path: str, message: str, password: str, output_path: str, 
                             strength: float = 25.0) -> None:
    encrypted_message = encrypt(message, password)
    binary_message = text_to_binary(encrypted_message) + '1111111111111110'
    
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not read image {image_path}")
    
    img_ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    
    y_channel = img_ycrcb[:,:,0].astype(float)
    height, width = y_channel.shape
    
    block_size = 8
    blocks_h = height // block_size
    blocks_w = width // block_size
    max_message_bits = blocks_h * blocks_w
    
    if len(binary_message) > max_message_bits:
        raise ValueError(f"Message too large to hide in this image. Max size: {max_message_bits // 8} bytes")
    
    message_index = 0
    for y in range(0, blocks_h * block_size, block_size):
        for x in range(0, blocks_w * block_size, block_size):
            if message_index < len(binary_message):
                block = y_channel[y:y+block_size, x:x+block_size]
                
                block_dct = dct(dct(block, axis=0), axis=1)
                
                bit = int(binary_message[message_index])
                if bit == 1:
                    block_dct[4, 5] = abs(block_dct[4, 5]) + strength
                else:
                    block_dct[4, 5] = -abs(block_dct[4, 5]) - strength
                
                block = idct(idct(block_dct, axis=1), axis=0)
                
                y_channel[y:y+block_size, x:x+block_size] = block
                message_index += 1
    
    img_ycrcb[:,:,0] = np.clip(y_channel, 0, 255).astype(np.uint8)
    
    stego_img = cv2.cvtColor(img_ycrcb, cv2.COLOR_YCrCb2BGR)
    
    cv2.imwrite(output_path, stego_img, [cv2.IMWRITE_JPEG_QUALITY, 100])
    print(f"Message successfully hidden in {output_path} using DCT method")

def extract_message_from_image_dct(image_path: str, password: str, threshold: float = 0) -> str:
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not read image {image_path}")
    
    img_ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    
    y_channel = img_ycrcb[:,:,0].astype(float)
    height, width = y_channel.shape
    
    block_size = 8
    blocks_h = height // block_size
    blocks_w = width // block_size
    
    binary_message = ''
    delimiter = '1111111111111110'
    
    for y in range(0, blocks_h * block_size, block_size):
        for x in range(0, blocks_w * block_size, block_size):
            block = y_channel[y:y+block_size, x:x+block_size]
            
            block_dct = dct(dct(block, axis=0), axis=1)
            
            bit = '1' if block_dct[4, 5] > threshold else '0'
            binary_message += bit
            
            if len(binary_message) >= len(delimiter) and binary_message[-len(delimiter):] == delimiter:
                binary_message = binary_message[:-len(delimiter)]
                try:
                    padding = 8 - (len(binary_message) % 8) if len(binary_message) % 8 != 0 else 0
                    binary_message += '0' * padding
                    encrypted_message = binary_to_text(binary_message)
                    return decrypt(encrypted_message, password)
                except Exception as e:
                    return f"Failed to extract message: {str(e)}"
    
    return "No hidden message found"