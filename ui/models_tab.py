# ============================================================
#  FreedomForge AI — ui/models_tab.py
#  Model browser — curated list grouped by size
# ============================================================

import os
import queue
import shutil
import threading
import webbrowser
from tkinter import filedialog

import customtkinter as ctk
import requests

from core import model_manager
from assets.i18n import t

from utils.paths import MODELS_DIR as _MODELS_DIR_PATH
MODELS_DIR = str(_MODELS_DIR_PATH)

CURATED = [
    # ── Small (≤4 GB RAM) ────────────────────────────────────────────────────
    {
        "name":     "TinyLlama 1.1B",
        "badge":    "⚡ Best for low-end PCs",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size": "670 MB", "ram": "2 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Tiny but surprisingly capable. Runs on almost anything.",
    },
    {
        "name":     "Qwen2.5 0.5B",
        "badge":    "🐣 Pocket-sized",
        "filename": "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "size": "350 MB", "ram": "2 GB+",
        "tags": ["small", "chat", "multilingual"],
        "desc": "Smallest model available. Surprisingly articulate for its size.",
    },
    {
        "name":     "SmolLM2 1.7B",
        "badge":    "🌱 Fast & light",
        "filename": "SmolLM2-1.7B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/SmolLM2-1.7B-Instruct-GGUF/resolve/main/SmolLM2-1.7B-Instruct-Q4_K_M.gguf",
        "size": "1.0 GB", "ram": "2 GB+",
        "tags": ["small", "chat"],
        "desc": "Tiny instruction model. Punches well above its weight.",
    },
    {
        "name":     "Phi-2 2.7B",
        "badge":    "🧠 Smart and compact",
        "filename": "phi-2.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
        "size": "1.6 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "coding", "chat"],
        "desc": "Compact powerhouse. Excellent at reasoning, coding, and writing.",
    },
    {
        "name":     "Phi-3.5 Mini 3.8B",
        "badge":    "🔷 Latest Phi-3.5",
        "filename": "Phi-3.5-mini-instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf",
        "size": "2.3 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "coding", "chat"],
        "desc": "Beats models 3× its size on benchmarks. Fast and efficient.",
    },
    {
        "name":     "Phi-4 Mini 3.8B",
        "badge":    "🔷 Phi-4 series",
        "filename": "phi-4-mini-instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/phi-4-mini-instruct-GGUF/resolve/main/phi-4-mini-instruct-Q4_K_M.gguf",
        "size": "2.3 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "coding", "chat"],
        "desc": "Latest Phi-4 generation. Best-in-class small model.",
    },
    {
        "name":     "Llama 3.2 3B",
        "badge":    "🦙 Meta — compact",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size": "2.0 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Meta's latest compact model. Fast, capable, fully open source.",
    },
    {
        "name":     "Gemma 2 2B",
        "badge":    "🔵 Google — compact",
        "filename": "gemma-2-2b-it-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf",
        "size": "1.6 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Google's compact instruction model. Clean, fast, capable.",
    },
    {
        "name":     "Qwen2.5 3B",
        "badge":    "🌏 Multilingual small",
        "filename": "Qwen2.5-3B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
        "size": "1.9 GB", "ram": "4 GB+",
        "tags": ["small", "chat", "multilingual"],
        "desc": "Strong multilingual and coding ability in a 3B package.",
    },
    # ── Medium (6–12 GB RAM) ─────────────────────────────────────────────────
    {
        "name":     "Mistral 7B Instruct",
        "badge":    "⚖️ Best all-rounder",
        "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat"],
        "desc": "The gold standard for local AI. Excellent at everything.",
    },
    {
        "name":     "Mistral Nemo 12B",
        "badge":    "🌊 128k context",
        "filename": "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF/resolve/main/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        "size": "7.1 GB", "ram": "12 GB+",
        "tags": ["popular", "chat"],
        "desc": "128k context window, multilingual, powerful.",
    },
    {
        "name":     "Dolphin Mistral 7B",
        "badge":    "🐬 Uncensored",
        "filename": "dolphin-2.2.1-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/dolphin-2.2.1-mistral-7B-GGUF/resolve/main/dolphin-2.2.1-mistral-7b.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["uncensored", "chat"],
        "desc": "Fine-tuned to never refuse. Loyal, direct, completely open.",
    },
    {
        "name":     "Dolphin Llama 3 8B",
        "badge":    "🐬 Uncensored + Powerful",
        "filename": "dolphin-2.9-llama3-8b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/dolphin-2.9-llama3-8b-GGUF/resolve/main/dolphin-2.9-llama3-8b-Q4_K_M.gguf",
        "size": "4.9 GB", "ram": "10 GB+",
        "tags": ["uncensored", "chat"],
        "desc": "Dolphin on Llama 3. Powerful, uncensored, deeply loyal.",
    },
    {
        "name":     "Llama 3.1 8B Instruct",
        "badge":    "🦙 Most popular 8B",
        "filename": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "size": "4.9 GB", "ram": "10 GB+",
        "tags": ["popular", "chat"],
        "desc": "Meta's flagship open source model. State of the art for 8B.",
    },
    {
        "name":     "Llama 3.2 11B Vision",
        "badge":    "👁️ Vision model",
        "filename": "Llama-3.2-11B-Vision-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Llama-3.2-11B-Vision-Instruct-GGUF/resolve/main/Llama-3.2-11B-Vision-Instruct-Q4_K_M.gguf",
        "size": "6.8 GB", "ram": "12 GB+",
        "tags": ["vision", "chat"],
        "desc": "Llama 3.2 with vision. See images, screenshots, charts, and more.",
    },
    {
        "name":     "Gemma 2 9B",
        "badge":    "🔵 Google — 9B",
        "filename": "gemma-2-9b-it-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it-Q4_K_M.gguf",
        "size": "5.8 GB", "ram": "10 GB+",
        "tags": ["popular", "chat"],
        "desc": "Google's mid-size model. Outperforms many larger models.",
    },
    {
        "name":     "Qwen2.5 7B",
        "badge":    "🌏 Multilingual 7B",
        "filename": "qwen2.5-7b-instruct-q4_k_m.gguf",
        "url":      "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "size": "4.7 GB", "ram": "8 GB+",
        "tags": ["multilingual", "chat"],
        "desc": "Strong multilingual model. English, Chinese, and many more.",
    },
    {
        "name":     "Qwen2.5 14B",
        "badge":    "🌏 Multilingual 14B",
        "filename": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Qwen2.5-14B-Instruct-GGUF/resolve/main/Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "size": "8.9 GB", "ram": "12 GB+",
        "tags": ["multilingual", "chat"],
        "desc": "Excellent reasoning, math, and code in many languages.",
    },
    {
        "name":     "OpenHermes 2.5 Mistral",
        "badge":    "🧙 Smart assistant",
        "filename": "openhermes-2.5-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/resolve/main/openhermes-2.5-mistral-7b.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat"],
        "desc": "Fine-tuned on high quality instructions. Sharp and reliable.",
    },
    {
        "name":     "Nous Hermes 2 7B",
        "badge":    "🏛️ Deep reasoning",
        "filename": "Nous-Hermes-2-Mistral-7B-DPO.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Nous-Hermes-2-Mistral-7B-DPO-GGUF/resolve/main/Nous-Hermes-2-Mistral-7B-DPO.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat"],
        "desc": "DPO fine-tuned for coherent, detailed long-form answers.",
    },
    {
        "name":     "Zephyr 7B",
        "badge":    "💨 RLHF fine-tuned",
        "filename": "zephyr-7b-beta.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/zephyr-7B-beta-GGUF/resolve/main/zephyr-7b-beta.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat"],
        "desc": "RLHF fine-tuned for helpfulness and honesty. Solid all-rounder.",
    },
    {
        "name":     "Neural Chat 7B",
        "badge":    "🤝 Conversational",
        "filename": "neural-chat-7b-v3-3.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/neural-chat-7B-v3-3-GGUF/resolve/main/neural-chat-7b-v3-3.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["chat"],
        "desc": "Optimized for conversational AI. Very natural tone.",
    },
    {
        "name":     "Yi 1.5 9B",
        "badge":    "🌐 32k context",
        "filename": "Yi-1.5-9B-Chat-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Yi-1.5-9B-Chat-GGUF/resolve/main/Yi-1.5-9B-Chat-Q4_K_M.gguf",
        "size": "5.5 GB", "ram": "10 GB+",
        "tags": ["popular", "chat", "multilingual"],
        "desc": "Exceptional reasoning and 32k token context window.",
    },
    {
        "name":     "Orca 2 7B",
        "badge":    "🐋 Reasoning model",
        "filename": "orca-2-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Orca-2-7B-GGUF/resolve/main/orca-2-7b.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["chat"],
        "desc": "Trained with step-by-step reasoning techniques. Thinks before answering.",
    },
    {
        "name":     "WizardLM 2 7B",
        "badge":    "🪄 Complex instructions",
        "filename": "WizardLM-2-7B.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/WizardLM-2-7B-GGUF/resolve/main/WizardLM-2-7B-Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["chat"],
        "desc": "Exceptional at following complex, multi-step instructions.",
    },
    # ── Coding ───────────────────────────────────────────────────────────────
    {
        "name":     "CodeLlama 7B",
        "badge":    "💻 Coding specialist",
        "filename": "codellama-7b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf",
        "size": "3.8 GB", "ram": "8 GB+",
        "tags": ["coding"],
        "desc": "Fine-tuned specifically for code. Write, debug, explain any language.",
    },
    {
        "name":     "DeepSeek Coder 6.7B",
        "badge":    "💻 Best code model",
        "filename": "deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF/resolve/main/deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
        "size": "3.8 GB", "ram": "8 GB+",
        "tags": ["coding"],
        "desc": "Dedicated coding model. Exceptional at writing and reviewing code.",
    },
    {
        "name":     "StarCoder2 7B",
        "badge":    "⭐ 600+ languages",
        "filename": "starcoder2-7b-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/starcoder2-7b-GGUF/resolve/main/starcoder2-7b-Q4_K_M.gguf",
        "size": "4.4 GB", "ram": "8 GB+",
        "tags": ["coding"],
        "desc": "Trained on 600+ programming languages. Great for niche languages.",
    },
    {
        "name":     "DeepSeek-R1 7B",
        "badge":    "🧮 Reasoning + Code",
        "filename": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "size": "4.7 GB", "ram": "8 GB+",
        "tags": ["coding", "chat"],
        "desc": "Thinks step-by-step. Strong at math and code reasoning.",
    },
    {
        "name":     "DeepSeek-R1 14B",
        "badge":    "🧮 Chain-of-thought",
        "filename": "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
        "size": "9.0 GB", "ram": "16 GB+",
        "tags": ["coding", "chat"],
        "desc": "Shows full chain-of-thought reasoning. Exceptional at math.",
    },
    # ── Vision ───────────────────────────────────────────────────────────────
    {
        "name":     "Llava 1.6 Mistral 7B",
        "badge":    "👁️ Can see images",
        "filename": "llava-v1.6-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/cjpais/llava-1.6-mistral-7b-gguf/resolve/main/llava-v1.6-mistral-7b.Q4_K_M.gguf",
        "size": "4.4 GB", "ram": "8 GB+",
        "tags": ["vision"],
        "desc": "Multimodal — describe images, read charts, answer visual questions.",
    },
    {
        "name":     "MiniCPM-V 2.6 8B",
        "badge":    "👁️ Advanced vision",
        "filename": "MiniCPM-V-2_6-Q4_K_M.gguf",
        "url":      "https://huggingface.co/openbmb/MiniCPM-V-2_6-gguf/resolve/main/MiniCPM-V-2_6-Q4_K_M.gguf",
        "size": "5.2 GB", "ram": "10 GB+",
        "tags": ["vision", "chat"],
        "desc": "Reads text in images, understands charts, tables, and screenshots.",
    },
    # ── Large (16+ GB RAM) ───────────────────────────────────────────────────
    {
        "name":     "Llama 3.3 70B (Q2)",
        "badge":    "🦙 Near GPT-4 quality",
        "filename": "Llama-3.3-70B-Instruct-Q2_K.gguf",
        "url":      "https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF/resolve/main/Llama-3.3-70B-Instruct-Q2_K.gguf",
        "size": "26 GB", "ram": "32 GB+",
        "tags": ["popular", "chat"],
        "desc": "70B quantized to Q2. Frontier-level quality. High-end machine required.",
    },
    {
        "name":     "Qwen2.5 32B",
        "badge":    "🌏 Flagship 32B",
        "filename": "Qwen2.5-32B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Qwen2.5-32B-Instruct-GGUF/resolve/main/Qwen2.5-32B-Instruct-Q4_K_M.gguf",
        "size": "20 GB", "ram": "24 GB+",
        "tags": ["multilingual", "chat"],
        "desc": "Best-in-class large model. Exceptional reasoning and multilingual.",
    },
    {
        "name":     "Mixtral 8x7B",
        "badge":    "🚀 Mixture of experts",
        "filename": "mixtral-8x7b-instruct-v0.1.Q3_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF/resolve/main/mixtral-8x7b-instruct-v0.1.Q3_K_M.gguf",
        "size": "19 GB", "ram": "24 GB+",
        "tags": ["popular", "chat"],
        "desc": "Mixture-of-experts architecture. Frontier quality at local speeds.",
    },
    # ── Additional models ────────────────────────────────────────────────────
    {
        "name":     "Phi-3 Mini 4K",
        "badge":    "⚡ Super light",
        "filename": "Phi-3-mini-4k-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Phi-3-mini-4k-instruct-GGUF/resolve/main/Phi-3-mini-4k-instruct-Q4_K_M.gguf",
        "size": "2.2 GB", "ram": "4 GB+",
        "tags": ["small", "coding", "chat"],
        "desc": "Compact and fast. Strong at reasoning and code. Runs on low-end hardware.",
    },
    {
        "name":     "Llama 3.2 1B",
        "badge":    "🦙 Smallest Llama",
        "filename": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "size": "740 MB", "ram": "2 GB+",
        "tags": ["small", "chat"],
        "desc": "Meta's smallest Llama 3.2. Ideal for devices with very limited RAM.",
    },
    {
        "name":     "Mistral 7B v0.3",
        "badge":    "⚖️ Improved Mistral",
        "filename": "Mistral-7B-Instruct-v0.3.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat"],
        "desc": "Mistral v0.3 with function-calling support. Polished and reliable.",
    },
    {
        "name":     "Dolphin 3.0 Llama 3.1 8B",
        "badge":    "🐬 Uncensored v3",
        "filename": "dolphin-3.0-llama3.1-8b-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/dolphin-3.0-llama3.1-8b-GGUF/resolve/main/dolphin-3.0-llama3.1-8b-Q4_K_M.gguf",
        "size": "4.9 GB", "ram": "10 GB+",
        "tags": ["uncensored", "chat"],
        "desc": "Dolphin 3.0 — latest uncensored series. Follows any instruction without refusal.",
    },
    {
        "name":     "Qwen2.5 Coder 7B",
        "badge":    "💻 Coding powerhouse",
        "filename": "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
        "size": "4.7 GB", "ram": "8 GB+",
        "tags": ["coding"],
        "desc": "Qwen2.5's dedicated coder. Tops many code benchmarks at the 7B level.",
    },
    {
        "name":     "Gemma 2 27B",
        "badge":    "🔵 Google flagship",
        "filename": "gemma-2-27b-it-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/gemma-2-27b-it-GGUF/resolve/main/gemma-2-27b-it-Q4_K_M.gguf",
        "size": "16.4 GB", "ram": "24 GB+",
        "tags": ["popular", "chat"],
        "desc": "Google's largest open Gemma model. Exceptional quality across all tasks.",
    },
    {
        "name":     "Hermes 3 Llama 3.1 8B",
        "badge":    "🏛️ Hermes 3",
        "filename": "Hermes-3-Llama-3.1-8B.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Hermes-3-Llama-3.1-8B-GGUF/resolve/main/Hermes-3-Llama-3.1-8B-Q4_K_M.gguf",
        "size": "4.9 GB", "ram": "10 GB+",
        "tags": ["popular", "chat"],
        "desc": "Hermes 3 on Llama 3.1. Excellent instruction following and roleplay.",
    },
    {
        "name":     "Nous Hermes Mixtral 8x7B",
        "badge":    "🏛️ Hermes MoE",
        "filename": "Nous-Hermes-2-Mixtral-8x7B-DPO.Q3_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-GGUF/resolve/main/Nous-Hermes-2-Mixtral-8x7B-DPO.Q3_K_M.gguf",
        "size": "17 GB", "ram": "24 GB+",
        "tags": ["popular", "chat"],
        "desc": "Nous Hermes DPO on Mixtral. Best large uncensored-capable assistant.",
    },
    {
        "name":     "Magicoder S 7B",
        "badge":    "✨ OSS code gen",
        "filename": "Magicoder-S-DS-6.7B.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Magicoder-S-DS-6.7B-GGUF/resolve/main/Magicoder-S-DS-6.7B.Q4_K_M.gguf",
        "size": "3.8 GB", "ram": "8 GB+",
        "tags": ["coding"],
        "desc": "Trained on OSS-Instruct data. Writes clean, idiomatic open-source code.",
    },
    {
        "name":     "Falcon 7B Instruct",
        "badge":    "🦅 Falcon series",
        "filename": "falcon-7b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/falcon-7b-instruct-GGUF/resolve/main/falcon-7b-instruct.Q4_K_M.gguf",
        "size": "4.2 GB", "ram": "8 GB+",
        "tags": ["chat"],
        "desc": "TII's Falcon 7B. Trained on a massive web dataset. Solid general assistant.",
    },
]

