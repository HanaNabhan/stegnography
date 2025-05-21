import cv2
import os
import unicodedata
from utils.crypto import encrypt, decrypt
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

def hide_message_in_video(video_path: str, message: str, password: str, output_path: str = None) -> str:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not output_path:
        output_path = "video_steganography.avi"
    
    encrypted_message = encrypt(message, password)
    
    encrypted_message = unicodedata.normalize('NFKD', encrypted_message).encode('ascii', 'ignore').decode('ascii')
    
    message_words = [ch for ch in encrypted_message]
    
    start_frame = 10
    
    first_delimiter = "^$^"
    word_delimiter = "^*^"
    frame_delimiter = "^#^"
    
    metadata = f"{first_delimiter}{start_frame}{word_delimiter}"
    
    prepared_words = []
    for i, word in enumerate(message_words):
        if i == len(message_words) - 1:
            prepared_words.append(word + frame_delimiter)
        else:
            prepared_words.append(word + word_delimiter)
    
    vidcap = cv2.VideoCapture(video_path)
    
    if not vidcap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}. Make sure it's a valid video file.")
    
    frame_width = int(vidcap.get(3))
    frame_height = int(vidcap.get(4))
    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    
    if frame_width <= 0 or frame_height <= 0 or fps <= 0:
        vidcap.release()
        raise ValueError(f"Invalid video dimensions or frame rate. Make sure {video_path} is a valid video file.")
    
    total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    required_frames = start_frame + len(prepared_words)
    if total_frames < required_frames:
        vidcap.release()
        raise ValueError(
            f"Video has only {total_frames} frames but {required_frames} are needed. "
            f"Choose a shorter message or a longer video."
        )
    
    try:
        fourcc = cv2.VideoWriter_fourcc(*'FFV1')
        out = cv2.VideoWriter('stego_TEMP.avi', fourcc, fps=fps, frameSize=(frame_width, frame_height))
        
        if not out.isOpened():
            vidcap.release()
            raise RuntimeError(
                "Failed to create output video file. "
                "Check if the codec is supported and you have write permissions."
            )
    except Exception as e:
        vidcap.release()
        raise RuntimeError(f"Error creating output video: {str(e)}")
    
    try:
        frame_number = 0
        frames_processed = 0
        while vidcap.isOpened():
            frame_number += 1
            ret, frame = vidcap.read()
            
            if not ret:
                break
            
            frames_processed += 1
            
            if frame_number == 1:
                frame = _lsb_hide_frame(frame, metadata)
            
            elif start_frame <= frame_number < start_frame + len(prepared_words):
                word_index = frame_number - start_frame
                frame = _lsb_hide_frame(frame, prepared_words[word_index])
            
            out.write(frame)
        
        if frames_processed < required_frames:
            raise ValueError(
                f"Video ended prematurely. Processed {frames_processed} frames but needed {required_frames}."
            )
    
    except Exception as e:
        vidcap.release()
        out.release()
        cv2.destroyAllWindows()
        if os.path.exists('stego_TEMP.avi'):
            os.remove('stego_TEMP.avi')
        raise RuntimeError(f"Error processing video: {str(e)}")
    
    vidcap.release()
    out.release()
    cv2.destroyAllWindows()
    
    try:
        _combine_video_audio(video_path, output_path)
    except Exception as e:
        if os.path.exists('stego_TEMP.avi'):
            os.remove('stego_TEMP.avi')
        if os.path.exists('audio_TEMP.mp3'):
            os.remove('audio_TEMP.mp3')
        raise RuntimeError(f"Error combining video and audio: {str(e)}")
    
    print(f"Message successfully hidden in {output_path}")
    return message

def extract_message_from_video(video_path: str, password: str) -> str:
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    vidcap = cv2.VideoCapture(video_path)
    
    if not vidcap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}. Make sure it's a valid video file.")
    
    first_delimiter = "^$^"
    word_delimiter = "^*^"
    frame_delimiter = "^#^"
    
    frame_number = 0
    start_frame = None
    extracted_words = []
    
    try:
        while vidcap.isOpened():
            frame_number += 1
            ret, frame = vidcap.read()
            
            if not ret:
                break
            
            if frame_number == 1:
                metadata = _lsb_extract_frame(frame)
                
                if metadata and first_delimiter in metadata:
                    metadata_parts = metadata.split(first_delimiter)
                    if len(metadata_parts) > 1:
                        metadata = metadata_parts[1]
                        
                        if word_delimiter in metadata:
                            start_frame_str = metadata.split(word_delimiter)[0]
                            try:
                                start_frame = int(start_frame_str)
                            except ValueError:
                                print("Invalid metadata format")
                                return "No valid hidden message found"
                        else:
                            print("No word delimiter found in metadata")
                            return "Invalid metadata format"
                    else:
                        print("Invalid first delimiter format")
                        return "Invalid metadata format"
                else:
                    print("No steganography metadata found in video")
                    return "No hidden message found"
            
            elif start_frame and frame_number >= start_frame:
                word = _lsb_extract_frame(frame)
                
                if not word:
                    continue
                
                if frame_delimiter in word:
                    word = word.split(frame_delimiter)[0]
                    extracted_words.append(word)
                    break
                
                elif word_delimiter in word:
                    word = word.split(word_delimiter)[0]
                    extracted_words.append(word)
                else:
                    extracted_words.append(word)
    except Exception as e:
        vidcap.release()
        cv2.destroyAllWindows()
        raise RuntimeError(f"Error extracting message from video: {str(e)}")
    finally:
        vidcap.release()
        cv2.destroyAllWindows()
    
    if not extracted_words:
        return "No hidden message found"
    
    encrypted_message = ''.join(extracted_words)
    
    try:
        decrypted_message = decrypt(encrypted_message, password)
        return decrypted_message
    except Exception as e:
        print(f"Error decrypting message: {str(e)}")
        return f"Failed to decrypt message (possibly incorrect password): {str(e)}"

