import wave
import pvfalcon
import pveagle

# Replace with your Picovoice Access Key
ACCESS_KEY = "your access key"

# Paths for Falcon and Eagle models
FALCON_MODEL_PATH = "your path"
EAGLE_MODEL_PATH = "your path"

# Replace with the path to the input audio file
INPUT_AUDIO_PATH = "your input file"

# Create instances of Falcon and Eagle
try:
    falcon = pvfalcon.create(ACCESS_KEY, FALCON_MODEL_PATH)
    eagle_profiler = pveagle.create_profiler(ACCESS_KEY, EAGLE_MODEL_PATH)
except (pvfalcon.FalconError, pveagle.EagleError) as e:
    print(f"Failed to create instances: {e}")
    exit(1)

# Function to load enrollment audio data for each speaker from files
def get_enrollment_audio_data_for_speaker(speaker_index):
    # Replace the paths with the actual paths to the audio files for each speaker
    if speaker_index == 0:
        audio_file_path = "your input file"
    elif speaker_index == 1:
        audio_file_path = "your input file"
    elif speaker_index == 2:
        audio_file_path = "your input file"
    else:
        raise ValueError("Invalid speaker index")
    
    # Load audio data from the file
    with wave.open(audio_file_path, "r") as audio_file:
        sample_rate = audio_file.getframerate()
        sample_width = audio_file.getsampwidth()
        channels = audio_file.getnchannels()
        if sample_rate != falcon.sample_rate:
            raise ValueError("Sample rate of the audio file doesn't match Falcon's sample rate")
        if channels != 1:
            raise ValueError("Audio file must be mono (single channel)")
        if sample_width != 2:
            raise ValueError("Audio file must be 16-bit PCM")

        pcm_data = audio_file.readframes(audio_file.getnframes())
        samples = list(wave.struct.unpack(f"{len(pcm_data) // sample_width}h", pcm_data))
    
    return samples

# Enroll speakers with Eagle
speaker_profiles = []

speaker_names = ["Jon Anik", "Joe Rogan", "Daniel Cormier"] # Example of names

for i in range(3):  # Enroll three speakers
    print(f"Enrolling Speaker {i + 1} ({speaker_names[i]})...")
    percentage = 0.0
    while percentage < 100.0:
        try:
            # Load enrollment audio data for the current speaker
            enroll_data = get_enrollment_audio_data_for_speaker(i)
            percentage, feedback = eagle_profiler.enroll(enroll_data)
            print(f"Speaker {i + 1} enrollment progress: {percentage:.2f}%, Feedback: {feedback.name}")
        except Exception as e:
            print(f"Failed to enroll Speaker {i + 1}: {e}")
            break
    else:
        try:
            # Export the speaker profile if enrollment was successful
            speaker_profile = eagle_profiler.export()
            speaker_profiles.append(speaker_profile)
            print(f"Speaker {i + 1} ({speaker_names[i]}) enrolled successfully.")
        except pveagle.EagleError as e:
            print(f"Failed to export speaker profile for Speaker {i + 1} ({speaker_names[i]}): {e}")
            exit(1)

eagle_profiler.delete()

# Create an instance of Eagle for speaker recognition
try:
    eagle = pveagle.create_recognizer(ACCESS_KEY, speaker_profiles, EAGLE_MODEL_PATH)
except pveagle.EagleError as e:
    print(f"Failed to create Eagle instance: {e}")
    exit(1)

# Perform speaker diarization and recognition
with wave.open(INPUT_AUDIO_PATH, "r") as input_wave:
    sample_rate = input_wave.getframerate()
    channels = input_wave.getnchannels()
    sample_width = input_wave.getsampwidth()

    if sample_rate != falcon.sample_rate or sample_rate != eagle.sample_rate:
        print(f"Input sample rate: {sample_rate} Hz, Falcon/Eagle sample rate: {falcon.sample_rate}/{eagle.sample_rate} Hz")
        print("Input audio is not compatible with Falcon/Eagle: Incorrect sample rate")
        exit(1)
    if channels != 1:
        print(f"Input audio channels: {channels}, Falcon/Eagle channels: 1")
        print("Input audio is not compatible with Falcon/Eagle: Number of channels must be 1 (mono)")
        exit(1)
    if sample_width != 2:
        print(f"Input audio sample width: {sample_width} bytes, Falcon/Eagle sample width: 2 bytes")
        print("Input audio is not compatible with Falcon/Eagle: Sample width must be 2 bytes (16-bit PCM)")
        exit(1)

    pcm_data = input_wave.readframes(input_wave.getnframes())
    samples = list(wave.struct.unpack(f"{len(pcm_data) // sample_width}h", pcm_data))

    try:
        segments = falcon.process(samples)
    except pvfalcon.FalconError as e:
        print(f"Failed to process audio: {e}")
        exit(1)

    for segment in segments:
        start_sec, end_sec, speaker_tag = segment
        test_data = samples[int(start_sec * sample_rate):int(end_sec * sample_rate)]

        try:
            scores = eagle.process(test_data)
            max_score = max(scores)
            speaker_index = scores.index(max_score) + 1
            print(f"Speaker {speaker_index}: {start_sec:.2f} - {end_sec:.2f} seconds, Score: {max_score:.2f}")
        except pveagle.EagleError as e:
            print(f"Failed to process audio for recognition: {e}")
            continue

# Clean up resources
falcon.delete()
eagle.delete()