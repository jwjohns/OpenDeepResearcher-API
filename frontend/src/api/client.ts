import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface ResearchRequest {
  query: string;
  max_iterations?: number;
}

export interface ResearchResponse {
  report: string;
  logs: string[];
}

export interface ResearchUpdate {
  type: string;
  message: string;
  queries?: string[];
  iteration?: number;
  count?: number;
  url?: string;
  useful?: boolean;
  report?: string;
  logs?: string[];
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async performResearch(request: ResearchRequest): Promise<ResearchResponse> {
    const response = await axios.post(`${this.baseURL}/research`, request);
    return response.data;
  }

  streamResearch(request: ResearchRequest, onUpdate: (update: ResearchUpdate) => void): () => void {
    // First make the POST request to start the research
    const startResearch = async () => {
      try {
        const response = await fetch(`${this.baseURL}/research/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request)
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No response body');
        }

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                onUpdate(data);

                if (data.type === 'complete' || data.type === 'error') {
                  reader.cancel();
                  return;
                }
              } catch (error) {
                console.error('Error parsing SSE data:', error);
              }
            }
          }
        }
      } catch (error) {
        console.error('SSE Error:', error);
        onUpdate({
          type: 'error',
          message: error instanceof Error ? error.message : 'Connection error. Please try again.'
        });
      }
    };

    // Start the research process
    startResearch();

    // Return cleanup function
    return () => {
      // Nothing to clean up since we're using fetch
      onUpdate({
        type: 'info',
        message: 'Research connection closed'
      });
    };
  }

  async checkHealth(): Promise<boolean> {
    try {
      const response = await axios.get(`${this.baseURL}/health`);
      return response.data.status === 'healthy';
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
}

export const apiClient = new APIClient(); 