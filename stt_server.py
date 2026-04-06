import os
import base64
import tempfile
import uvicorn
from fastapi import FastAPI, Request
from openai import AsyncOpenAI

try:
    import mlx_whisper
    import librosa
except ImportError:
    print("FATAL: Missing dependencies. Run `uv sync --extra mac-server`!")
    exit(1)

app = FastAPI()

# LM Studio endpoint
LM_STUDIO_URL = "http://localhost:1234/v1"
client = AsyncOpenAI(base_url=LM_STUDIO_URL, api_key="not-needed")

@app.post("/api/rocky_chat")
async def rocky_chat(request: Request):
    payload = await request.json()
    base64_audio = payload.get("audio_base64")
    system_prompt = payload.get("system_prompt", "You are Rocky.")
    
    print("\n[STT Proxy] Received Audio Stream from Raspberry Pi!")
    
    # 1. Expand Base64 payload back into a local `.wav` temp file
    audio_bytes = base64.b64decode(base64_audio)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
        
    print(" [STT Proxy] Bypassing FFmpeg: Decoding raw array natively...")
    # 2. Extract raw waveform array at 16000Hz (Bypasses mlx_whisper's FFmpeg requirement)
    waveform, sr = librosa.load(tmp_path, sr=16000)
        
    print(" [STT Proxy] Transcribing numeric audio vector with mlx-whisper...")
    try:
        # Transcribe with MLX Whisper using the native NumPy array
        result = mlx_whisper.transcribe(waveform, path_or_hf_repo="mlx-community/whisper-tiny")
        transcribed_text = result["text"].strip()
        print(f" [STT Proxy] Transcribed text: '{transcribed_text}'")
    except Exception as e:
        print(f" [STT Proxy] STT Error: {e}")
        os.remove(tmp_path)
        return {"error": str(e)}

    os.remove(tmp_path)
    
    if not transcribed_text:
         print(" [STT Proxy] No text detected.")
         return {"text": ""}

    print(" [STT Proxy] Sending text to LM Studio via OpenAI client...")
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcribed_text}
    ]
    
    try:
        response = await client.chat.completions.create(
            model="local-model", # LM Studio intercepts this automatically
            messages=messages,
            max_tokens=2048, # Increased drastically to account for Gemma's <reasoning> chain tokens
            temperature=0.7
        )
        
        reply = response.choices[0].message.content.strip()
        print(f" [STT Proxy] Reply from LM Studio: {reply[:80]}...")
        return {"text": reply}
    except Exception as e:
         print(f" [STT Proxy] LM Studio Error: {e}")
         return {"error": str(e)}

def main():
    print("🚀 Starting STT Proxy server on port 8000...")
    print("Ensure LM Studio is running locally on port 1234 with a model loaded.")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
