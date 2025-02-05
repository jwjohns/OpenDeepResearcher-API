# OpenDeepResearcher-API

A REST API service for conducting deep research on any topic using AI. This project is an adaptation of Justin Pinkney's research notebook into a modular API service.

## Overview

OpenDeepResearcher-API is a research assistant that:
- Generates intelligent search queries
- Performs parallel web searches
- Evaluates content relevance
- Extracts key information
- Synthesizes findings into comprehensive reports
- Provides real-time status updates during research

## Features

- **Multiple LLM Provider Support**:
  - OpenRouter (default)
  - OpenAI
  - Anthropic
  - Ollama (local)
- **Intelligent Query Generation**: Creates targeted search queries to explore different aspects of your topic
- **Parallel Web Search**: Uses SERPAPI for efficient web searching
- **Content Processing**: Uses Jina AI for webpage content extraction
- **Automated Research Process**: Iteratively explores topics until sufficient information is gathered
- **Real-time Status Updates**: Streams research progress using Server-Sent Events (SSE)
- **Markdown Report Generation**: Saves research findings with full process logs

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/OpenDeepResearcher-API.git
cd OpenDeepResearcher-API
```

2. Create a Python virtual environment:
```bash
python -m venv venv-odr-310
source venv-odr-310/bin/activate  # On Unix/macOS
# or
.\venv-odr-310\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Configure your environment variables in `.env`:

```env
# Required API Keys
SERPAPI_API_KEY=your_serpapi_key
JINA_API_KEY=your_jina_key

# LLM Provider (choose one)
LLM_PROVIDER=openrouter  # Options: openrouter, openai, anthropic, ollama

# Provider-specific API Keys (only needed for chosen provider)
OPENROUTER_API_KEY=your_openrouter_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Ollama Settings (only needed if using ollama)
OLLAMA_HOST=http://localhost:11434  # Default Ollama host
OLLAMA_MODEL=llama2  # Default model
```

## Usage

1. Start the API server:
```bash
uvicorn app.main:app --reload
```

2. The API will be available at `http://localhost:8000`

3. API Endpoints:
   - POST `/api/research`: Traditional synchronous research endpoint
   - POST `/api/research/stream`: Stream research progress in real-time using SSE
   - GET `/api/health`: Check API health

Example research request (traditional):
```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Impact of quantum computing on cryptography", "max_iterations": 5}'
```

Example streaming request (real-time updates):
```bash
curl -N -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8000/api/research/stream \
  -d '{"query": "Impact of quantum computing on cryptography", "max_iterations": 5}'
```

The streaming endpoint provides real-time updates on:
- Research initialization
- Query generation
- Search execution
- Content processing
- Context extraction
- Report generation
- Final results

## LLM Provider Configuration

### OpenRouter (Default)
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=meta-llama/llama-3-8b-instruct:free
```

### OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-3.5-turbo
```

### Anthropic
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

### Ollama (Local)
```env
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
```

## Testing with Ollama Locally

1. Install Ollama:
```bash
# macOS or Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

2. Start the Ollama service:
```bash
ollama serve
```

3. Pull your desired model (e.g., Llama 2):
```bash
ollama pull llama2
```

4. Configure your `.env` file for Ollama:
```env
# Required API Keys (still needed for web search and content extraction)
SERPAPI_API_KEY=your_serpapi_key
JINA_API_KEY=your_jina_key

# Set Ollama as the LLM provider
LLM_PROVIDER=ollama

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
```

5. Start the API server:
```bash
uvicorn app.main:app --reload
```

6. Test the research endpoint:
```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main features of the Llama 2 model?", "max_iterations": 2}'
```

Available Ollama models:
- `llama2` - General purpose model
- `mistral` - Powerful open-source model
- `codellama` - Code-specialized model
- `llama2-uncensored` - Less restricted version
- `neural-chat` - Optimized for chat

To use a different model, update `OLLAMA_MODEL` in your `.env` file and ensure you've pulled the model with `ollama pull model_name`.

## Development

The project structure:
```
OpenDeepResearcher-API/
├── app/
│   ├── __init__.py      # Version and package info
│   ├── main.py          # FastAPI application and endpoints
│   ├── config.py        # Configuration management
│   ├── researcher.py    # Core research engine with streaming support
│   └── llm_providers.py # LLM provider implementations
├── research_outputs/    # Generated research reports
├── requirements.txt     # Python dependencies
├── .env                # Environment variables (create from .env.example)
├── .env.example        # Example environment configuration
├── LICENSE            # MIT License
└── README.md          # Project documentation
```

## Acknowledgments

This project is based on Justin Pinkney's research notebook implementation. The original work has been adapted into a REST API service with additional features like multi-provider LLM support and parallel processing.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
