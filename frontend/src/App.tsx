import { useState, useEffect } from 'react';
import { MantineProvider, AppShell, Title, Container, Stack, Alert, rem, Text, createTheme, Group } from '@mantine/core';
import { IconInfoCircle, IconBrain, IconAlertCircle } from '@tabler/icons-react';
import { ResearchForm } from './components/ResearchForm';
import { ResearchProgress } from './components/ResearchProgress';
import { ResearchReport } from './components/ResearchReport';
import { apiClient, ResearchRequest, ResearchUpdate } from './api/client';

const theme = createTheme({
  primaryColor: 'blue',
  fontFamily: 'Inter, sans-serif',
  defaultRadius: 'md',
  components: {
    Paper: {
      defaultProps: {
        p: 'xl',
        radius: 'md',
        withBorder: true,
      },
      styles: {
        root: {
          border: '1px solid var(--mantine-color-gray-3)',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
        }
      }
    },
    Title: {
      styles: {
        root: {
          fontWeight: 600,
        }
      }
    },
    Button: {
      defaultProps: {
        size: 'md',
      },
      styles: {
        root: {
          fontWeight: 600,
          transition: 'transform 0.2s ease',
          '&:active': {
            transform: 'translateY(1px)'
          }
        }
      }
    },
    TextInput: {
      styles: {
        label: {
          marginBottom: '0.5rem',
          fontWeight: 500,
        },
        input: {
          fontSize: '1rem',
          '&:focus': {
            borderColor: 'var(--mantine-color-blue-5)',
            boxShadow: '0 0 0 3px var(--mantine-color-blue-1)'
          }
        }
      }
    },
    NumberInput: {
      styles: {
        label: {
          marginBottom: '0.5rem',
          fontWeight: 500,
        },
        input: {
          fontSize: '1rem',
          '&:focus': {
            borderColor: 'var(--mantine-color-blue-5)',
            boxShadow: '0 0 0 3px var(--mantine-color-blue-1)'
          }
        }
      }
    }
  }
});

export default function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [updates, setUpdates] = useState<ResearchUpdate[]>([]);
  const [report, setReport] = useState<string>('');
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string>('');
  const [isConnected, setIsConnected] = useState(true);

  const handleResearch = async (request: ResearchRequest) => {
    if (!isConnected) {
      setError('API is not available. Please try again later.');
      return;
    }

    setIsLoading(true);
    setUpdates([]);
    setReport('');
    setLogs([]);
    setError('');

    try {
      const cleanup = apiClient.streamResearch(request, (update) => {
        if (update.type === 'error') {
          setError(update.message);
          setIsLoading(false);
          return;
        }

        if (update.type === 'warning') {
          setError(update.message);
          return;
        }

        setUpdates(prev => [...prev, update]);
        
        if (update.type === 'complete' && update.report) {
          setReport(update.report);
          setLogs(update.logs || []);
          setIsLoading(false);
        }
      });

      return cleanup;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start research. Please try again.';
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  // Add periodic health check
  useEffect(() => {
    const checkHealth = async () => {
      const isHealthy = await apiClient.checkHealth();
      setIsConnected(isHealthy);
      if (!isHealthy) {
        setError('API connection lost. Please check your connection and try again.');
      } else if (error === 'API connection lost. Please check your connection and try again.') {
        setError(''); // Clear the error if we're back online
      }
    };

    // Initial check
    checkHealth();

    // Set up periodic health check
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [error]);

  const handleErrorClose = () => {
    setError('');
  };

  return (
    <MantineProvider theme={theme}>
      <AppShell
        header={{ height: 70 }}
        padding="md"
        styles={{
          main: {
            background: 'var(--mantine-color-gray-0)',
            paddingTop: 'calc(var(--mantine-spacing-xl) + 70px)',
          }
        }}
      >
        <AppShell.Header style={{ 
          borderBottom: '1px solid var(--mantine-color-gray-2)',
          background: 'white'
        }}>
          <Container size="lg" h="100%">
            <Group justify="space-between" h="100%" wrap="nowrap">
              <Group gap="xs" wrap="nowrap">
                <IconBrain 
                  size={32} 
                  style={{ 
                    color: 'var(--mantine-color-blue-6)',
                  }} 
                />
                <div>
                  <Title order={1} size={rem(24)} style={{ 
                    color: 'var(--mantine-color-dark-9)',
                    lineHeight: 1.1
                  }}>
                    OpenDeepResearcher
                  </Title>
                  <Text size="xs" c="dimmed" fw={500}>AI-Powered Research Assistant</Text>
                </div>
              </Group>
              {!isConnected && (
                <Alert 
                  icon={<IconAlertCircle size={16} />}
                  color="red"
                  variant="light"
                  styles={{
                    root: {
                      padding: '0.5rem 0.75rem',
                    },
                    message: {
                      margin: 0,
                    }
                  }}
                >
                  API Disconnected
                </Alert>
              )}
            </Group>
          </Container>
        </AppShell.Header>

        <AppShell.Main>
          <Container size="lg">
            <Stack gap="xl">
              {error && (
                <Alert 
                  icon={<IconInfoCircle size={16} />} 
                  title="Error" 
                  color="red"
                  withCloseButton
                  onClose={handleErrorClose}
                  radius="md"
                  styles={{
                    title: { fontWeight: 600 }
                  }}
                >
                  {error}
                </Alert>
              )}

              <ResearchForm 
                onSubmit={handleResearch}
                isLoading={isLoading}
                isDisabled={!isConnected}
              />

              {updates.length > 0 && (
                <ResearchProgress updates={updates} />
              )}

              {report && (
                <ResearchReport 
                  report={report}
                  logs={logs}
                />
              )}
            </Stack>
          </Container>
        </AppShell.Main>
      </AppShell>
    </MantineProvider>
  );
}
