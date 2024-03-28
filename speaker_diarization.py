import wave
import pvfalcon

ACCESS_KEY = "your access key"

MODEL_PATH = "your path"

INPUT_AUDIO_PATH = "your input audio file"

# Create a Falcon instance
try:
    falcon = pvfalcon.create(ACCESS_KEY, MODEL_PATH)
except pvfalcon.FalconError as e:
    print(f"Failed to create Falcon instance: {e}")
    exit(1)

# Open the input audio file
with wave.open(INPUT_AUDIO_PATH, "r") as input_wave:
    # Get audio parameters
    sample_rate = input_wave.getframerate()
    channels = input_wave.getnchannels()
    sample_width = input_wave.getsampwidth()

    # Check if the input audio is compatible with Falcon
    if sample_rate != falcon.sample_rate:
        print(f"Input sample rate: {sample_rate} Hz, Falcon sample rate: {falcon.sample_rate} Hz")
        print("Input audio is not compatible with Falcon: Incorrect sample rate")
        exit(1)
    if channels != 1:
        print(f"Input audio channels: {channels}, Falcon channels: 1")
        print("Input audio is not compatible with Falcon: Number of channels must be 1 (mono)")
        exit(1)
    if sample_width != 2:
        print(f"Input audio sample width: {sample_width} bytes, Falcon sample width: 2 bytes")
        print("Input audio is not compatible with Falcon: Sample width must be 2 bytes (16-bit PCM)")
        exit(1)

    # Process the audio data
    pcm_data = input_wave.readframes(input_wave.getnframes())
    samples = list(wave.struct.unpack(f"{len(pcm_data) // sample_width}h", pcm_data))

    try:
        segments = falcon.process(samples)
    except pvfalcon.FalconError as e:
        print(f"Failed to process audio: {e}")
        exit(1)

    # Print the diarization output
    speaker_labels = {}
    for segment in segments:
        start_sec, end_sec, speaker_tag = segment
        if speaker_tag not in speaker_labels:
            speaker_labels[speaker_tag] = f"Speaker {len(speaker_labels) + 1}"
        
        speaker_label = speaker_labels[speaker_tag]
        print(f"{speaker_label}: {start_sec:.2f} - {end_sec:.2f} seconds")

# Clean up resources
falcon.delete()