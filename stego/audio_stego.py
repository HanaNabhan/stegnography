import wave
import numpy as np
from utils.crypto import text_to_binary, binary_to_text, encrypt, decrypt
from scipy.io import wavfile

def hide_message_in_audio_lsb(audio_path: str, message: str, password: str, output_path: str) -> None:
    encrypted_message = encrypt(message, password)
    binary_message = text_to_binary(encrypted_message) + '1111111111111110'
    
    with wave.open(audio_path, 'rb') as wav:
        n_channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        frame_rate = wav.getframerate()
        n_frames = wav.getnframes()
        
        frames = wav.readframes(n_frames)
    
    max_message_bits = len(frames) * 8 // sample_width
    if len(binary_message) > max_message_bits:
        raise ValueError(f"Message too large to hide in this audio. Max size: {max_message_bits // 8} bytes")
    
    if sample_width == 1:
        dtype = np.uint8
    elif sample_width == 2:
        dtype = np.int16
    else:
        raise ValueError("Unsupported sample width")
    
    samples = np.frombuffer(frames, dtype=dtype)
    
    binary_array = np.array([int(bit) for bit in binary_message], dtype=np.uint8)
    
    modified_samples = samples.copy()
    
    message_length = len(binary_array)
    
    modified_samples[:message_length] &= ~1
    
    modified_samples[:message_length] |= binary_array
    
    modified_frames = modified_samples.tobytes()
    
    with wave.open(output_path, 'wb') as wav_out:
        wav_out.setparams((n_channels, sample_width, frame_rate, len(modified_samples), 'NONE', 'not compressed'))
        wav_out.writeframes(modified_frames)
    
    print(f"Message successfully hidden in {output_path}")

def extract_message_from_audio_lsb(audio_path: str, password: str) -> str:
    with wave.open(audio_path, 'rb') as wav:
        sample_width = wav.getsampwidth()
        n_frames = wav.getnframes()
        
        frames = wav.readframes(n_frames)
    
    if sample_width == 1:
        dtype = np.uint8
    elif sample_width == 2:
        dtype = np.int16
    else:
        raise ValueError("Unsupported sample width")
    
    samples = np.frombuffer(frames, dtype=dtype)
    
    lsb_array = samples & 1
    
    binary_message = ''.join(map(str, lsb_array))
    
    delimiter = '1111111111111110'
    pos = binary_message.find(delimiter)
    
    if pos >= 0:
        binary_message = binary_message[:pos]
        try:
            padding = 8 - (len(binary_message) % 8) if len(binary_message) % 8 != 0 else 0
            binary_message += '0' * padding
            encrypted_message = binary_to_text(binary_message)
            return decrypt(encrypted_message, password)
        except Exception as e:
            return f"Failed to extract message: {str(e)}"
    
    return "No hidden message found"

def hide_message_in_audio_echo(audio_path: str, message: str, password: str, output_path: str) -> None:
    encrypted_message = encrypt(message, password)
    binary_message = text_to_binary(encrypted_message)
    
    rate, audio = wavfile.read(audio_path)
    original_audio = audio.copy()
    
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)
        if audio.dtype == np.int16:
            audio = audio / 32767.0
    
    if len(audio.shape) > 1:
        audio = audio[:, 0]
    
    decay = 0.6
    delay_0 = int(rate * 0.001)
    delay_1 = int(rate * 0.003)
    
    segment_length = int(rate * 0.1)
    num_segments = len(audio) // segment_length
    if len(binary_message) > num_segments:
        raise ValueError(f"Message too large. Max length: {num_segments//8} bytes")
    
    binary_message += '1111111111111110'
    
    output_audio = np.copy(audio)
    
    for i in range(len(binary_message)):
        if i >= num_segments:
            break
        
        start = i * segment_length
        end = min((i + 1) * segment_length, len(audio))
        segment = audio[start:end]
        
        delay = delay_1 if binary_message[i] == '1' else delay_0
        
        echo = np.zeros_like(segment)
        echo[delay:] = segment[:-delay] * decay if delay < len(segment) else segment * 0
        
        output_segment = segment + echo
        
        max_val = np.max(np.abs(output_segment))
        if max_val > 1.0:
            output_segment = output_segment / max_val
        
        output_audio[start:end] = output_segment
    
    if original_audio.dtype == np.int16:
        output_audio = (output_audio * 32767.0).astype(np.int16)
    
    if len(original_audio.shape) > 1 and original_audio.shape[1] > 1:
        output_stereo = np.column_stack((output_audio, original_audio[:len(output_audio), 1]))
        wavfile.write(output_path, rate, output_stereo)
    else:
        wavfile.write(output_path, rate, output_audio)
    
    print(f"Message successfully hidden in {output_path} (echo hiding)")

def extract_message_from_audio_echo(audio_path: str, password: str) -> str:
    rate, audio = wavfile.read(audio_path)
    
    if len(audio.shape) > 1:
        audio = audio[:, 0]
    
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)
        if audio.dtype == np.int16:
            audio = audio / 32767.0
    
    delay_0 = int(rate * 0.001)
    delay_1 = int(rate * 0.003)
    segment_length = int(rate * 0.1)
    
    tolerance = 2
    
    extracted_bits = []
    
    num_segments = len(audio) // segment_length
    for i in range(num_segments):
        start = i * segment_length
        end = min((i + 1) * segment_length, len(audio))
        segment = audio[start:end]
        
        windowed_segment = segment * np.hamming(len(segment))
        spectrum = np.fft.fft(windowed_segment)
        log_spectrum = np.log(np.abs(spectrum) + 1e-10)
        cepstrum = np.fft.ifft(log_spectrum).real
        
        cepstrum = cepstrum[:len(cepstrum)//2]
        
        sum_0 = np.sum(cepstrum[max(0, delay_0-tolerance):min(len(cepstrum), delay_0+tolerance)])
        sum_1 = np.sum(cepstrum[max(0, delay_1-tolerance):min(len(cepstrum), delay_1+tolerance)])
        
        bit = '1' if sum_1 > sum_0 else '0'
        extracted_bits.append(bit)
    
    binary_message = ''.join(extracted_bits)
    
    delimiter = '1111111111111110'
    pos = binary_message.find(delimiter)
    
    if pos >= 0:
        binary_message = binary_message[:pos]
        try:
            padding = 8 - (len(binary_message) % 8) if len(binary_message) % 8 != 0 else 0
            binary_message += '0' * padding
            
            encrypted_message = binary_to_text(binary_message)
            
            return decrypt(encrypted_message, password)
        except Exception as e:
            return f"Failed to extract message: {str(e)}"
    
    return "No hidden message found"

