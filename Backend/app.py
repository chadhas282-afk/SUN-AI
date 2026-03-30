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