import torch
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    torch_dtype=torch.float16, 
    device_map="auto"
)

async def generate_tokens(prompt: str, request: Request):
    messages = [
        {
            "role": "system", 
            "content": "You are Lumina, an expert developer. Always provide code snippets inside Markdown triple backticks."
        },
        {"role": "user", "content": prompt},
    ]
    
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
        timeout=20.0, 
        skip_prompt=True, 
        skip_special_tokens=True
    )
    
    gen_kwargs = dict(
        input_ids=input_ids, 
        streamer=streamer,
        max_new_tokens=1024,
        do_sample=True,
        temperature=0.4,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id
    )

    thread = Thread(target=model.generate, kwargs=gen_kwargs)
    thread.start()

    try:
        for new_text in streamer:
            if await request.is_disconnected():
                break 
            
            if new_text:
                print(new_text, end="", flush=True)
                yield f"data: {json.dumps({'text': new_text})}\n\n"
            
            await asyncio.sleep(0.01)
            
    except Exception as e:
        print(f"\nStreaming Error: {e}")
        yield f"data: {json.dumps({'text': ' [Stream Error]'})}\n\n"
    finally:
        thread.join(timeout=1.0)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    return StreamingResponse(
        
    )