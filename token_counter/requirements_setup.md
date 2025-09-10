# Universal LLM Token Counter Setup

## Installation

```bash
# Install required packages
pip install tiktoken transformers torch huggingface-hub

# For optional dependencies (if you plan to use specific models)
pip install sentencepiece  # For some models like T5, LLaMA
pip install accelerate      # For large models
pip install bitsandbytes   # For quantized models
```

## Requirements.txt
```
tiktoken>=0.5.0
transformers>=4.30.0
torch>=2.0.0
huggingface-hub>=0.16.0
sentencepiece>=0.1.99
numpy>=1.21.0
```

## Authentication Setup

For some models, you'll need to authenticate:

```bash
# Login to Hugging Face (for gated models like LLaMA)
huggingface-cli login

# For OpenAI models (if using their API)
export OPENAI_API_KEY="your-api-key"
```

## Quick Start Examples

### Basic Usage
```python
from universal_token_counter import UniversalTokenCounter

counter = UniversalTokenCounter()

# Count tokens for any model
result = counter.count_tokens("Hello world!", "gpt-4")
print(f"Tokens: {result['token_count']}")

# Compare across models
comparison = counter.compare_models(
    "Your text here",
    ["gpt-4", "gpt-3.5-turbo", "llama-2", "mistral"]
)
```

### Supported Model Categories

| Category | Models | Tokenizer |
|----------|--------|-----------|
| **OpenAI** | GPT-4, GPT-3.5-turbo, etc. | tiktoken |
| **Anthropic** | Claude-3, Claude-2 | tiktoken (approximate) |
| **Meta** | LLaMA, LLaMA-2, LLaMA-3 | HuggingFace |
| **Mistral** | Mistral-7B, Mixtral-8x7B | HuggingFace |
| **Google** | T5, PaLM (via HF) | HuggingFace |
| **Open Source** | Falcon, MPT, BLOOM, etc. | HuggingFace |
| **Custom** | Any HuggingFace model | HuggingFace |

### CLI Usage

```bash
# Basic counting
python universal_token_counter.py --text "Hello world" --model gpt-4

# Compare models
python universal_token_counter.py --text "Hello world" --compare gpt-4 gpt-3.5-turbo llama-2

# From file
python universal_token_counter.py --file document.txt --model claude-3-sonnet

# List all supported models
python universal_token_counter.py --list-models
```

## Advanced Features

### Cost Estimation
```python
# Define costs per 1K tokens
costs = {
    "gpt-4": 0.03,
    "gpt-3.5-turbo": 0.002,
    "claude-3-sonnet": 0.003
}

cost_analysis = counter.estimate_costs("Your text", costs)
```

### Batch Processing
```python
texts = ["Text 1", "Text 2", "Text 3"]
results = counter.batch_count_tokens(texts, "gpt-4")
```

## Troubleshooting

### Common Issues

1. **"Model not found"**: Make sure you're using the correct model name
2. **"Authentication required"**: Some models need HuggingFace login
3. **"Out of memory"**: Large models may need GPU or quantization
4. **"Encoding not found"**: Install the latest tiktoken version

### Model Access Requirements

- **LLaMA models**: Need approval from Meta + HuggingFace login
- **Gated models**: Request access on HuggingFace model page
- **Commercial models**: Some require specific licenses

## Performance Tips

1. **Cache tokenizers**: The class automatically caches loaded tokenizers
2. **Use appropriate models**: Smaller models for development, larger for production
3. **Batch processing**: More efficient for multiple texts
4. **Memory management**: Unload unused tokenizers if memory is limited

## Accuracy Notes

- **OpenAI models**: Uses official tiktoken (100% accurate)
- **Claude models**: Uses tiktoken as approximation (~95% accurate)
- **HuggingFace models**: Uses official tokenizers (100% accurate)
- **Custom models**: Accuracy depends on tokenizer implementation