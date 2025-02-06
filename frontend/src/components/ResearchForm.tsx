import { TextInput, Button, Paper, Stack, NumberInput, Group, Title, Text, Box } from '@mantine/core';
import { useForm } from '@mantine/form';
import { IconSearch, IconBrain } from '@tabler/icons-react';
import { ResearchRequest } from '../api/client';

interface ResearchFormProps {
  onSubmit: (request: ResearchRequest) => void;
  isLoading: boolean;
  isDisabled?: boolean;
}

export function ResearchForm({ onSubmit, isLoading, isDisabled }: ResearchFormProps) {
  const form = useForm({
    initialValues: {
      query: '',
      max_iterations: 10,
    },
    validate: {
      query: (value) => (value.length < 3 ? 'Query must be at least 3 characters' : null),
      max_iterations: (value) => 
        value < 1 || value > 20 ? 'Iterations must be between 1 and 20' : null,
    },
  });

  return (
    <Paper>
      <form onSubmit={form.onSubmit((values) => onSubmit(values))}>
        <Stack gap="lg">
          <Box>
            <Group gap={8} align="center" mb={4}>
              <IconBrain size={24} style={{ color: 'var(--mantine-color-blue-6)' }} />
              <Title order={3}>Start New Research</Title>
            </Group>
            <Text size="sm" c="dimmed">Enter your research topic and configure the research depth</Text>
          </Box>

          <TextInput
            required
            label="Research Query"
            placeholder="e.g., 'Impact of artificial intelligence on healthcare' or 'Latest developments in quantum computing'"
            {...form.getInputProps('query')}
            size="md"
            disabled={isDisabled}
            styles={{
              label: { 
                marginBottom: 8,
                fontSize: '0.95rem'
              },
              input: { 
                fontSize: '1rem',
                padding: '1.25rem 1rem',
                '&::placeholder': {
                  color: 'var(--mantine-color-gray-5)'
                }
              }
            }}
          />
          
          <NumberInput
            required
            label="Maximum Research Iterations"
            description="Higher values result in more thorough research but take longer"
            min={1}
            max={20}
            {...form.getInputProps('max_iterations')}
            size="md"
            disabled={isDisabled}
            styles={{
              label: { 
                marginBottom: 8,
                fontSize: '0.95rem'
              },
              input: { 
                fontSize: '1rem',
                padding: '1.25rem 1rem'
              },
              description: {
                marginTop: 6
              }
            }}
          />

          <Group justify="flex-end">
            <Button 
              type="submit" 
              size="md"
              leftSection={<IconSearch size={20} />}
              loading={isLoading}
              disabled={isDisabled}
              styles={{
                root: {
                  padding: '0.75rem 2rem',
                  fontSize: '1rem'
                },
                section: {
                  marginRight: '0.5rem'
                }
              }}
            >
              Start Research
            </Button>
          </Group>
        </Stack>
      </form>
    </Paper>
  );
} 