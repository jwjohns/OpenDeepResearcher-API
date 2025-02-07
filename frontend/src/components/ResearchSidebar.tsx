import { Drawer, Stack, Text, Title, ScrollArea, Card, Group, Button, Badge } from '@mantine/core';
import { IconHistory, IconChevronLeft, IconDownload } from '@tabler/icons-react';
import { useState, useEffect } from 'react';

interface ResearchMeta {
  id: string;
  query: string;
  timestamp: number;
  preview: string;
}

interface ResearchSidebarProps {
  opened: boolean;
  onClose: () => void;
  currentReport?: {
    query: string;
    report: string;
    timestamp?: number;
  };
}

export function ResearchSidebar({ opened, onClose, currentReport }: ResearchSidebarProps) {
  const [history, setHistory] = useState<ResearchMeta[]>([]);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [reportContent, setReportContent] = useState<string | null>(null);

  // Load history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('researchHistory');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Save current report to history when it changes
  useEffect(() => {
    if (currentReport && currentReport.report) {
      const newMeta: ResearchMeta = {
        id: Date.now().toString(),
        query: currentReport.query,
        timestamp: currentReport.timestamp || Date.now(),
        preview: currentReport.report.substring(0, 150) + '...'
      };

      const updatedHistory = [newMeta, ...history].slice(0, 50); // Keep last 50 reports
      setHistory(updatedHistory);
      localStorage.setItem('researchHistory', JSON.stringify(updatedHistory));
      
      // Save full report content
      localStorage.setItem(`report_${newMeta.id}`, currentReport.report);
    }
  }, [currentReport]);

  const handleReportClick = async (id: string) => {
    setSelectedReport(id);
    // Try to load from localStorage first
    const savedReport = localStorage.getItem(`report_${id}`);
    if (savedReport) {
      setReportContent(savedReport);
    } else {
      // If not in localStorage, fetch from backend
      try {
        const response = await fetch(`/api/research/${id}`);
        if (response.ok) {
          const report = await response.text();
          setReportContent(report);
          // Cache for future use
          localStorage.setItem(`report_${id}`, report);
        }
      } catch (error) {
        console.error('Failed to fetch report:', error);
      }
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Drawer 
      opened={opened} 
      onClose={onClose} 
      position="right"
      size="md"
      title={
        <Group>
          <IconHistory size={20} />
          <Title order={3}>Research History</Title>
        </Group>
      }
    >
      <Stack h="100%" gap="md">
        <ScrollArea h="calc(100vh - 100px)">
          <Stack gap="md" p="md">
            {history.map((item) => (
              <Card 
                key={item.id}
                withBorder
                padding="md"
                radius="md"
                style={{ 
                  cursor: 'pointer',
                  backgroundColor: selectedReport === item.id ? 'var(--mantine-color-blue-0)' : undefined
                }}
                onClick={() => handleReportClick(item.id)}
              >
                <Stack gap="xs">
                  <Group justify="space-between" wrap="nowrap">
                    <Text size="sm" fw={500} lineClamp={1}>
                      {item.query}
                    </Text>
                    <Badge size="sm" variant="light">
                      {formatDate(item.timestamp)}
                    </Badge>
                  </Group>
                  <Text size="sm" c="dimmed" lineClamp={2}>
                    {item.preview}
                  </Text>
                </Stack>
              </Card>
            ))}
          </Stack>
        </ScrollArea>

        {selectedReport && reportContent && (
          <Card withBorder padding="md" radius="md">
            <Stack gap="sm">
              <Group justify="space-between">
                <Button 
                  variant="subtle" 
                  leftSection={<IconChevronLeft size={16} />}
                  onClick={() => {
                    setSelectedReport(null);
                    setReportContent(null);
                  }}
                >
                  Back to List
                </Button>
                <Button
                  variant="light"
                  leftSection={<IconDownload size={16} />}
                  onClick={() => {
                    const blob = new Blob([reportContent], { type: 'text/markdown' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `research_${selectedReport}.md`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                  }}
                >
                  Download
                </Button>
              </Group>
              <ScrollArea h={300}>
                <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                  {reportContent}
                </Text>
              </ScrollArea>
            </Stack>
          </Card>
        )}
      </Stack>
    </Drawer>
  );
} 