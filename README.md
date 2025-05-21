# Steganography Toolkit 🔐🖼️🔊🎥

A Python-based toolkit for **securely hiding and extracting secret messages** within images, audio, and video files using steganography techniques. All hidden messages are encrypted for added security.

---

## 🔧 Features

- 🖼️ **Image Steganography**: LSB & DCT techniques.
- 🔊 **Audio Steganography**: LSB & Echo Hiding.
- 🎥 **Video Steganography**: Frame-by-frame LSB embedding.
- 🔐 **Encryption**: All messages are encrypted using password-based Fernet encryption.
- 🧩 **Modular Design**: Easy to extend and maintain.
- 🖥️ **Command-Line Interface (CLI)** for user interaction.

---

## 📁 Code Structure

steg_project/   
│   
├── image_stego.py # Image steganography (LSB & DCT)  
├── audio_stego.py # Audio steganography (LSB & Echo)  
├── video_stego.py # Video steganography (LSB)  
├── crypto.py # Encryption and binary utilities  
└── main.py # CLI to run hide/extract commands     


---

## 💡 How It Works

### 🔒 Encryption
Before hiding, messages are encrypted using a password-derived key via PBKDF2 + Fernet. This adds a secure layer even if someone detects the stego content.

### 🧬 Delimiters
Each method appends a special delimiter (`1111111111111110`) to detect where the hidden message ends during extraction.

---

## 🛠️ Supported Methods

### 🖼️ Image Steganography
- **LSB**: Embeds binary message in the least significant bits of pixel RGB channels.
- **DCT**: Embeds message in DCT coefficients (frequency domain) — more resistant to compression.

### 🔊 Audio Steganography
- **LSB**: Modifies audio samples' least significant bits.
- **Echo Hiding**: Uses artificial echo delays to encode bits (e.g., 1ms for '0', 3ms for '1').

### 🎥 Video Steganography
- Embeds characters frame by frame using LSB in the RGB channels of selected pixels.
- Preserves audio and maintains synchronization.

---

## 🖱️ Command Line Usage

### 🔐 Hide a Message

```bash
python main.py hide [image|audio|video] [lsb|dct|echo] input_file output_file "Your secret message" --password yourpassword

```
### 🔓 Extract a Message
```
python main.py extract [image|audio|video] [lsb|dct|echo] input_file --password yourpassword
```
