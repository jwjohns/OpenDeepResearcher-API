# OpenDeepResearcher-API

A FastAPI implementation of OpenDeepResearcher that provides a REST API for automated web research using LLMs. This project is an API adaptation of [Justin Pinkney's original OpenDeepResearcher](https://github.com/justinpinkney/OpenDeepResearcher).

## Overview

OpenDeepResearcher-API transforms the original notebook-based research tool into a REST API service that:
- Generates intelligent search queries based on your research question
- Searches the web for relevant information
- Evaluates and extracts relevant content from web pages
- Generates a research report
- Saves research outputs and logs for transparency

## Features

- **Intelligent Query Generation**: Uses LLMs to create targeted search queries
- **Parallel Web Search**: Efficiently searches multiple queries simultaneously
- **Content Evaluation**: Evaluates webpage relevance
- **Context Extraction**: Extracts relevant information from web pages
- **Report Generation**: Creates research reports from gathered information
- **Detailed Logging**: Maintains logs of the research process
- **Markdown Output**: Saves research results in formatted markdown files

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/OpenDeepResearcher-API.git
cd OpenDeepResearcher-API
```

2. Create a virtual environment:
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

4. Create a `.env` file with your API keys:
```
OPENROUTER_API_KEY=your_openrouter_key
SERPAPI_API_KEY=your_serpapi_key
JINA_API_KEY=your_jina_key
```

## Usage

1. Start the server:
```bash
python run.py
```

2. Make a research request:
```bash
curl -X POST http://localhost:8080/api/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Your research question here", "max_iterations": 1}'
```

The research results will be:
- Returned in the API response
- Saved as a markdown file in the `research_outputs` directory

## Project Structure

```
OpenDeepResearcher-API/
├── app/
│   ├── __init__.py
│   ├── config.py        # Configuration and environment variables
│   ├── main.py         # FastAPI application
│   └── researcher.py    # Core research engine
├── research_outputs/    # Generated research reports
├── .env                # API keys and configuration
├── .env.example        # Example environment file
├── requirements.txt    # Python dependencies
└── run.py             # Server startup script
```

## API Keys Required

- **OpenRouter**: For LLM access (https://openrouter.ai/)
- **SerpAPI**: For web search (https://serpapi.com/)
- **Jina**: For webpage content extraction (https://jina.ai/)

## Acknowledgments

This project is a REST API implementation of Justin Pinkney's original OpenDeepResearcher notebook. While maintaining the core research capabilities of the original work, this version adds API endpoints, error handling, logging, and markdown output generation. This is an experimental project and may need additional work for production use.

## License

MIT License - See LICENSE file for details
