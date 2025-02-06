import { Paper, Title, Text, Stack, Divider, ScrollArea } from '@mantine/core';
import ReactMarkdown from 'react-markdown';

interface ResearchReportProps {
  report: string;
  logs: string[];
}

export function ResearchReport({ report, logs }: ResearchReportProps) {
  return (
    <Paper>
      <Stack gap="lg">
        <Title order={3}>Research Report</Title>
        
        <div className="markdown-content">
          <ReactMarkdown>{report}</ReactMarkdown>
        </div>

        <Stack gap="md">
          <Title order={4}>Process Logs</Title>
          <ScrollArea h={300} type="hover" offsetScrollbars>
            <Stack gap="xs">
              {logs.map((log, index) => (
                <Text 
                  key={index} 
                  size="sm" 
                  c="dimmed"
                  style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}
                >
                  {log}
                </Text>
              ))}
            </Stack>
          </ScrollArea>
        </Stack>
      </Stack>
    </Paper>
  );
} 