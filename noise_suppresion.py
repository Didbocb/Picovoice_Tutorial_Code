import wave
import pvkoala

ACCESS_KEY = "your access key"

MODEL_PATH = "your path"

INPUT_AUDIO_PATH = "your input audio file"

OUTPUT_AUDIO_PATH = "your output audio file"

# Create a Koala instance
try:
    koala = pvkoala.create(ACCESS_KEY)
except pvkoala.KoalaError as e:
    print(f"Failed to create Koala instance: {e}")
    exit(1)

# Open the input audio file
with wave.open(INPUT_AUDIO_PATH, "r") as input_wave:
    # Get audio parameters
    sample_rate = input_wave.getframerate()
    channels = input_wave.getnchannels()
    sample_width = input_wave.getsampwidth()
    
    # Check if the input audio is compatible with Koala
    if sample_rate != koala.sample_rate:
        print(f"Input sample rate: {sample_rate} Hz, Koala sample rate: {koala.sample_rate} Hz")
        print("Input audio is not compatible with Koala: Incorrect sample rate")
        exit(1)

    if channels != 1:
        print(f"Input audio channels: {channels}, Koala channels: 1")
        print("Input audio is not compatible with Koala: Number of channels must be 1 (mono)")
        exit(1)

    if sample_width != 2:
        print(f"Input audio sample width: {sample_width} bytes, Koala sample width: 2 bytes")
        print("Input audio is not compatible with Koala: Sample width must be 2 bytes (16-bit PCM)")
        exit(1)


    # Open the output audio file
    with wave.open(OUTPUT_AUDIO_PATH, "w") as output_wave:
        output_wave.setframerate(sample_rate)
        output_wave.setnchannels(1)
        output_wave.setsampwidth(2)

        # Process the audio frame by frame
        while True:
            frame = input_wave.readframes(koala.frame_length)
            if not frame:
                break

            # Convert the frame to a list of samples
            samples = list(wave.struct.unpack(f"{len(frame) // sample_width}h", frame))

            # Process the frame with Koala
            try:
                enhanced_samples = koala.process(samples)
            except pvkoala.KoalaError as e:
                print(f"Failed to process frame: {e}")
                continue

            # Convert the enhanced samples back to bytes
            enhanced_frame = wave.struct.pack(f"{len(enhanced_samples)}h", *enhanced_samples)

            # Write the enhanced frame to the output file
            output_wave.writeframes(enhanced_frame)

    print("Noise suppression completed successfully.")

# Clean up resources
koala.delete()