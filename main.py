
import argparse
from stego.image_stego import hide_message_in_image_lsb, extract_message_from_image_lsb, hide_message_in_image_dct, extract_message_from_image_dct
from stego.audio_stego import hide_message_in_audio_lsb, extract_message_from_audio_lsb, hide_message_in_audio_echo, extract_message_from_audio_echo
from stego.video_stego import hide_message_in_video, extract_message_from_video
# from analysis.steganalysis import 

def main():
    parser = argparse.ArgumentParser(description="Steganography Application: Hide and extract messages in images, audio, and video files")
    
    # Main command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Hide command
    hide_parser = subparsers.add_parser("hide", help="Hide a message in a file")
    hide_parser.add_argument("file_type", choices=["image", "audio", "video"], help="Type of file to hide message in")
    hide_parser.add_argument("method", help="Method to use for hiding (lsb, dct, echo)")
    hide_parser.add_argument("input_file", help="Path to the input file")
    hide_parser.add_argument("output_file", help="Path to save the output file")
    hide_parser.add_argument("message", help="Message to hide")
    hide_parser.add_argument("--password", required=True, help="Password for encryption")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract a hidden message from a file")
    extract_parser.add_argument("file_type", choices=["image", "audio", "video"], help="Type of file to extract message from")
    extract_parser.add_argument("method", help="Method used for hiding (lsb, dct, echo)")
    extract_parser.add_argument("input_file", help="Path to the file with hidden message")
    extract_parser.add_argument("--password", required=True, help="Password for decryption")
    
    # Analyze command
    # analyze_parser = subparsers.add_parser("analyze", help="Analyze a file for potential hidden messages")
    # analyze_parser.add_argument("method", choices=["histogram , extra..."], help="Analysis method")
    # analyze_parser.add_argument("input_file", help="Path to the file to analyze")
    # analyze_parser.add_argument("--reference", help="Path to reference file (for histogram comparison)")
    
    args = parser.parse_args()
    
    # Process commands
    if args.command == "hide":
        if args.file_type == "image":
            if args.method.lower() == "lsb":
                hide_message_in_image_lsb(args.input_file, args.message, args.password, args.output_file)
            elif args.method.lower() == "dct":
                hide_message_in_image_dct(args.input_file, args.message, args.password, args.output_file)
            else:
                print(f"Unsupported method '{args.method}' for image steganography")
        
        elif args.file_type == "audio":
            if args.method.lower() == "lsb":
                hide_message_in_audio_lsb(args.input_file, args.message, args.password, args.output_file)
            elif args.method.lower() == "echo":
                hide_message_in_audio_echo(args.input_file, args.message, args.password, args.output_file)
            else:
                print(f"Unsupported method '{args.method}' for audio steganography")
        
        elif args.file_type == "video":
            if args.method.lower() == "lsb":
                hide_message_in_video(args.input_file, args.message, args.password, args.output_file)
            else:
                print(f"Unsupported method '{args.method}' for video steganography")
    
    elif args.command == "extract":
        if args.file_type == "image":
            if args.method.lower() == "lsb":
                message = extract_message_from_image_lsb(args.input_file, args.password)
            elif args.method.lower() == "dct":
                message = extract_message_from_image_dct(args.input_file, args.password)
            else:
                print(f"Unsupported method '{args.method}' for image steganography")
                return
        
        elif args.file_type == "audio":
            if args.method.lower() == "lsb":
                message = extract_message_from_audio_lsb(args.input_file, args.password)
            elif args.method.lower() == "echo":
                message = extract_message_from_audio_echo(args.input_file, args.password)
            else:
                print(f"Unsupported method '{args.method}' for audio steganography")
                return
        
        elif args.file_type == "video":
            if args.method.lower() == "lsb":
                message = extract_message_from_video(args.input_file, args.password)
            else:
                print(f"Unsupported method '{args.method}' for video steganography")
                return
        
        print(f"Extracted message: {message}")
    
    # elif args.command == "analyze":
    #     if args.method == "histogram":
    #         analyze_image_histogram(args.input_file, args.reference)

if __name__ == "__main__":
    main()