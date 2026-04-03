import torch
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Model & Tokenizer
model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_id)

# Optimization: Using SDPA for faster inference kernels
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    torch_dtype=torch.float16, 
    device_map="auto",
    attn_implementation="sdpa" 
)

async def generate_tokens(prompt: str, request: Request):
    messages = [
        {"role": "system", "content": "You are Lumina, a high-speed expert developer."},
        {"role": "user", "content": prompt},
    ]
    
    # Generate the input tensor
    # .apply_chat_template with return_tensors="pt" returns the tensor directly
    inputs = tokenizer.apply_chat_template(
    messages, 
    add_generation_prompt=True, 
    return_tensors="pt"
    ).to(model.device)
    if isinstance(inputs, torch.Tensor):
        input_ids = inputs
    else:
        input_ids = inputs["input_ids"]

    streamer = TextIteratorStreamer(
        tokenizer, 
        timeout=10.0, 
        skip_prompt=True, 
        skip_special_tokens=True
    )
    
    gen_kwargs = dict(
        input_ids=input_ids,  # Now passing the Tensor, not the dict
        streamer=streamer,
        max_new_tokens=1024,
        do_sample=True,
        temperature=0.5,
        top_p=0.9,
        use_cache=True,
        pad_token_id=tokenizer.eos_token_id
    )

    # Start generation in a background thread to prevent blocking the API
    thread = Thread(target=model.generate, kwargs=gen_kwargs)
    thread.start()

    async def stream_iterator():
        try:
            for new_text in streamer:
                if await request.is_disconnected():
                    break
                
                if new_text:
                    # Yielding data as SSE (Server-Sent Events)
                    yield f"data: {json.dumps({'text': new_text})}\n\n"
                
                # Yield control to event loop; 0 delay for max speed
                await asyncio.sleep(0)
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            thread.join(timeout=1.0)

    return stream_iterator()

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    
    event_generator = await generate_tokens(prompt, request)
    return StreamingResponse(event_generator, media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)