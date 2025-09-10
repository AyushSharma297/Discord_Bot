import tiktoken
from transformers import AutoTokenizer
import json
import os
from typing import Dict, List, Union, Optional
import warnings

class UniversalTokenCounter:
    """
    Universal token counter supporting multiple LLM families:
    - OpenAI models (GPT-3.5, GPT-4, etc.)
    - Anthropic Claude models
    - Meta Llama models
    - Google PaLM/Gemini models
    - Mistral models
    - And many others via Hugging Face
    """
    
    def __init__(self):
        self.tokenizers = {}
        self.model_mappings = {
            # OpenAI models
            "gpt-4": "cl100k_base",
            "gpt-4-32k": "cl100k_base",
            "gpt-4-turbo": "cl100k_base",
            "gpt-4-turbo-preview": "cl100k_base",
            "gpt-4o": "o200k_base",
            "gpt-4o-mini": "o200k_base",
            "gpt-3.5-turbo": "cl100k_base",
            "gpt-3.5-turbo-16k": "cl100k_base",
            "text-davinci-003": "p50k_base",
            "text-davinci-002": "p50k_base",
            "code-davinci-002": "p50k_base",
            
            # Claude models (approximate - uses cl100k_base as estimation)
            "claude-3-opus": "cl100k_base",
            "claude-3-sonnet": "cl100k_base",
            "claude-3-haiku": "cl100k_base",
            "claude-2": "cl100k_base",
            "claude-2.1": "cl100k_base",
            "claude-instant": "cl100k_base",
            
            # Hugging Face model patterns
            "llama": "meta-llama/Llama-2-7b-hf",
            "llama-2": "meta-llama/Llama-2-7b-hf",
            "llama-3": "meta-llama/Meta-Llama-3-8B",
            "mistral": "mistralai/Mistral-7B-v0.1",
            "mixtral": "mistralai/Mixtral-8x7B-v0.1",
            "falcon": "tiiuae/falcon-7b",
            "mpt": "mosaicml/mpt-7b",
            "bloom": "bigscience/bloom-560m",
            "t5": "t5-base",
            "bart": "facebook/bart-base",
            "roberta": "roberta-base",
            "bert": "bert-base-uncased",
            "distilbert": "distilbert-base-uncased",
            "gpt2": "gpt2",
            "gpt-neo": "EleutherAI/gpt-neo-125M",
            "gpt-j": "EleutherAI/gpt-j-6B",
        }
    
    def _get_tiktoken_tokenizer(self, encoding_name: str):
        """Get tiktoken tokenizer for OpenAI models"""
        if encoding_name not in self.tokenizers:
            try:
                self.tokenizers[encoding_name] = tiktoken.get_encoding(encoding_name)
            except Exception as e:
                print(f"Warning: Could not load tiktoken encoding {encoding_name}: {e}")
                return None
        return self.tokenizers.get(encoding_name)
    
    def _get_hf_tokenizer(self, model_name: str):
        """Get Hugging Face tokenizer"""
        if model_name not in self.tokenizers:
            try:
                self.tokenizers[model_name] = AutoTokenizer.from_pretrained(model_name)
                print(f"Loaded tokenizer for {model_name}")
            except Exception as e:
                print(f"Warning: Could not load HF tokenizer for {model_name}: {e}")
                return None
        return self.tokenizers.get(model_name)
    
    def _detect_model_type(self, model_name: str) -> tuple:
        """Detect model type and return (type, tokenizer_key)"""
        model_lower = model_name.lower()
        
        # Check exact matches first
        if model_name in self.model_mappings:
            mapping = self.model_mappings[model_name]
            if mapping.startswith(("cl100k_base", "p50k_base", "r50k_base", "o200k_base")):
                return ("tiktoken", mapping)
            else:
                return ("huggingface", mapping)
        
        # Check partial matches
        for pattern, mapping in self.model_mappings.items():
            if pattern in model_lower:
                if mapping.startswith(("cl100k_base", "p50k_base", "r50k_base", "o200k_base")):
                    return ("tiktoken", mapping)
                else:
                    return ("huggingface", mapping)
        
        # If no match, assume it's a Hugging Face model name
        return ("huggingface", model_name)
    
    def count_tokens(self, text: str, model: str = "gpt-4") -> Dict:
        """
        Count tokens for any supported model
        
        Args:
            text (str): Input text
            model (str): Model name or identifier
            
        Returns:
            dict: Token count information
        """
        model_type, tokenizer_key = self._detect_model_type(model)
        
        if model_type == "tiktoken":
            return self._count_tiktoken(text, tokenizer_key, model)
        elif model_type == "huggingface":
            return self._count_huggingface(text, tokenizer_key, model)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def _count_tiktoken(self, text: str, encoding_name: str, model: str) -> Dict:
        """Count tokens using tiktoken"""
        tokenizer = self._get_tiktoken_tokenizer(encoding_name)
        if not tokenizer:
            raise RuntimeError(f"Could not load tiktoken encoding: {encoding_name}")
        
        tokens = tokenizer.encode(text)
        
        return {
            'model': model,
            'tokenizer_type': 'tiktoken',
            'encoding': encoding_name,
            'text': text,
            'token_count': len(tokens),
            'tokens': [tokenizer.decode([token]) for token in tokens[:20]],  # First 20 tokens
            'token_ids': tokens[:20] if len(tokens) <= 20 else tokens[:20],
            'truncated': len(tokens) > 20
        }
    
    def _count_huggingface(self, text: str, model_name: str, original_model: str) -> Dict:
        """Count tokens using Hugging Face tokenizer"""
        tokenizer = self._get_hf_tokenizer(model_name)
        if not tokenizer:
            raise RuntimeError(f"Could not load HuggingFace tokenizer: {model_name}")
        
        # Tokenize
        tokens = tokenizer.tokenize(text)
        token_ids = tokenizer.encode(text, add_special_tokens=True)
        
        return {
            'model': original_model,
            'tokenizer_type': 'huggingface',
            'hf_model': model_name,
            'text': text,
            'token_count': len(token_ids),
            'tokens': tokens[:20] if len(tokens) > 20 else tokens,
            'token_ids': token_ids[:20] if len(token_ids) > 20 else token_ids,
            'special_tokens_count': len(token_ids) - len(tokens),
            'truncated': len(tokens) > 20,
            'vocab_size': getattr(tokenizer, 'vocab_size', None)
        }
    
    def batch_count_tokens(self, texts: List[str], model: str = "gpt-4") -> List[Dict]:
        """Count tokens for multiple texts"""
        return [self.count_tokens(text, model) for text in texts]
    
    def compare_models(self, text: str, models: List[str]) -> Dict:
        """Compare token counts across different models"""
        results = {}
        for model in models:
            try:
                results[model] = self.count_tokens(text, model)
            except Exception as e:
                results[model] = {'error': str(e)}
        
        # Calculate statistics
        valid_counts = [r['token_count'] for r in results.values() if 'token_count' in r]
        
        stats = {}
        if valid_counts:
            stats = {
                'min_tokens': min(valid_counts),
                'max_tokens': max(valid_counts),
                'avg_tokens': sum(valid_counts) / len(valid_counts),
                'token_variance': max(valid_counts) - min(valid_counts)
            }
        
        return {
            'text': text,
            'results': results,
            'stats': stats
        }
    
    def estimate_costs(self, text: str, model_costs: Dict[str, float]) -> Dict:
        """
        Estimate costs for different models
        
        Args:
            text (str): Input text
            model_costs (dict): Dict of {model_name: cost_per_1k_tokens}
            
        Returns:
            dict: Cost estimates per model
        """
        results = {}
        for model, cost_per_1k in model_costs.items():
            try:
                token_info = self.count_tokens(text, model)
                cost = (token_info['token_count'] / 1000) * cost_per_1k
                results[model] = {
                    **token_info,
                    'cost_per_1k_tokens': cost_per_1k,
                    'estimated_cost': cost
                }
            except Exception as e:
                results[model] = {'error': str(e)}
        
        return results
    
    def supported_models(self) -> Dict[str, List[str]]:
        """List all supported models by category"""
        return {
            'OpenAI (tiktoken)': [
                'gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini',
                'gpt-3.5-turbo', 'text-davinci-003'
            ],
            'Anthropic Claude (approximate)': [
                'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku',
                'claude-2', 'claude-2.1'
            ],
            'Meta Llama': ['llama', 'llama-2', 'llama-3'],
            'Mistral': ['mistral', 'mixtral'],
            'Other Open Source': [
                'falcon', 'mpt', 'bloom', 't5', 'bart',
                'gpt2', 'gpt-neo', 'gpt-j', 'bert', 'roberta'
            ],
            'Custom': ['Any Hugging Face model name']
        }

