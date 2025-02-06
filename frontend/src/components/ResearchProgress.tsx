import { Timeline, Text, Paper, Title, Badge, Stack, rem, Progress, Group, ThemeIcon, ScrollArea } from '@mantine/core';
import { IconSearch, IconCheck, IconX, IconLink, IconBrain, IconLoader2 } from '@tabler/icons-react';
import { ResearchUpdate } from '../api/client';
import { useEffect, useState, useRef } from 'react';

interface ResearchProgressProps {
  updates: ResearchUpdate[];
}

export function ResearchProgress({ updates }: ResearchProgressProps) {
  const [progress, setProgress] = useState(0);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const latestUpdate = updates[updates.length - 1];

  useEffect(() => {
    // Calculate progress based on research stages
    if (latestUpdate?.type === 'complete') {
      setProgress(100);
    } else if (latestUpdate?.type === 'error') {
      setProgress(0);
    } else if (latestUpdate?.iteration) {
      // Each iteration contributes to progress
      const iterationProgress = Math.min((latestUpdate.iteration * 10), 90);
      
      // Add extra progress based on the stage within the iteration
      let stageBonus = 0;
      switch (latestUpdate.type) {
        case 'queries':
          stageBonus = 2;
          break;
        case 'links':
          stageBonus = 4;
          break;
        case 'processing':
          stageBonus = 6;
          break;
        case 'evaluation':
          stageBonus = 8;
          break;
        case 'context':
          stageBonus = 9;
          break;
      }
      
      setProgress(Math.min(iterationProgress + stageBonus, 90));
    } else {
      // Initial stages
      switch (latestUpdate?.type) {
        case 'start':
          setProgress(5);
          break;
        case 'queries':
          setProgress(10);
          break;
        case 'progress':
          setProgress(15);
          break;
      }
    }

    // Auto-scroll to bottom when new updates arrive
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({
        top: scrollAreaRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [latestUpdate, updates]);

  const getStatusIcon = (type: string) => {
    switch (type) {
      case 'start':
        return <IconBrain style={{ animation: 'pulse 2s infinite' }} />;
      case 'queries':
        return <IconSearch />;
      case 'processing':
        return <IconLoader2 style={{ animation: 'spin 1s linear infinite' }} />;
      case 'complete':
        return <IconCheck />;
      case 'error':
        return <IconX />;
      default:
        return <IconBrain />;
    }
  };

  const getStatusColor = (type: string, useful?: boolean) => {
    if (useful !== undefined) return useful ? 'teal' : 'red';
    switch (type) {
      case 'complete':
        return 'teal';
      case 'error':
        return 'red';
      case 'processing':
        return 'blue';
      default:
        return 'gray';
    }
  };

  return (
    <Paper>
      <Stack gap="lg">
        <div>
          <Group justify="space-between" mb="xs">
            <Title order={3}>Research Progress</Title>
            <Badge 
              size="lg"
              variant="light"
              color={getStatusColor(latestUpdate?.type || 'start')}
            >
              {latestUpdate?.type === 'complete' ? 'Complete' : 'In Progress'}
            </Badge>
          </Group>
          <Progress 
            value={progress} 
            size="lg" 
            radius="xl"
            color={getStatusColor(latestUpdate?.type || 'start')}
            striped
            animated={progress < 100}
          />
        </div>

        <ScrollArea 
          h={400} 
          offsetScrollbars 
          scrollbarSize={8}
          viewportRef={scrollAreaRef}
          styles={{
            root: { 
              border: '1px solid var(--mantine-color-gray-3)',
              borderRadius: 'var(--mantine-radius-md)'
            },
            viewport: { padding: '1rem' }
          }}
        >
          <Timeline 
            active={updates.length - 1} 
            bulletSize={32}
            lineWidth={2}
            styles={{
              item: {
                paddingLeft: rem(32),
              }
            }}
          >
            {updates.map((update, index) => (
              <Timeline.Item
                key={index}
                bullet={
                  <ThemeIcon 
                    size={32} 
                    radius="xl"
                    color={getStatusColor(update.type, update.useful)}
                    variant="light"
                  >
                    {getStatusIcon(update.type)}
                  </ThemeIcon>
                }
                title={
                  <Group gap="xs" mb={4}>
                    <Text size="lg" fw={600}>
                      {update.type.charAt(0).toUpperCase() + update.type.slice(1)}
                    </Text>
                    {update.iteration && 
                      <Badge 
                        variant="light"
                        size="lg"
                      >
                        Iteration {update.iteration}
                      </Badge>
                    }
                  </Group>
                }
              >
                <Text c="dimmed" size="sm" mb={update.queries || update.url ? 'xs' : 0}>
                  {update.message}
                </Text>
                
                {update.queries && (
                  <Text size="sm" mb="xs">
                    <Text span fw={500}>Queries: </Text>
                    {update.queries.map((query, i) => (
                      <Badge 
                        key={i}
                        variant="dot"
                        size="sm"
                        mr={4}
                        style={{ fontWeight: 'normal' }}
                      >
                        {query}
                      </Badge>
                    ))}
                  </Text>
                )}
                
                {update.url && (
                  <Group gap="xs">
                    <IconLink size={16} style={{ color: 'var(--mantine-color-gray-6)' }} />
                    <Text size="sm" style={{ wordBreak: 'break-word' }} component="a" href={update.url} target="_blank">
                      {update.url}
                    </Text>
                    {update.useful !== undefined && (
                      <Badge 
                        variant="light"
                        color={update.useful ? 'teal' : 'red'}
                        size="sm"
                      >
                        {update.useful ? 'Useful' : 'Not Useful'}
                      </Badge>
                    )}
                  </Group>
                )}
              </Timeline.Item>
            ))}
          </Timeline>
        </ScrollArea>
      </Stack>
    </Paper>
  );
} 