def _lsb_hide_frame(frame, data):
    binary_data = ''.join(format(ord(char), '07b') for char in data)
    length_data = len(binary_data)
    
    padding_needed = (3 - (length_data % 3)) % 3
    binary_data += '0' * padding_needed
    length_data = len(binary_data)
    
    index_data = 0
    pixel_count = 0
    
    modified_frame = frame.copy()
    
    for i in range(frame.shape[0]):
        for j in range(frame.shape[1]):
            pixel_count += 1
            
            if pixel_count % 4 == 0:
                continue
            
            pixel = modified_frame[i, j]
            
            if index_data + 3 <= length_data:
                modified_frame[i, j, 0] = (pixel[0] & 0xFE) | int(binary_data[index_data])
                modified_frame[i, j, 1] = (pixel[1] & 0xFE) | int(binary_data[index_data + 1])
                modified_frame[i, j, 2] = (pixel[2] & 0xFE) | int(binary_data[index_data + 2])
                index_data += 3
            else:
                if index_data < length_data:
                    modified_frame[i, j, 0] = (pixel[0] & 0xFE) | int(binary_data[index_data])
                    index_data += 1
                
                if index_data < length_data:
                    modified_frame[i, j, 1] = (pixel[1] & 0xFE) | int(binary_data[index_data])
                    index_data += 1
                
                if index_data < length_data:
                    modified_frame[i, j, 2] = (pixel[2] & 0xFE) | int(binary_data[index_data])
                    index_data += 1
            
            if index_data >= length_data:
                return modified_frame
    
    print(f"Warning: Frame too small to hide all data. Only {index_data}/{length_data} bits were hidden.")
    return modified_frame

def _lsb_extract_frame(frame):
    MAX_CHARS = 150
    binary_data = ""
    extracted_chars = []
    pixel_count = 0
    
    for i in range(frame.shape[0]):
        for j in range(frame.shape[1]):
            pixel = frame[i, j]
            pixel_count += 1
            
            if pixel_count % 4 == 0:
                continue
            
            binary_data += str(pixel[0] & 1)
            binary_data += str(pixel[1] & 1)
            binary_data += str(pixel[2] & 1)
            
            while len(binary_data) >= 7:
                char_code = int(binary_data[:7], 2)
                char = chr(char_code)
                extracted_chars.append(char)
                binary_data = binary_data[7:]
                
                current_text = ''.join(extracted_chars[-10:])
                
                if "^*^" in current_text or "^#^" in current_text:
                    return ''.join(extracted_chars)
            
            if len(extracted_chars) > MAX_CHARS:
                full_text = ''.join(extracted_chars)
                if "^*^" in full_text or "^#^" in full_text:
                    return full_text
                
                return full_text
    
    if extracted_chars:
        return ''.join(extracted_chars)
    
    return None

def _combine_video_audio(video_path, output_path):
    print("Combining video with original audio...")
    
    original_clip = VideoFileClip(video_path)
    original_clip.audio.write_audiofile("audio_TEMP.mp3", logger=None)
    
    audio_clip = AudioFileClip("audio_TEMP.mp3")
    
    video_clip = VideoFileClip("stego_TEMP.avi")
    
    final_clip = video_clip.with_audio(audio_clip)
    
    final_clip.write_videofile(output_path, codec="ffv1", audio_codec="aac", logger=None)
    
    original_clip.close()
    audio_clip.close()
    video_clip.close()
    final_clip.close()
    
    if os.path.exists("audio_TEMP.mp3"):
        os.remove("audio_TEMP.mp3")
    if os.path.exists("stego_TEMP.avi"):
        os.remove("stego_TEMP.avi")
    
    print(f"Video steganography completed: {output_path}")
