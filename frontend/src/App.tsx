import { useState, useEffect } from 'react';
import { MantineProvider, AppShell, Title, Container, Stack, Alert, rem, Text, createTheme, Group, Button } from '@mantine/core';
import { IconInfoCircle, IconBrain, IconAlertCircle, IconChevronDown, IconChevronRight, IconHistory } from '@tabler/icons-react';
import { ResearchForm } from './components/ResearchForm';
import { ResearchProgress } from './components/ResearchProgress';
import { ResearchReport } from './components/ResearchReport';
import { ResearchSidebar } from './components/ResearchSidebar';
import { LLMConfig } from './components/LLMConfig';
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
  const [showConfig, setShowConfig] = useState(true);
  const [showResearchForm, setShowResearchForm] = useState(true);
  const [showProgress, setShowProgress] = useState(true);
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-4');
  const [progressHideTimeout, setProgressHideTimeout] = useState<number | null>(null);
  const [sidebarOpened, setSidebarOpened] = useState(false);
  const [currentReport, setCurrentReport] = useState<{
    query: string;
    report: string;
    timestamp: number;
  } | null>(null);
  
  const handleResearch = async (request: ResearchRequest) => {
    if (!isConnected) {
      setError('API is not available. Please try again later.');
      return;
    }

    // Clear any existing timeout
    if (progressHideTimeout) {
      clearTimeout(progressHideTimeout);
      setProgressHideTimeout(null);
    }

    setIsLoading(true);
    setUpdates([]);
    setReport('');
    setLogs([]);
    setError('');
    
    // Collapse config and form when research starts
    setShowConfig(false);
    setShowResearchForm(false);
    setShowProgress(true);

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
          
          // Update current report for history
          setCurrentReport({
            query: request.query,
            report: update.report,
            timestamp: Date.now()
          });
          
          // Set timeout to hide progress after 2 seconds
          const timeout = setTimeout(() => {
            setShowProgress(false);
          }, 2000);
          setProgressHideTimeout(timeout);
        }
      });

      return () => {
        cleanup();
        if (progressHideTimeout) {
          clearTimeout(progressHideTimeout);
        }
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start research. Please try again.';
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (progressHideTimeout) {
        clearTimeout(progressHideTimeout);
      }
    };
  }, [progressHideTimeout]);

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

  const handleConfigChange = (newProvider: string, newModel: string) => {
    setProvider(newProvider);
    setModel(newModel);
    setUpdates([]);
    setReport('');
    setLogs([]);
    setError('');
  };

  const toggleSection = (section: 'config' | 'form' | 'progress') => {
    switch (section) {
      case 'config':
        setShowConfig(!showConfig);
        break;
      case 'form':
        setShowResearchForm(!showResearchForm);
        break;
      case 'progress':
        setShowProgress(!showProgress);
        break;
    }
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
                  style={{ color: 'var(--mantine-color-blue-6)' }} 
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
              <Group>
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
                <Button
                  variant="subtle"
                  leftSection={<IconHistory size={16} />}
                  onClick={() => setSidebarOpened(true)}
                >
                  History
                </Button>
              </Group>
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

              <Group justify="space-between" align="center" onClick={() => toggleSection('config')} style={{ cursor: 'pointer' }}>
                <Group gap="md">
                  <Title order={3}>LLM Configuration</Title>
                  {!showConfig && (
                    <Text size="sm" c="dimmed" span style={{ marginLeft: '1rem' }}>
                      {`${provider.charAt(0).toUpperCase() + provider.slice(1)} / ${model}`}
                    </Text>
                  )}
                </Group>
                {showConfig ? <IconChevronDown size={20} /> : <IconChevronRight size={20} />}
              </Group>
              {showConfig && <LLMConfig onConfigChange={handleConfigChange} />}

              <Group justify="space-between" align="center" onClick={() => toggleSection('form')} style={{ cursor: 'pointer' }}>
                <Group gap="md">
                  <Title order={3}>Research Query</Title>
                  {!showResearchForm && updates.length > 0 && (
                    <Text size="sm" c="dimmed" span style={{ marginLeft: '1rem' }}>
                      {updates[0]?.message || ''}
                    </Text>
                  )}
                </Group>
                {showResearchForm ? <IconChevronDown size={20} /> : <IconChevronRight size={20} />}
              </Group>
              {showResearchForm && (
                <ResearchForm 
                  onSubmit={handleResearch}
                  isLoading={isLoading}
                  isDisabled={!isConnected}
                />
              )}

              {updates.length > 0 && (
                <>
                  <Group justify="space-between" align="center" onClick={() => toggleSection('progress')} style={{ cursor: 'pointer' }}>
                    <Group gap="md">
                      <Title order={3}>Research Progress</Title>
                      {!showProgress && (
                        <Group gap="xs">
                          {updates[updates.length - 1]?.type === 'complete' ? (
                            <Text size="sm" c="teal" span>Complete</Text>
                          ) : (
                            <>
                              <Text size="sm" c="dimmed" span>
                                {updates[updates.length - 1]?.message || ''}
                              </Text>
                              {updates[updates.length - 1]?.type === 'processing' && (
                                <Text size="sm" c="blue" span>Processing...</Text>
                              )}
                            </>
                          )}
                        </Group>
                      )}
                    </Group>
                    {showProgress ? <IconChevronDown size={20} /> : <IconChevronRight size={20} />}
                  </Group>
                  {showProgress && <ResearchProgress updates={updates} />}
                </>
              )}

              {report && (
                <>
                  <Group justify="space-between" align="center">
                    <Title order={3}>Research Report</Title>
                  </Group>
                  <ResearchReport report={report} logs={logs} />
                </>
              )}
            </Stack>
          </Container>
        </AppShell.Main>
        
        <ResearchSidebar
          opened={sidebarOpened}
          onClose={() => setSidebarOpened(false)}
          currentReport={currentReport || undefined}
        />
      </AppShell>
    </MantineProvider>
  );
}
