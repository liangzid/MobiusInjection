#!/bin/bash
export OLLAMA_HOST=127.0.0.1:11435
export CUDA_VISIBLE_DEVICES=1
exec ollama serve
