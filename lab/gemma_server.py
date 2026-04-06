import os
import base64
import tempfile
from fastapi import FastAPI, Request
import uvicorn
from transformers import AutoProcessor, AutoModelForCausalLM

try:
    import torch
except ImportError:
    print("FATAL: Missing dependencies!")
    exit(1)

app = FastAPI()

# Pointing natively to the Official HuggingFace Source
MODEL_ID = "google/gemma-4-e2b-it" 

print(f"Loading Official {MODEL_ID} Pipeline (Approx ~4GB Download)...")
try:
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    
    # Explicitly map the tensor storage directly into CPU! 
    # An 8GB Mac physically cannot map a single 4.38GB block into the Metal 'mps' GPU without an OOM crash.
    # CPU forces Mac OS to use Unified Swap memory gracefully (it will run slightly slower, but will not crash!)
    device_str = "cpu"
    print(f"Forcing allocation into absolute memory grid: {device_str.upper()}...")
    
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16).to(device_str)
    print("\n✅ Gemma 4 Native Initialization Complete! Listening on port 8000...\n")
except Exception as e:
    print(f"\n❌ Error initializing model: {e}")
    print("NOTE: You must accept the terms on HF and login via `huggingface-cli login` if this crashes on 401!")
    exit(1)


@app.post("/api/rocky_chat")
async def rocky_chat(request: Request):
    payload = await request.json()
    base64_audio = payload.get("audio_base64")
    system_prompt = payload.get("system_prompt", "You are Rocky.")
    
    print("\n[Native Pipeline] Received Audio Stream from Raspberry Pi!")
    
    audio_bytes = base64.b64decode(base64_audio)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
        
    print(" - Processing audio array...")

    # Using Gemma 4's exact dynamic Template format for multi-modal processing
    conversation = [
         {"role": "user", "content": [
            {"type": "audio", "url": tmp_path}, 
            {"type": "text", "text": "You are Rocky! Listen to the audio and respond textually: " + system_prompt}
         ]}
    ]

    print(" - Applying Chat Template & Tokens...")
    inputs = processor.apply_chat_template(
        conversation, 
        tokenize=True, 
        return_dict=True, 
        return_tensors="pt", 
        add_generation_prompt=True
    ).to(model.device)
    
    print(" - Tensor generation started...")
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=400)
        
    # Gemma returns the outputs combined with prompts, so we slice the inputs off!
    generated_ids = outputs[0][inputs.input_ids.shape[-1]:]
    response = processor.decode(generated_ids, skip_special_tokens=True).strip()
    
    print(f" - Native Response Generated: {response[:40]}...")
    os.remove(tmp_path)
    return {"text": response}

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
