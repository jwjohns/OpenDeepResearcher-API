import { Select, Paper, Title, Group, Text, Alert } from '@mantine/core';
import { IconBrain, IconAlertCircle } from '@tabler/icons-react';
import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface LLMConfigProps {
  onConfigChange?: (provider: string, model: string) => void;
}

interface Provider {
  id: string;
  name: string;
  available: boolean;
}

interface ConfigResponse {
  current_provider: string;
  current_model: string;
  available_providers: Provider[];
  available_models: Record<string, string[]>;
}

export function LLMConfig({ onConfigChange }: LLMConfigProps) {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [provider, setProvider] = useState<string>('');
  const [model, setModel] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/config/llm`);
      const data = await response.json();
      setConfig(data);
      setProvider(data.current_provider);
      setModel(data.current_model);
    } catch (error) {
      setError('Failed to load LLM configuration');
    }
  };

  const handleProviderChange = async (value: string | null) => {
    if (!value) return;
    setProvider(value);
    // Reset model when provider changes
    setModel('');
    
    try {
      setLoading(true);
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/config/llm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ provider: value }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update provider');
      }
      
      if (onConfigChange) {
        onConfigChange(value, model);
      }
      
      setError('');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update provider');
    } finally {
      setLoading(false);
    }
  };

  const handleModelChange = async (value: string | null) => {
    if (!value) return;
    setModel(value);
    
    try {
      setLoading(true);
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/config/llm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ provider, model: value }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update model');
      }
      
      if (onConfigChange) {
        onConfigChange(provider, value);
      }
      
      setError('');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update model');
    } finally {
      setLoading(false);
    }
  };

  if (!config) {
    return null;
  }

  return (
    <Paper>
      <Group gap="xs" mb="md">
        <IconBrain size={24} style={{ color: 'var(--mantine-color-blue-6)' }} />
        <Title order={3}>LLM Configuration</Title>
      </Group>

      {error && (
        <Alert 
          icon={<IconAlertCircle size={16} />}
          color="red"
          mb="md"
          title="Error"
          variant="light"
        >
          {error}
        </Alert>
      )}

      <Group grow align="flex-start">
        <div>
          <Text size="sm" fw={500} mb={4}>Provider</Text>
          <Select
            data={config.available_providers.map(p => ({
              value: p.id,
              label: `${p.name}${!p.available ? ' (No API Key)' : ''}`,
              disabled: !p.available
            }))}
            value={provider}
            onChange={handleProviderChange}
            disabled={loading}
          />
        </div>

        <div>
          <Text size="sm" fw={500} mb={4}>Model</Text>
          <Select
            data={config.available_models[provider] || []}
            value={model}
            onChange={handleModelChange}
            disabled={loading || !provider}
            placeholder="Select a model"
          />
        </div>
      </Group>
    </Paper>
  );
} 