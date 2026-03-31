from transformers import pipeline
import soundfile as sf
import torch

# Load the automatic speech recognition pipeline
print("Loading ASR model...")
transcriber = pipeline("automatic-speech-recognition", model="facebook/wav2vec2-base-960h")

# This is just for demonstration purposes. In a real scenario, you would load your audio file.
#audio_file = r"D:\eng-accelerator\Submissions_C5\Jitendra_Banna\day_2\supportfiles\sample.m4a"# Dummy data for 1 second of audio at 16kHz
#sf.write("/supportfiles/sample.m4a", audio_data, 16000)

# Create dummy audio data (1 second of random noise)
sample_rate = 16000
duration = 3  # seconds
dummy_audio = torch.randn(sample_rate * duration).numpy()  # Convert to numpy array
sf.write("dummy_audio.wav", dummy_audio, sample_rate)
print("✅ Created dummy_audio.wav")

# Transcribe the audio
audio_file = "dummy_audio.wav" # Using the dummy audio created previously
audio_data, sample_rate = sf.read(audio_file)
transcription = transcriber(audio_data, sample_rate=sample_rate)

print("Transcription:")
print(transcription)