def main():
    """Example usage and CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal LLM Token Counter')
    parser.add_argument('--text', type=str, help='Text to tokenize')
    parser.add_argument('--file', type=str, help='File containing text')
    parser.add_argument('--model', type=str, default='gpt-4', help='Model name')
    parser.add_argument('--compare', nargs='+', help='Compare across multiple models')
    parser.add_argument('--list-models', action='store_true', help='List supported models')
    
    args = parser.parse_args()
    
    counter = UniversalTokenCounter()
    
    if args.list_models:
        models = counter.supported_models()
        print("Supported Models:")
        for category, model_list in models.items():
            print(f"\n{category}:")
            for model in model_list:
                print(f"  - {model}")
        return
    
    # Get text
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        text = input("Enter text to tokenize: ")
    
    # Compare models if specified
    if args.compare:
        results = counter.compare_models(text, args.compare)
        print(f"\nComparison Results for {len(args.compare)} models:")
        print(f"Text: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        for model, result in results['results'].items():
            if 'error' in result:
                print(f"{model}: ERROR - {result['error']}")
            else:
                print(f"{model}: {result['token_count']} tokens ({result['tokenizer_type']})")
        
        if results['stats']:
            stats = results['stats']
            print(f"\nStatistics:")
            print(f"  Range: {stats['min_tokens']} - {stats['max_tokens']} tokens")
            print(f"  Average: {stats['avg_tokens']:.1f} tokens")
            print(f"  Variance: {stats['token_variance']} tokens")
    
    else:
        # Single model
        result = counter.count_tokens(text, args.model)
        print(f"\nModel: {result['model']}")
        print(f"Tokenizer: {result['tokenizer_type']}")
        print(f"Token Count: {result['token_count']}")
        if result.get('special_tokens_count'):
            print(f"Special Tokens: {result['special_tokens_count']}")
        print(f"Sample Tokens: {result['tokens']}")

if __name__ == "__main__":
    # Example usage
    counter = UniversalTokenCounter()
    
    text = "Hello! This is a test message for token counting across different LLMs."
    
    print("=== Universal Token Counter Demo ===")
    
    # Single model example
    result = counter.count_tokens(text, "gpt-4")
    print(f"\nGPT-4 Token Count: {result['token_count']}")
    
    # Compare multiple models
    models_to_compare = ["gpt-4", "gpt-3.5-turbo", "llama-2", "claude-3-sonnet"]
    comparison = counter.compare_models(text, models_to_compare)
    
    print(f"\n=== Model Comparison ===")
    for model, result in comparison['results'].items():
        if 'error' not in result:
            print(f"{model}: {result['token_count']} tokens")
        else:
            print(f"{model}: {result['error']}")
    
    # Cost estimation example
    costs = {
        "gpt-4": 0.03,      # $30 per 1M tokens
        "gpt-3.5-turbo": 0.002,  # $2 per 1M tokens
        "claude-3-sonnet": 0.003  # $3 per 1M tokens
    }
    
    cost_analysis = counter.estimate_costs(text, costs)
    print(f"\n=== Cost Analysis ===")
    for model, result in cost_analysis.items():
        if 'error' not in result:
            print(f"{model}: ${result['estimated_cost']:.6f} ({result['token_count']} tokens)")