def _ram_gb(ram_str: str) -> int:
    try:
        return int(ram_str.split()[0])
    except Exception:
        return 0

SMALL  = [m for m in CURATED if _ram_gb(m["ram"]) <= 4]
MEDIUM = [m for m in CURATED if 4 < _ram_gb(m["ram"]) <= 12]
LARGE  = [m for m in CURATED if _ram_gb(m["ram"]) > 12]


class ModelsPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app            = app
        self.theme          = theme
        self._local_models  = []
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        self._rebuild()

    def _rebuild(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        # ── Header ───────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=56)
        hdr.pack(fill="x", padx=22, pady=(20, 0))
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="📦  Model Library",
            font=("Arial", 22, "bold"),
            text_color=T["text_primary"],
        ).pack(side="left", anchor="w")

        ctk.CTkLabel(
            hdr, text="Download once — runs 100% on your machine",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(side="left", padx=16, anchor="w")

        ctk.CTkButton(
            hdr, text="↻  Refresh",
            width=90, height=30,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            command=self._rebuild,
        ).pack(side="right", padx=4)

        # ── My Models card ────────────────────────────────────
        my_card = ctk.CTkFrame(self, corner_radius=10, fg_color=T["bg_card"])
        my_card.pack(fill="x", padx=12, pady=(10, 0))

        my_hdr = ctk.CTkFrame(my_card, fg_color="transparent")
        my_hdr.pack(fill="x", padx=14, pady=(10, 6))

        ctk.CTkLabel(
            my_hdr, text="📂  My Models",
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            my_hdr, text="🔍 Scan Computer for Models",
            width=210, height=28, corner_radius=6,
            fg_color=T["bg_hover"], hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            font=("Arial", 11),
            command=self._scan_computer,
        ).pack(side="right")

        self._my_models_frame = ctk.CTkFrame(my_card, fg_color="transparent")
        self._my_models_frame.pack(fill="x", padx=14, pady=(0, 10))
        self._refresh_my_models()

        # ── Single scrollable grouped list ───────────────────
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=12, pady=(10, 0))

        # ── Bottom search / add bar ───────────────────────────
        bot = ctk.CTkFrame(self, fg_color=T["bg_topbar"], height=54)
        bot.pack(fill="x", pady=(4, 0))
        bot.pack_propagate(False)

        self._search_var = ctk.StringVar()
        entry = ctk.CTkEntry(
            bot,
            textvariable=self._search_var,
            placeholder_text="Search models…",
            font=("Arial", 12), height=36,
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_color=T["border"],
            placeholder_text_color=T["text_secondary"],
        )
        entry.pack(side="left", fill="both", expand=True, padx=(16, 6), pady=9)
        entry.bind("<Return>", lambda _: self._do_search())

        ctk.CTkButton(
            bot, text="Search",
            width=90, height=36, corner_radius=8,
            fg_color=T["accent"], hover_color=T["accent_hover"],
            command=self._do_search,
        ).pack(side="left", padx=(0, 6), pady=9)

        ctk.CTkButton(
            bot, text="📁 Add Local File",
            width=130, height=36, corner_radius=8,
            fg_color=T["bg_card"], hover_color=T["bg_hover"],
            text_color=T["text_secondary"],
            command=self._add_local,
        ).pack(side="left", padx=(0, 16), pady=9)

        self._populate_list()
        threading.Thread(target=self._probe_local, daemon=True).start()

    # ── Populate grouped list ────────────────────────────────

    def _populate_list(self, prepend=None):
        T = self.theme
        for w in self._scroll.winfo_children():
            w.destroy()

        if prepend:
            self._section_header("✅  Installed")
            for m in prepend:
                self._installed_row(m)
            self._divider()

        groups = [
            ("⚡  Small  —  runs on almost anything  (2–4 GB RAM)", SMALL),
            ("⚖️  Medium  —  8 GB+ RAM recommended",                MEDIUM),
            ("🚀  Large  —  16 GB+ RAM recommended",                LARGE),
        ]
        first = True
        for header, models in groups:
            if not first:
                self._divider()
            first = False
            self._section_header(header)
            for m in models:
                self._model_row(m)

    def _section_header(self, text: str):
        T = self.theme
        ctk.CTkLabel(
            self._scroll, text=text,
            font=("Arial", 13, "bold"),
            text_color=T["text_secondary"],
            anchor="w",
        ).pack(anchor="w", padx=10, pady=(12, 4))

    def _divider(self):
        ctk.CTkFrame(
            self._scroll, height=2,
            fg_color=self.theme["divider"],
        ).pack(fill="x", pady=(6, 2), padx=4)

    # ── Installed (local) row ────────────────────────────────

    def _probe_local(self):
        """Show any .gguf files already in MODELS_DIR as 'Installed'."""
        try:
            files = [f for f in os.listdir(MODELS_DIR) if f.endswith(".gguf")]
            if files:
                self._local_models = files
                self.after(0, lambda: self._populate_list(files))
        except Exception:
            pass

    def _refresh_my_models(self):
        """Rebuild the My Models row list from model_manager + MODELS_DIR."""
        T = self.theme
        for w in self._my_models_frame.winfo_children():
            w.destroy()

        try:
            models = model_manager.get_model_list()
        except Exception:
            models = []

        # Also include any .gguf files on disk not yet in manager
        try:
            on_disk = [f for f in os.listdir(MODELS_DIR) if f.endswith(".gguf")]
            for f in on_disk:
                if f not in models:
                    models.append(f)
        except Exception:
            pass

        if not models:
            ctk.CTkLabel(
                self._my_models_frame,
                text="No models yet — download one below or scan your computer.",
                font=("Arial", 11), text_color=T["text_dim"], anchor="w",
            ).pack(anchor="w", pady=4)
            return

        for filename in models:
            loaded = model_manager.get_current_model() == filename
            row = ctk.CTkFrame(self._my_models_frame, fg_color=T["bg_input"],
                               corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row, text=filename,
                font=("Arial", 12), text_color=T["text_primary"], anchor="w",
            ).pack(side="left", padx=10, pady=6, fill="x", expand=True)

            if loaded:
                ctk.CTkLabel(row, text="▶ Active",
                             font=("Arial", 11, "bold"),
                             text_color=T["gold"]).pack(side="right", padx=10)
            else:
                ctk.CTkButton(
                    row, text="▶ Load",
                    width=80, height=26, corner_radius=6,
                    fg_color=T["accent"], hover_color=T["accent_hover"],
                    text_color="#ffffff", font=("Arial", 11),
                    command=lambda fn=filename: self._load(fn),
                ).pack(side="right", padx=(4, 10), pady=4)

    def _scan_computer(self):
        """Walk common directories for .gguf files and show results in a popup."""
        T   = self.theme
        win = ctk.CTkToplevel(self)
        win.title("Scan for Models")
        win.geometry("700x480")
        win.configure(fg_color=T["bg_panel"])

        def _on_close():
            win.destroy()
            try:
                self.winfo_toplevel().focus_force()
            except Exception:
                pass
        win.protocol("WM_DELETE_WINDOW", _on_close)

        ctk.CTkLabel(
            win, text="🔍  Scanning your computer for .gguf files…",
            font=("Arial", 14, "bold"), text_color=T["text_primary"],
        ).pack(pady=(18, 4), padx=20, anchor="w")

        status_lbl = ctk.CTkLabel(
            win, text="Scanning…",
            font=("Arial", 11), text_color=T["text_secondary"],
        )
        status_lbl.pack(padx=20, anchor="w")

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=8)

        found_paths = []

        def _scan():
            home = os.path.expanduser("~")
            search_roots = [
                os.path.join(home, "Downloads"),
                os.path.join(home, "Documents"),
                os.path.join(home, "Desktop"),
                "/mnt",
            ]
            results = []
            for root_dir in search_roots:
                if not os.path.isdir(root_dir):
                    continue
                try:
                    for dirpath, dirnames, filenames in os.walk(root_dir):
                        # Skip hidden dirs and venvs
                        dirnames[:] = [
                            d for d in dirnames
                            if not d.startswith(".") and d not in (".venv", "venv", "__pycache__")
                        ]
                        for fname in filenames:
                            if fname.endswith(".gguf"):
                                results.append(os.path.join(dirpath, fname))
                        win.after(0, lambda p=dirpath: status_lbl.configure(
                            text=f"Scanning: …{p[-60:]}" if len(p) > 60 else f"Scanning: {p}"))
                except Exception:
                    continue
            win.after(0, lambda: _show_results(results))

        def _show_results(results):
            status_lbl.configure(
                text=f"Found {len(results)} model file{'s' if len(results) != 1 else ''}."
                     + ("" if results else " Nothing found in Downloads, Documents, Desktop, /mnt.")
            )
            found_paths.clear()
            found_paths.extend(results)

            for w in scroll.winfo_children():
                w.destroy()

            if not results:
                ctk.CTkLabel(
                    scroll, text="No .gguf files found.",
                    font=("Arial", 12), text_color=T["text_dim"],
                ).pack(pady=20)
                return

            for fpath in results:
                fname   = os.path.basename(fpath)
                already = os.path.exists(os.path.join(MODELS_DIR, fname))

                row = ctk.CTkFrame(scroll, corner_radius=8, fg_color=T["bg_card"])
                row.pack(fill="x", pady=3, padx=4)

                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="both", expand=True, padx=12, pady=8)

                ctk.CTkLabel(info, text=fname,
                             font=("Arial", 12, "bold"),
                             text_color=T["text_primary"], anchor="w").pack(anchor="w")
                ctk.CTkLabel(info, text=fpath,
                             font=("Arial", 9), text_color=T["text_dim"],
                             anchor="w").pack(anchor="w")

                if already:
                    ctk.CTkLabel(row, text="✅ Already added",
                                 font=("Arial", 11), text_color=T["green"],
                                 ).pack(side="right", padx=12, pady=8)
                else:
                    ctk.CTkButton(
                        row, text="➕ Add",
                        width=80, height=30, corner_radius=6,
                        fg_color=T["accent"], hover_color=T["accent_hover"],
                        text_color="#ffffff",
                        command=lambda src=fpath, fn=fname, r=row: _add_file(src, fn, r),
                    ).pack(side="right", padx=12, pady=8)

        def _add_file(src, fname, row):
            try:
                os.makedirs(MODELS_DIR, exist_ok=True)
                dest = os.path.join(MODELS_DIR, fname)
                if not os.path.exists(dest):
                    shutil.copy2(src, dest)
                # Replace the Add button with a confirmation label
                for w in row.winfo_children():
                    try:
                        if hasattr(w, 'cget') and w.cget('text') == "➕ Add":
                            w.destroy()
                    except Exception:
                        pass
                ctk.CTkLabel(row, text="✅ Added",
                             font=("Arial", 11), text_color=T["green"],
                             ).pack(side="right", padx=12, pady=8)
                self._refresh_my_models()
            except Exception as e:
                ctk.CTkLabel(row, text=f"❌ {e}",
                             font=("Arial", 10), text_color=T.get("red", "#ff4444"),
                             ).pack(side="right", padx=12, pady=8)

        threading.Thread(target=_scan, daemon=True).start()

    def _installed_row(self, filename):
        T      = self.theme
        loaded = model_manager.get_current_model() == filename
        row    = ctk.CTkFrame(self._scroll, corner_radius=10, fg_color=T["bg_card"])
        row.pack(fill="x", pady=3, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        ctk.CTkLabel(
            info, text=filename,
            font=("Arial", 13, "bold"),
            text_color=T["text_primary"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text="On disk",
            font=("Arial", 10),
            text_color=T["text_dim"], anchor="w",
        ).pack(anchor="w")

        if loaded:
            ctk.CTkLabel(
                row, text="▶ Running",
                font=("Arial", 12, "bold"),
                text_color=T["gold"],
            ).pack(side="right", padx=12, pady=10)
        else:
            ctk.CTkButton(
                row, text="▶ Load",
                width=90, height=34, corner_radius=8,
                fg_color=T["accent"], hover_color=T["accent_hover"],
                text_color="#ffffff",
                command=lambda fn=filename: self._load(fn),
            ).pack(side="right", padx=12, pady=10)

    # ── Curated model row ────────────────────────────────────

    def _model_row(self, m: dict):
        T      = self.theme
        have   = os.path.exists(os.path.join(MODELS_DIR, m["filename"]))
        loaded = model_manager.get_current_model() == m["filename"]

        row = ctk.CTkFrame(self._scroll, corner_radius=10, fg_color=T["bg_card"])
        row.pack(fill="x", pady=3, padx=4)

        # Info column
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        # Name + status
        title_row = ctk.CTkFrame(info, fg_color="transparent")
        title_row.pack(anchor="w", fill="x")

        ctk.CTkLabel(
            title_row, text=m["name"],
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"], anchor="w",
        ).pack(side="left")

        if loaded:
            ctk.CTkLabel(title_row, text="  ▶ Active",
                         font=("Arial", 11, "bold"),
                         text_color=T["gold"]).pack(side="left")
        elif have:
            ctk.CTkLabel(title_row, text="  ✅",
                         font=("Arial", 11),
                         text_color=T["green"]).pack(side="left")

        # Badge + desc
        ctk.CTkLabel(
            info, text=m["badge"],
            font=("Arial", 11),
            text_color=T["text_secondary"], anchor="w",
        ).pack(anchor="w", pady=(1, 0))

        ctk.CTkLabel(
            info, text=m["desc"],
            font=("Arial", 11),
            text_color=T["text_dim"],
            anchor="w", wraplength=520, justify="left",
        ).pack(anchor="w")

        # Size + RAM chips
        chips = ctk.CTkFrame(info, fg_color="transparent")
        chips.pack(anchor="w", pady=(5, 0))
        for val in [m["size"], f"RAM: {m['ram']}"]:
            ctk.CTkLabel(
                chips, text=val,
                font=("Arial", 10),
                text_color=T["text_dim"],
                fg_color=T["bg_hover"],
                corner_radius=4, width=100,
            ).pack(side="left", padx=(0, 6))

        # Action button
        btn_wrap = ctk.CTkFrame(row, fg_color="transparent", width=124)
        btn_wrap.pack(side="right", padx=12, pady=10)
        btn_wrap.pack_propagate(False)

        if loaded:
            ctk.CTkLabel(
                btn_wrap, text="▶ Running",
                font=("Arial", 12, "bold"),
                text_color=T["gold"],
            ).pack(expand=True)
        elif have:
            ctk.CTkButton(
                btn_wrap, text="▶ Load",
                height=36, corner_radius=8,
                fg_color="#1a4a1a", hover_color="#0d2e0d",
                text_color="#ffffff",
                command=lambda fn=m["filename"]: self._load(fn),
            ).pack(fill="x", pady=(0, 4))
            ctk.CTkButton(
                btn_wrap, text="🗑 Delete",
                height=22, corner_radius=6,
                fg_color="#2a1212", hover_color="#3a1a1a",
                text_color=T["text_secondary"],
                font=("Arial", 10),
                command=lambda fn=m["filename"]: self._delete(fn),
            ).pack(fill="x")
        else:
            ctk.CTkButton(
                btn_wrap, text="⬇ Download",
                height=36, corner_radius=8,
                fg_color=T["accent"], hover_color=T["accent_hover"],
                text_color="#ffffff",
                command=lambda mo=m: self._download(mo),
            ).pack(fill="x")

    # ── Search ───────────────────────────────────────────────

    def _do_search(self):
        query = self._search_var.get().strip()
        if not query:
            return
        T = self.theme

        for w in self._scroll.winfo_children():
            w.destroy()

        ctk.CTkButton(
            self._scroll, text="← Back to catalog",
            width=140, height=28,
            fg_color=T["bg_hover"], hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            font=("Arial", 11), anchor="w",
            command=self._back_to_catalog,
        ).pack(anchor="w", pady=(4, 8))

        status = ctk.CTkLabel(
            self._scroll,
            text=f"🔍  Searching for \"{query}\"…",
            font=("Arial", 13),
            text_color=T["text_secondary"],
        )
        status.pack(pady=40)

        def _search():
            try:
                r = requests.get(
                    f"https://huggingface.co/api/models"
                    f"?search={query}&filter=gguf&sort=downloads&limit=20&full=false",
                    timeout=12)
                r.raise_for_status()
                results = r.json()
                self.after(0, lambda: self._render_search(results, query, status))
            except Exception as e:
                self.after(0, lambda: status.configure(
                    text=f"❌  Search failed: {e}",
                    text_color=T.get("red", "#ff4444")))

        threading.Thread(target=_search, daemon=True).start()

    def _render_search(self, results: list, query: str, status):
        T = self.theme
        try:
            status.destroy()
        except Exception:
            pass

        if not results:
            ctk.CTkLabel(
                self._scroll,
                text=f"No models found for \"{query}\".",
                font=("Arial", 13),
                text_color=T["text_secondary"],
            ).pack(pady=20)
            return

        ctk.CTkLabel(
            self._scroll,
            text=f"{len(results)} models found — click a result to view files",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))

        for model in results:
            self._search_result_row(model)

    def _search_result_row(self, model: dict):
        T         = self.theme
        model_id  = model.get("modelId", model.get("id", "Unknown"))
        downloads = model.get("downloads", 0)

        row = ctk.CTkFrame(self._scroll, corner_radius=10, fg_color=T["bg_card"])
        row.pack(fill="x", pady=4, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        # Strip "author/" prefix for display — no external brand shown
        display_name = model_id.split("/")[-1] if "/" in model_id else model_id
        ctk.CTkLabel(
            info, text=display_name,
            font=("Arial", 13, "bold"),
            text_color=T["text_primary"], anchor="w",
        ).pack(anchor="w")

        if downloads:
            ctk.CTkLabel(
                info, text=f"⬇ {downloads:,} downloads",
                font=("Arial", 10),
                text_color=T["text_secondary"],
            ).pack(anchor="w")

        ctk.CTkButton(
            row, text="View Files",
            width=100, height=32, corner_radius=8,
            fg_color=T["accent"], hover_color=T["accent_hover"],
            text_color="#ffffff",
            command=lambda mid=model_id: self._show_files(mid),
        ).pack(side="right", padx=12, pady=10)

    def _back_to_catalog(self):
        self._populate_list(self._local_models or None)

    # ── File browser for search results ──────────────────────

    def _show_files(self, model_id: str):
        T   = self.theme
        # Use display name (strip author/)
        display = model_id.split("/")[-1] if "/" in model_id else model_id
        win = ctk.CTkToplevel(self)
        win.title(display)
        win.geometry("720x520")
        win.configure(fg_color=T["bg_panel"])

        def _on_close():
            win.destroy()
            try:
                self.winfo_toplevel().focus_force()
            except Exception:
                pass

        win.protocol("WM_DELETE_WINDOW", _on_close)

        ctk.CTkLabel(
            win, text=display,
            font=("Arial", 15, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(18, 2), padx=22, anchor="w")

        ctk.CTkLabel(
            win, text="Select a file to download",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(padx=22, anchor="w")

        status = ctk.CTkLabel(
            win, text="Loading files…",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        )
        status.pack(pady=20)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        def _fetch():
            try:
                r    = requests.get(
                    f"https://huggingface.co/api/models/{model_id}", timeout=12)
                r.raise_for_status()
                data  = r.json()
                files = [
                    s for s in data.get("siblings", [])
                    if s.get("rfilename", "").endswith(".gguf")
                ]
                win.after(0, lambda: _show(files))
            except Exception as e:
                win.after(0, lambda: status.configure(
                    text=f"❌  {e}",
                    text_color=T.get("red", "#ff4444")))

        def _show(files: list):
            try:
                status.destroy()
            except Exception:
                pass

            if not files:
                ctk.CTkLabel(
                    scroll, text="No downloadable files found.",
                    text_color=T["text_secondary"],
                ).pack(pady=20)
                return

            for f in files:
                fname    = f.get("rfilename", "")
                size_b   = f.get("size", 0)
                size_str = (
                    f"{size_b/(1024**3):.1f} GB"
                    if size_b > 1024**3
                    else f"{size_b/(1024**2):.0f} MB"
                    if size_b else "?"
                )
                frow = ctk.CTkFrame(scroll, corner_radius=8, fg_color=T["bg_card"])
                frow.pack(fill="x", pady=4, padx=2)

                fi = ctk.CTkFrame(frow, fg_color="transparent")
                fi.pack(side="left", fill="both", expand=True, padx=12, pady=8)

                ctk.CTkLabel(
                    fi, text=fname,
                    font=("Arial", 12, "bold"),
                    text_color=T["text_primary"], anchor="w",
                ).pack(anchor="w")
                ctk.CTkLabel(
                    fi, text=size_str,
                    font=("Arial", 10),
                    text_color=T["text_secondary"], anchor="w",
                ).pack(anchor="w")

                dl_url = f"https://huggingface.co/{model_id}/resolve/main/{fname}"
                have   = os.path.exists(os.path.join(MODELS_DIR, fname))

                if have:
                    ctk.CTkLabel(
                        frow, text="✅ Downloaded",
                        font=("Arial", 11),
                        text_color=T["green"],
                    ).pack(side="right", padx=12, pady=10)
                else:
                    ctk.CTkButton(
                        frow, text="⬇ Download",
                        width=116, height=32, corner_radius=8,
                        fg_color=T["accent"], hover_color=T["accent_hover"],
                        text_color="#ffffff",
                        command=lambda u=dl_url, fn=fname: (
                            _on_close(),
                            self._download({
                                "name":     fn,
                                "filename": fn,
                                "url":      u,
                                "size":     size_str,
                                "ram":      "?",
                                "desc":     f"From {display}",
                            })
                        ),
                    ).pack(side="right", padx=12, pady=8)

        threading.Thread(target=_fetch, daemon=True).start()

    # ── Actions ──────────────────────────────────────────────

    def _load(self, filename: str):
        self.app.load_model(filename)
        self.app.switch_panel("Chat")

    def _delete(self, filename: str):
        path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(path):
            os.remove(path)
        self.refresh()

    def _download(self, model: dict):
        DownloadWindow(self, model, self.theme, self.refresh)

    def _add_local(self):
        path = filedialog.askopenfilename(
            title="Select a model file",
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")])
        if path:
            os.makedirs(MODELS_DIR, exist_ok=True)
            dest = os.path.join(MODELS_DIR, os.path.basename(path))
            shutil.copy2(path, dest)
            self.refresh()
            try:
                self.app.chat_panel.sys_message(
                    f"✅  Added {os.path.basename(path)}")
            except Exception:
                pass

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()


# ── Download window ──────────────────────────────────────────

class DownloadWindow(ctk.CTkToplevel):

    def __init__(self, parent, model: dict, theme: dict, on_done=None):
        super().__init__(parent)
        self.on_done = on_done
        self._q      = queue.Queue()
        T            = theme

        self.title("Downloading")
        self.geometry("540x210")
        self.resizable(False, False)
        self.configure(fg_color=T["bg_panel"])

        ctk.CTkLabel(
            self,
            text=f"⬇  {model.get('name', model['filename'])}",
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(22, 4))

        self.bar = ctk.CTkProgressBar(
            self, width=480,
            progress_color=T["accent"],
            fg_color=T["bg_card"],
        )
        self.bar.set(0)
        self.bar.pack(pady=8)

        self.lbl = ctk.CTkLabel(
            self, text="Connecting…",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        )
        self.lbl.pack()

        ctk.CTkLabel(
            self, text="You can minimize this window while downloading.",
            font=("Arial", 10),
            text_color=T["text_dim"],
        ).pack(pady=4)

        threading.Thread(target=self._dl, args=(model,), daemon=True).start()
        self._poll()

    def _dl(self, model: dict):
        try:
            os.makedirs(MODELS_DIR, exist_ok=True)
            r     = requests.get(model["url"], stream=True, timeout=60)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done  = 0
            dest  = os.path.join(MODELS_DIR, model["filename"])
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        self._q.put(("p", done / total, done, total))
            self._q.put(("done", None))
        except Exception as e:
            self._q.put(("error", str(e)))

    def _poll(self):
        try:
            while True:
                msg = self._q.get_nowait()
                if msg[0] == "p":
                    _, pct, done, total = msg
                    self.bar.set(pct)
                    self.lbl.configure(
                        text=f"{done/(1024**2):.1f} MB / "
                             f"{total/(1024**2):.1f} MB  ({pct*100:.1f}%)"
                    )
                elif msg[0] == "done":
                    self.bar.set(1.0)
                    self.lbl.configure(text="✅  Download complete!")
                    self.after(1400, self._finish)
                    return
                elif msg[0] == "error":
                    self.lbl.configure(text=f"❌  {msg[1]}")
                    return
        except queue.Empty:
            pass
        self.after(110, self._poll)

    def _finish(self):
        if self.on_done:
            self.on_done()
        try:
            self.destroy()
        except Exception:
            pass

CURATED = [
    # ── Ultra-small (≤2 GB RAM) ──────────────────────────────────────────────
    {
        "name":     "TinyLlama 1.1B",
        "badge":    "⚡ Best for low-end PCs",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size": "670 MB", "ram": "2 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Tiny but surprisingly capable. Runs on almost anything. Perfect starting point.",
    },
    {
        "name":     "Qwen2.5 0.5B",
        "badge":    "🐣 Pocket-sized",
        "filename": "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "size": "350 MB", "ram": "2 GB+",
        "tags": ["small", "chat", "multilingual"],
        "desc": "Alibaba's smallest model. Surprisingly articulate for its size.",
    },
    {
        "name":     "SmolLM2 1.7B",
        "badge":    "🌱 Fast & light",
        "filename": "SmolLM2-1.7B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/SmolLM2-1.7B-Instruct-GGUF/resolve/main/SmolLM2-1.7B-Instruct-Q4_K_M.gguf",
        "size": "1.0 GB", "ram": "2 GB+",
        "tags": ["small", "chat"],
        "desc": "HuggingFace's tiny instruction model. Punches above its weight.",
    },
    # ── Small (2–4 GB RAM) ───────────────────────────────────────────────────
    {
        "name":     "Phi-2 2.7B",
        "badge":    "🧠 Smart and compact",
        "filename": "phi-2.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
        "size": "1.6 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "coding", "chat"],
        "desc": "Microsoft's compact powerhouse. Excellent at reasoning, coding, and writing.",
    },
    {
        "name":     "Phi-3.5 Mini 3.8B",
        "badge":    "🔷 Microsoft latest",
        "filename": "Phi-3.5-mini-instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf",
        "size": "2.3 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "coding", "chat"],
        "desc": "Microsoft's Phi-3.5 Mini — beats models 3× its size on benchmarks.",
    },
    {
        "name":     "Phi-4 Mini 3.8B",
        "badge":    "🔷 Phi-4 series",
        "filename": "phi-4-mini-instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/phi-4-mini-instruct-GGUF/resolve/main/phi-4-mini-instruct-Q4_K_M.gguf",
        "size": "2.3 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "coding", "chat"],
        "desc": "Latest Phi-4 generation. Microsoft's best small model yet.",
    },
    {
        "name":     "Llama 3.2 3B",
        "badge":    "🦙 Latest from Meta",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size": "2.0 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Meta's latest compact model. Fast, capable, and fully open source.",
    },
    {
        "name":     "Gemma 2 2B",
        "badge":    "🔵 Google",
        "filename": "gemma-2-2b-it-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf",
        "size": "1.6 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Google's compact instruction model. Clean, fast, and capable.",
    },
    {
        "name":     "Qwen2.5 3B",
        "badge":    "🌏 Multilingual small",
        "filename": "Qwen2.5-3B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf",
        "size": "1.9 GB", "ram": "4 GB+",
        "tags": ["small", "chat", "multilingual"],
        "desc": "Qwen2.5's entry into the 3B class. Strong multilingual and coding ability.",
    },
    # ── Medium (6–12 GB RAM) ─────────────────────────────────────────────────
    {
        "name":     "Mistral 7B Instruct",
        "badge":    "⚖️ Best all-rounder",
        "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "The gold standard for local AI. Excellent at everything.",
    },
    {
        "name":     "Mistral Nemo 12B",
        "badge":    "🌊 Mistral + NVIDIA",
        "filename": "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF/resolve/main/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        "size": "7.1 GB", "ram": "12 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "Mistral and NVIDIA's collaboration. 128k context, multi-lingual, powerful.",
    },
    {
        "name":     "Dolphin Mistral 7B",
        "badge":    "🐬 Uncensored",
        "filename": "dolphin-2.2.1-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/dolphin-2.2.1-mistral-7B-GGUF/resolve/main/dolphin-2.2.1-mistral-7b.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["uncensored", "chat", "large"],
        "desc": "Mistral fine-tuned to never refuse. Loyal, direct, completely open.",
    },
    {
        "name":     "Dolphin Llama 3 8B",
        "badge":    "🐬 Uncensored + Powerful",
        "filename": "dolphin-2.9-llama3-8b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/dolphin-2.9-llama3-8b-GGUF/resolve/main/dolphin-2.9-llama3-8b-Q4_K_M.gguf",
        "size": "4.9 GB", "ram": "10 GB+",
        "tags": ["uncensored", "chat", "large"],
        "desc": "Dolphin on Llama 3. Powerful, uncensored, deeply loyal.",
    },
    {
        "name":     "Llama 3.1 8B Instruct",
        "badge":    "🦙 Most popular 8B",
        "filename": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "size": "4.9 GB", "ram": "10 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "Meta's flagship open source model. State of the art for 8B.",
    },
    {
        "name":     "Llama 3.2 11B Vision",
        "badge":    "👁️ Llama + Vision",
        "filename": "Llama-3.2-11B-Vision-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Llama-3.2-11B-Vision-Instruct-GGUF/resolve/main/Llama-3.2-11B-Vision-Instruct-Q4_K_M.gguf",
        "size": "6.8 GB", "ram": "12 GB+",
        "tags": ["vision", "large", "chat"],
        "desc": "Llama 3.2 with vision. See images, screenshots, charts, and more.",
    },
    {
        "name":     "Gemma 2 9B",
        "badge":    "🔵 Google 9B",
        "filename": "gemma-2-9b-it-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it-Q4_K_M.gguf",
        "size": "5.8 GB", "ram": "10 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "Google's mid-size Gemma 2. Outperforms many larger models.",
    },
    {
        "name":     "Qwen2.5 7B",
        "badge":    "🌏 Multilingual 7B",
        "filename": "qwen2.5-7b-instruct-q4_k_m.gguf",
        "url":      "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "size": "4.7 GB", "ram": "8 GB+",
        "tags": ["multilingual", "chat", "large"],
        "desc": "Alibaba's multilingual powerhouse. Strong at English, Chinese, and more.",
    },
    {
        "name":     "Qwen2.5 14B",
        "badge":    "🌏 Multilingual 14B",
        "filename": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Qwen2.5-14B-Instruct-GGUF/resolve/main/Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "size": "8.9 GB", "ram": "12 GB+",
        "tags": ["multilingual", "chat", "large"],
        "desc": "Qwen2.5's 14B. Excellent reasoning, math, and code in many languages.",
    },
    {
        "name":     "OpenHermes 2.5 Mistral",
        "badge":    "🧙 Smart assistant",
        "filename": "openhermes-2.5-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/resolve/main/openhermes-2.5-mistral-7b.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "Mistral fine-tuned on high quality instructions. Sharp and reliable.",
    },
    {
        "name":     "Nous Hermes 2 Mixtral",
        "badge":    "🏛️ Nous Research",
        "filename": "Nous-Hermes-2-Mistral-7B-DPO.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Nous-Hermes-2-Mistral-7B-DPO-GGUF/resolve/main/Nous-Hermes-2-Mistral-7B-DPO.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "Nous Research's DPO fine-tuned Mistral. Very coherent, long-form answers.",
    },
    {
        "name":     "Zephyr 7B Beta",
        "badge":    "💨 HuggingFace RLHF",
        "filename": "zephyr-7b-beta.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/zephyr-7B-beta-GGUF/resolve/main/zephyr-7b-beta.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "HuggingFace's RLHF model. Helpful, harmless, honest — their best 7B.",
    },
    {
        "name":     "Neural Chat 7B",
        "badge":    "🤝 Intel optimized",
        "filename": "neural-chat-7b-v3-3.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/neural-chat-7B-v3-3-GGUF/resolve/main/neural-chat-7b-v3-3.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["chat", "large"],
        "desc": "Intel's Neural Chat, optimized for conversational AI. Very natural tone.",
    },
    {
        "name":     "Yi 1.5 9B",
        "badge":    "🇨🇳 01.AI",
        "filename": "Yi-1.5-9B-Chat-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Yi-1.5-9B-Chat-GGUF/resolve/main/Yi-1.5-9B-Chat-Q4_K_M.gguf",
        "size": "5.5 GB", "ram": "10 GB+",
        "tags": ["popular", "chat", "large", "multilingual"],
        "desc": "01.AI's Yi-1.5. Exceptional reasoning and long context (32k tokens).",
    },
    {
        "name":     "Orca 2 7B",
        "badge":    "🐋 Microsoft Orca",
        "filename": "orca-2-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Orca-2-7B-GGUF/resolve/main/orca-2-7b.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["chat", "large"],
        "desc": "Microsoft Orca 2 — trained with 'reasoning' techniques from GPT-4.",
    },
    {
        "name":     "WizardLM 2 7B",
        "badge":    "🪄 Following complex instructions",
        "filename": "WizardLM-2-7B.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/WizardLM-2-7B-GGUF/resolve/main/WizardLM-2-7B-Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["chat", "large"],
        "desc": "WizardLM 2 — exceptional at following complex, multi-step instructions.",
    },
    # ── Coding specialists ───────────────────────────────────────────────────
    {
        "name":     "CodeLlama 7B",
        "badge":    "💻 Coding specialist",
        "filename": "codellama-7b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf",
        "size": "3.8 GB", "ram": "8 GB+",
        "tags": ["coding", "large"],
        "desc": "Fine-tuned specifically for code. Write, debug, and explain in any language.",
    },
    {
        "name":     "DeepSeek Coder 6.7B",
        "badge":    "💻 Best code model",
        "filename": "deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF/resolve/main/deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
        "size": "3.8 GB", "ram": "8 GB+",
        "tags": ["coding", "large"],
        "desc": "DeepSeek's dedicated coding model. Exceptional at writing and reviewing code.",
    },
    {
        "name":     "StarCoder2 7B",
        "badge":    "⭐ Code generation",
        "filename": "starcoder2-7b-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/starcoder2-7b-GGUF/resolve/main/starcoder2-7b-Q4_K_M.gguf",
        "size": "4.4 GB", "ram": "8 GB+",
        "tags": ["coding", "large"],
        "desc": "BigCode's StarCoder2. Trained on 600+ programming languages.",
    },
    {
        "name":     "DeepSeek-R1 Distill 7B",
        "badge":    "🧮 Reasoning + Code",
        "filename": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "size": "4.7 GB", "ram": "8 GB+",
        "tags": ["coding", "chat", "large"],
        "desc": "DeepSeek-R1 distilled to 7B. Thinks step-by-step. Strong at math and code.",
    },
    # ── Large (16+ GB RAM) ───────────────────────────────────────────────────
    {
        "name":     "Llama 3.3 70B (Q2)",
        "badge":    "🦙 Meta's best — Q2",
        "filename": "Llama-3.3-70B-Instruct-Q2_K.gguf",
        "url":      "https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF/resolve/main/Llama-3.3-70B-Instruct-Q2_K.gguf",
        "size": "26 GB", "ram": "32 GB+",
        "tags": ["popular", "large", "chat"],
        "desc": "Llama 3.3 70B quantized to Q2. Near GPT-4 quality. High-end machine required.",
    },
    {
        "name":     "Qwen2.5 32B",
        "badge":    "🌏 Qwen flagship",
        "filename": "Qwen2.5-32B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Qwen2.5-32B-Instruct-GGUF/resolve/main/Qwen2.5-32B-Instruct-Q4_K_M.gguf",
        "size": "20 GB", "ram": "24 GB+",
        "tags": ["multilingual", "large", "chat"],
        "desc": "Qwen2.5's 32B. Alibaba's best large model. Exceptional at reasoning.",
    },
    {
        "name":     "Mixtral 8x7B",
        "badge":    "🚀 Mixture of experts",
        "filename": "mixtral-8x7b-instruct-v0.1.Q3_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF/resolve/main/mixtral-8x7b-instruct-v0.1.Q3_K_M.gguf",
        "size": "19 GB", "ram": "24 GB+",
        "tags": ["popular", "large", "chat"],
        "desc": "Mistral's mixture-of-experts. GPT-4 level. Needs a powerful machine.",
    },
    {
        "name":     "DeepSeek-R1 14B",
        "badge":    "🧮 Chain-of-thought",
        "filename": "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
        "size": "9.0 GB", "ram": "16 GB+",
        "tags": ["coding", "chat", "large"],
        "desc": "DeepSeek's reasoning model at 14B. Shows its thinking step-by-step.",
    },
    # ── Vision ───────────────────────────────────────────────────────────────
    {
        "name":     "Llava 1.6 Mistral 7B",
        "badge":    "👁️ Can see images",
        "filename": "llava-v1.6-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/cjpais/llava-1.6-mistral-7b-gguf/resolve/main/llava-v1.6-mistral-7b.Q4_K_M.gguf",
        "size": "4.4 GB", "ram": "8 GB+",
        "tags": ["vision", "large"],
        "desc": "Multimodal — can see and describe images. Show it a photo and ask questions.",
    },
    {
        "name":     "MiniCPM-V 2.6 8B",
        "badge":    "👁️ Advanced vision",
        "filename": "MiniCPM-V-2_6-Q4_K_M.gguf",
        "url":      "https://huggingface.co/openbmb/MiniCPM-V-2_6-gguf/resolve/main/MiniCPM-V-2_6-Q4_K_M.gguf",
        "size": "5.2 GB", "ram": "10 GB+",
        "tags": ["vision", "large", "chat"],
        "desc": "MiniCPM-V 2.6 — reads text in images, understands charts, tables, and more.",
    },
]

def _ram_gb(ram_str: str) -> int:
    """Parse '8 GB+' → 8."""
    try:
        return int(ram_str.split()[0])
    except Exception:
        return 0

SMALL  = [m for m in CURATED if _ram_gb(m["ram"]) <= 4]
MEDIUM = [m for m in CURATED if 4 < _ram_gb(m["ram"]) <= 12]
LARGE  = [m for m in CURATED if _ram_gb(m["ram"]) > 12]


class ModelsPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app            = app
        self.theme          = theme
        self._ollama_models = []
        self._hf_loading    = False
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        self._rebuild()

    def _rebuild(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        # ── Header ───────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=56)
        hdr.pack(fill="x", padx=22, pady=(20, 0))
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="📦  Model Library",
            font=("Arial", 22, "bold"),
            text_color=T["text_primary"],
        ).pack(side="left", anchor="w")

        ctk.CTkLabel(
            hdr, text="Download once — runs 100% on your machine",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(side="left", padx=16, anchor="w")

        ctk.CTkButton(
            hdr, text="↻  Refresh",
            width=90, height=30,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            command=self._rebuild,
        ).pack(side="right", padx=4)

        # ── Scrollable model list ────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=12, pady=(10, 0))

        # ── Bottom search bar ────────────────────────────────
        bot = ctk.CTkFrame(self, fg_color=T["bg_topbar"], height=54)
        bot.pack(fill="x", pady=(4, 0))
        bot.pack_propagate(False)

        self._search_var = ctk.StringVar()
        self._search_entry = ctk.CTkEntry(
            bot,
            textvariable=self._search_var,
            placeholder_text="Find more models…",
            font=("Arial", 12), height=36,
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_color=T["border"],
            placeholder_text_color=T["text_secondary"],
        )
        self._search_entry.pack(
            side="left", fill="both", expand=True, padx=(16, 6), pady=9)
        self._search_entry.bind("<Return>", lambda _: self._do_search())

        ctk.CTkButton(
            bot, text="Search",
            width=90, height=36, corner_radius=8,
            fg_color=T["accent"], hover_color=T["accent_hover"],
            command=self._do_search,
        ).pack(side="left", padx=(0, 6), pady=9)

        ctk.CTkButton(
            bot, text="📁 Local File",
            width=114, height=36, corner_radius=8,
            fg_color=T["bg_card"], hover_color=T["bg_hover"],
            text_color=T["text_secondary"],
            command=self._add_local,
        ).pack(side="left", padx=(0, 16), pady=9)

        # Populate and auto-detect Ollama
        self._populate_list()
        threading.Thread(target=self._ollama_probe, daemon=True).start()

    # ── Populate list ────────────────────────────────────────

    def _populate_list(self, ollama_models=None):
        """Fill scroll with models grouped by size; optionally prepend Ollama models."""
        T = self.theme
        for w in self._scroll.winfo_children():
            w.destroy()

        # Installed models (Ollama) — no backend branding shown to user
        if ollama_models:
            self._section_header("✅  Available Now")
            for m in ollama_models:
                self._ollama_row(m)
            ctk.CTkFrame(
                self._scroll, height=2, fg_color=T["border"]
            ).pack(fill="x", pady=8, padx=4)

        # ── Small ──
        self._section_header("⚡  Small — Runs on anything  (2–4 GB RAM)")
        for m in SMALL:
            self._model_row(m)

        # ── Medium ──
        ctk.CTkFrame(
            self._scroll, height=2, fg_color=T["border"]
        ).pack(fill="x", pady=(10, 4), padx=4)
        self._section_header("⚖️  Medium — 8 GB RAM recommended")
        for m in MEDIUM:
            self._model_row(m)

        # ── Large ──
        ctk.CTkFrame(
            self._scroll, height=2, fg_color=T["border"]
        ).pack(fill="x", pady=(10, 4), padx=4)
        self._section_header("🚀  Large — 16 GB+ recommended")
        for m in LARGE:
            self._model_row(m)

    def _section_header(self, text: str):
        T = self.theme
        ctk.CTkLabel(
            self._scroll, text=text,
            font=("Arial", 13, "bold"),
            text_color=T["text_secondary"],
            anchor="w",
        ).pack(anchor="w", padx=10, pady=(10, 4))

    # ── Ollama auto-detection ────────────────────────────────

    def _ollama_probe(self):
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            r.raise_for_status()
            models = r.json().get("models", [])
            if models:
                self._ollama_models = models
                self.after(0, lambda: self._populate_list(models))
        except Exception:
            pass  # Ollama not running — that's fine

    def _ollama_row(self, m: dict):
        T      = self.theme
        name   = m.get("name", "unknown")
        size_b = m.get("size", 0)
        size_s = f"{size_b / (1024**3):.1f} GB" if size_b else ""
        family = m.get("details", {}).get("family", "")
        params = m.get("details", {}).get("parameter_size", "")
        loaded = (model_manager.get_current_model() == name)

        row = ctk.CTkFrame(self._scroll, corner_radius=10, fg_color=T["bg_card"])
        row.pack(fill="x", pady=3, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        ctk.CTkLabel(
            info, text=name,
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"], anchor="w",
        ).pack(anchor="w")

        detail = "  •  ".join(x for x in [family, params, size_s] if x) or "Installed"
        ctk.CTkLabel(
            info, text=detail,
            font=("Arial", 11),
            text_color=T["text_secondary"], anchor="w",
        ).pack(anchor="w")

        if loaded:
            ctk.CTkLabel(
                row, text="▶ Running",
                font=("Arial", 12, "bold"),
                text_color=T["gold"],
            ).pack(side="right", padx=12, pady=10)
        else:
            ctk.CTkButton(
                row, text="▶ Load",
                width=90, height=34, corner_radius=8,
                fg_color=T["accent"], hover_color=T["accent_hover"],
                text_color="#ffffff",
                command=lambda n=name: self._load_ollama(n),
            ).pack(side="right", padx=12, pady=10)

    def _load_ollama(self, name: str):
        try:
            self.app.chat_panel.sys_message(f"▶  Loading {name}…")
        except Exception:
            pass
        self.app.load_model(name)
        self.app.switch_panel("Chat")

    # ── Curated model row ────────────────────────────────────

    def _model_row(self, m: dict):
        T      = self.theme
        have   = os.path.exists(os.path.join(MODELS_DIR, m["filename"]))
        loaded = (model_manager.get_current_model() == m["filename"])

        row = ctk.CTkFrame(self._scroll, corner_radius=12, fg_color=T["bg_card"])
        row.pack(fill="x", pady=4, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        # Title row
        tr = ctk.CTkFrame(info, fg_color="transparent")
        tr.pack(anchor="w", fill="x")

        ctk.CTkLabel(
            tr, text=m["name"],
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"], anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            tr, text=f"  {m['badge']}",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(side="left")

        if loaded:
            ctk.CTkLabel(tr, text="  ▶ Active",
                         font=("Arial", 11, "bold"),
                         text_color=T["gold"]).pack(side="left")
        elif have:
            ctk.CTkLabel(tr, text="  ✅ Downloaded",
                         font=("Arial", 11),
                         text_color=T["green"]).pack(side="left")

        ctk.CTkLabel(
            info, text=m["desc"],
            font=("Arial", 11),
            text_color=T["text_secondary"],
            anchor="w", wraplength=560, justify="left",
        ).pack(anchor="w", pady=(2, 0))

        meta = ctk.CTkFrame(info, fg_color="transparent")
        meta.pack(anchor="w", pady=(5, 0))

        for label, val in [("Size", m["size"]), ("RAM", m["ram"])]:
            ctk.CTkLabel(
                meta, text=f"{label}: {val}",
                font=("Arial", 10),
                text_color=T["text_dim"],
                fg_color=T["bg_hover"],
                corner_radius=4, width=110,
            ).pack(side="left", padx=(0, 6))

        # Action button
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=124)
        btn_frame.pack(side="right", padx=12, pady=12)
        btn_frame.pack_propagate(False)

        if loaded:
            ctk.CTkLabel(
                btn_frame, text="▶ Running",
                font=("Arial", 12, "bold"),
                text_color=T["gold"],
            ).pack(expand=True)
        elif have:
            ctk.CTkButton(
                btn_frame, text="▶ Load",
                height=36, corner_radius=8,
                fg_color="#1a4a1a", hover_color="#0d2e0d",
                text_color="#ffffff",
                command=lambda fn=m["filename"]: self._load(fn),
            ).pack(fill="x", pady=(0, 4))
            ctk.CTkButton(
                btn_frame, text="🗑 Delete",
                height=22, corner_radius=6,
                fg_color="#2a1212", hover_color="#3a1a1a",
                text_color=T["text_secondary"],
                font=("Arial", 10),
                command=lambda fn=m["filename"]: self._delete(fn),
            ).pack(fill="x")
        else:
            ctk.CTkButton(
                btn_frame, text="⬇ Download",
                height=36, corner_radius=8,
                fg_color=T["accent"], hover_color=T["accent_hover"],
                text_color="#ffffff",
                command=lambda mo=m: self._download(mo),
            ).pack(fill="x")

    # ── Search (HuggingFace + GitHub) ────────────────────────

    def _do_search(self):
        query = self._search_var.get().strip()
        if not query or self._hf_loading:
            return
        self._hf_loading = True
        T = self.theme

        for w in self._scroll.winfo_children():
            w.destroy()

        ctk.CTkButton(
            self._scroll, text="← Back to catalog",
            width=140, height=28,
            fg_color=T["bg_hover"], hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            font=("Arial", 11), anchor="w",
            command=self._back_to_catalog,
        ).pack(anchor="w", pady=(4, 8))

        status = ctk.CTkLabel(
            self._scroll,
            text=f"🔍  Searching for \"{query}\"…",
            font=("Arial", 13),
            text_color=T["text_secondary"],
        )
        status.pack(pady=40)

        def _search():
            try:
                url = (
                    f"https://huggingface.co/api/models"
                    f"?search={query}&filter=gguf"
                    f"&sort=downloads&limit=20&full=false"
                )
                r = requests.get(url, timeout=12)
                r.raise_for_status()
                results = r.json()
                self.after(0, lambda: self._render_search(results, query, status))
            except Exception as e:
                self.after(0, lambda: status.configure(
                    text=f"❌  Search failed: {e}\nCheck your connection.",
                    text_color=T.get("text_error", "#ff4444")))
            finally:
                self._hf_loading = False

        threading.Thread(target=_search, daemon=True).start()
        threading.Thread(
            target=self._github_search, args=(query,), daemon=True).start()

    def _github_search(self, query: str):
        T = self.theme
        try:
            url = (
                f"https://api.github.com/search/repositories"
                f"?q={query}+gguf&sort=stars&per_page=20"
            )
            r = requests.get(
                url,
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=12,
            )
            if r.status_code in (403, 429):
                self.after(0, lambda: self._render_github_results(
                    None, query, rate_limited=True))
                return
            r.raise_for_status()
            items = r.json().get("items", [])
            self.after(0, lambda: self._render_github_results(items, query))
        except Exception:
            pass  # silently skip GitHub results if unavailable

    def _render_github_results(self, items, query: str, rate_limited: bool = False):
        T = self.theme
        if rate_limited:
            ctk.CTkLabel(
                self._scroll,
                text="⚠️  GitHub search limit reached — try again in 60 seconds",
                font=("Arial", 12),
                text_color=T.get("text_error", "#ff9944"),
            ).pack(anchor="w", padx=10, pady=(8, 4))
            return

        if not items:
            return

        ctk.CTkLabel(
            self._scroll,
            text=f"[GitHub]  {len(items)} repositories found",
            font=("Arial", 12, "bold"),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=10, pady=(12, 4))

        for item in items:
            self._github_result_row(item)

    def _github_result_row(self, item: dict):
        T    = self.theme
        name = item.get("full_name", item.get("name", "Unknown"))
        desc = item.get("description") or ""
        stars = item.get("stargazers_count", 0)
        html_url  = item.get("html_url", "")
        clone_url = item.get("clone_url", "")

        row = ctk.CTkFrame(self._scroll, corner_radius=10, fg_color=T["bg_card"])
        row.pack(fill="x", pady=4, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        name_row = ctk.CTkFrame(info, fg_color="transparent")
        name_row.pack(anchor="w", fill="x")

        ctk.CTkLabel(
            name_row, text=name,
            font=("Arial", 13, "bold"),
            text_color=T["text_primary"], anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            name_row, text="  [GitHub]",
            font=("Arial", 11),
            text_color=T.get("accent", "#4a9eff"), anchor="w",
        ).pack(side="left")

        if desc:
            ctk.CTkLabel(
                info, text=desc,
                font=("Arial", 10),
                text_color=T["text_secondary"], anchor="w",
                wraplength=420,
            ).pack(anchor="w")

        meta_parts = [f"⭐ {stars:,}"]
        if clone_url:
            meta_parts.append(clone_url)
        ctk.CTkLabel(
            info, text="  ".join(meta_parts),
            font=("Arial", 10),
            text_color=T["text_secondary"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkButton(
            row, text="View Repo",
            width=100, height=32, corner_radius=8,
            fg_color=T["bg_hover"], hover_color=T["bg_card"],
            text_color=T["text_primary"],
            command=lambda url=html_url: webbrowser.open(url),
        ).pack(side="right", padx=12, pady=10)

    def _render_search(self, results: list, query: str, status):
        T = self.theme
        try:
            status.destroy()
        except Exception:
            pass

        if not results:
            ctk.CTkLabel(
                self._scroll,
                text=f"No GGUF models found for \"{query}\".",
                font=("Arial", 13),
                text_color=T["text_secondary"],
            ).pack(pady=20)
            return

        ctk.CTkLabel(
            self._scroll,
            text=f"{len(results)} models found — click View Files to download",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))

        for model in results:
            self._search_result_row(model)

    def _search_result_row(self, model: dict):
        T         = self.theme
        model_id  = model.get("modelId", model.get("id", "Unknown"))
        downloads = model.get("downloads", 0)

        row = ctk.CTkFrame(self._scroll, corner_radius=10, fg_color=T["bg_card"])
        row.pack(fill="x", pady=4, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        ctk.CTkLabel(
            info, text=model_id,
            font=("Arial", 13, "bold"),
            text_color=T["text_primary"], anchor="w",
        ).pack(anchor="w")

        if downloads:
            ctk.CTkLabel(
                info, text=f"⬇ {downloads:,} downloads",
                font=("Arial", 10),
                text_color=T["text_secondary"],
            ).pack(anchor="w")

        ctk.CTkButton(
            row, text="View Files",
            width=100, height=32, corner_radius=8,
            fg_color=T["accent"], hover_color=T["accent_hover"],
            text_color="#ffffff",
            command=lambda mid=model_id: self._show_files(mid),
        ).pack(side="right", padx=12, pady=10)

    def _back_to_catalog(self):
        self._populate_list(self._ollama_models or None)

    # ── HuggingFace file browser ─────────────────────────────

    def _show_files(self, model_id: str):
        T   = self.theme
        win = ctk.CTkToplevel(self)
        win.title(model_id)
        win.geometry("720x520")
        win.configure(fg_color=T["bg_panel"])
        # No grab_set — preserves main window WM decorations on Linux

        def _on_close():
            win.destroy()
            try:
                self.winfo_toplevel().focus_force()
            except Exception:
                pass

        win.protocol("WM_DELETE_WINDOW", _on_close)

        ctk.CTkLabel(
            win, text=model_id,
            font=("Arial", 15, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(18, 2), padx=22, anchor="w")

        ctk.CTkLabel(
            win, text=t("models_select_dl"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(padx=22, anchor="w")

        status = ctk.CTkLabel(
            win, text=t("models_loading_files"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        )
        status.pack(pady=20)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        def _fetch():
            try:
                r    = requests.get(
                    f"https://huggingface.co/api/models/{model_id}",
                    timeout=12)
                r.raise_for_status()
                data  = r.json()
                files = [
                    s for s in data.get("siblings", [])
                    if s.get("rfilename", "").endswith(".gguf")
                ]
                win.after(0, lambda: _show(files))
            except Exception as e:
                win.after(0, lambda: status.configure(
                    text=f"❌  {e}",
                    text_color=T.get("text_error", "#ff4444")))

        def _show(files: list):
            try:
                status.destroy()
            except Exception:
                pass

            if not files:
                ctk.CTkLabel(
                    scroll, text=t("models_no_files"),
                    text_color=T["text_secondary"],
                ).pack(pady=20)
                return

            for f in files:
                fname    = f.get("rfilename", "")
                size_b   = f.get("size", 0)
                size_str = (
                    f"{size_b/(1024**3):.1f} GB"
                    if size_b > 1024**3
                    else f"{size_b/(1024**2):.0f} MB"
                    if size_b else "?"
                )
                frow = ctk.CTkFrame(scroll, corner_radius=8, fg_color=T["bg_card"])
                frow.pack(fill="x", pady=4, padx=2)

                fi = ctk.CTkFrame(frow, fg_color="transparent")
                fi.pack(side="left", fill="both", expand=True, padx=12, pady=8)

                ctk.CTkLabel(
                    fi, text=fname,
                    font=("Arial", 12, "bold"),
                    text_color=T["text_primary"], anchor="w",
                ).pack(anchor="w")
                ctk.CTkLabel(
                    fi, text=size_str,
                    font=("Arial", 10),
                    text_color=T["text_secondary"], anchor="w",
                ).pack(anchor="w")

                dl_url = (
                    f"https://huggingface.co/{model_id}"
                    f"/resolve/main/{fname}"
                )
                have = os.path.exists(os.path.join(MODELS_DIR, fname))

                if have:
                    ctk.CTkLabel(
                        frow, text=t("models_downloaded"),
                        font=("Arial", 11),
                        text_color=T["green"],
                    ).pack(side="right", padx=12, pady=10)
                else:
                    ctk.CTkButton(
                        frow, text=t("models_download"),
                        width=116, height=32, corner_radius=8,
                        fg_color=T["accent"], hover_color=T["accent_hover"],
                        text_color="#ffffff",
                        command=lambda u=dl_url, fn=fname: (
                            _on_close(),
                            self._download({
                                "name":     fn,
                                "filename": fn,
                                "url":      u,
                                "size":     size_str,
                                "ram":      "?",
                                "desc":     f"From {model_id}",
                            })
                        ),
                    ).pack(side="right", padx=12, pady=8)

        threading.Thread(target=_fetch, daemon=True).start()

    # ── Actions ──────────────────────────────────────────────

    def _load(self, filename: str):
        self.app.load_model(filename)
        self.app.switch_panel("Chat")

    def _delete(self, filename: str):
        path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(path):
            os.remove(path)
        self.refresh()

    def _download(self, model: dict):
        DownloadWindow(self, model, self.theme, self.refresh)

    def _add_local(self):
        path = filedialog.askopenfilename(
            title=t("models_select_file"),
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")])
        if path:
            os.makedirs(MODELS_DIR, exist_ok=True)
            dest = os.path.join(MODELS_DIR, os.path.basename(path))
            shutil.copy2(path, dest)
            self.refresh()
            try:
                self.app.chat_panel.sys_message(
                    f"✅  {t('models_added')} {os.path.basename(path)}")
            except Exception:
                pass

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()


# ── Download window ──────────────────────────────────────────

class DownloadWindow(ctk.CTkToplevel):

    def __init__(self, parent, model: dict,
                 theme: dict, on_done=None):
        super().__init__(parent)
        self.on_done = on_done
        self._q      = queue.Queue()
        T            = theme

        self.title("Downloading")
        self.geometry("540x210")
        self.resizable(False, False)
        self.configure(fg_color=T["bg_panel"])
        # No grab_set — download window is non-modal; parent keeps WM decorations

        ctk.CTkLabel(
            self,
            text=f"⬇  {model.get('name', model['filename'])}",
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(22, 4))

        self.bar = ctk.CTkProgressBar(
            self, width=480,
            progress_color=T["accent"],
            fg_color=T["bg_card"],
        )
        self.bar.set(0)
        self.bar.pack(pady=8)

        self.lbl = ctk.CTkLabel(
            self,
            text=t("models_connecting"),
            font=("Arial", 11),
            text_color=T["text_secondary"],
        )
        self.lbl.pack()

        ctk.CTkLabel(
            self,
            text=t("models_minimize"),
            font=("Arial", 10),
            text_color=T["text_dim"],
        ).pack(pady=4)

        threading.Thread(
            target=self._dl, args=(model,), daemon=True).start()
        self._poll()

    def _dl(self, model: dict):
        try:
            os.makedirs(MODELS_DIR, exist_ok=True)
            r     = requests.get(
                model["url"], stream=True, timeout=60)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done  = 0
            dest  = os.path.join(MODELS_DIR, model["filename"])
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        self._q.put(("p", done / total, done, total))
            self._q.put(("done", None))
        except Exception as e:
            self._q.put(("error", str(e)))

    def _poll(self):
        try:
            while True:
                msg = self._q.get_nowait()
                if msg[0] == "p":
                    _, pct, done, total = msg
                    self.bar.set(pct)
                    self.lbl.configure(
                        text=f"{done/(1024**2):.1f} MB / "
                             f"{total/(1024**2):.1f} MB  "
                             f"({pct*100:.1f}%)"
                    )
                elif msg[0] == "done":
                    self.bar.set(1.0)
                    self.lbl.configure(text=t("models_complete"))
                    self.after(1400, self._finish)
                    return
                elif msg[0] == "error":
                    self.lbl.configure(text=f"❌  {msg[1]}")
                    return
        except queue.Empty:
            pass
        self.after(110, self._poll)

    def _finish(self):
        if self.on_done:
            self.on_done()
        try:
            self.destroy()
        except Exception:
            pass
