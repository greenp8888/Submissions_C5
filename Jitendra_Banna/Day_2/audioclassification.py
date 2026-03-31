from transformers import pipeline
import os
import torch
import soundfile as sf


# Load an audio classification pipeline
# We use a smaller model for demonstration purposes
classifier = pipeline("audio-classification", model="superb/wav2vec2-base-superb-ks")

# This is a simple sine wave, you would load your actual audio data
dummy_audio = torch.randn(16000) # 1 second of dummy audio at 16kHz
sf.write("dummy_audio.wav", dummy_audio.numpy(), 16000)


# Classify the audio
audio_file = "dummy_audio.wav"
audio_data, sample_rate = sf.read(audio_file)
predictions = classifier(audio_data, sample_rate=sample_rate)




# file_path = "supportfiles/smplesoundfile.wav"

# if os.path.exists(file_path):
#     print(f"✅ File found: {file_path}")
#     print(f"File size: {os.path.getsize(file_path)} bytes")
# else:
#     print(f"❌ File NOT found at: {os.path.abspath(file_path)}")
    
# # Load classifier
# classifier = pipeline("audio-classification", model="superb/wav2vec2-base-superb-ks")

# # Read your audio file with soundfile (no ffmpeg needed)
# audio_data, sample_rate = sf.read("supportfiles/smplesoundfile.wav")

# Pass the audio data directly to the classifier
# predictions = classifier(audio_data, sampling_rate=sample_rate)

print("Audio Classification Results:")
for prediction in predictions:
    print(f"- {prediction['label']}: {prediction['score']:.2f}")