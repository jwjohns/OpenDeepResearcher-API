import { Timeline, Text, Paper, Title, Badge, Stack, rem, Progress, Group, ThemeIcon, ScrollArea } from '@mantine/core';
import { IconSearch, IconCheck, IconX, IconLink, IconBrain, IconLoader2 } from '@tabler/icons-react';
import { ResearchUpdate } from '../api/client';
import { useEffect, useState, useRef } from 'react';

interface ResearchProgressProps {
  updates: ResearchUpdate[];
}

export function ResearchProgress({ updates }: ResearchProgressProps) {
  const [progress, setProgress] = useState(0);
  const [prevProgress, setPrevProgress] = useState(0);
  const [urlsInCurrentIteration, setUrlsInCurrentIteration] = useState(0);
  const [processedUrls, setProcessedUrls] = useState(0);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const latestUpdate = updates[updates.length - 1];
  const progressTimeout = useRef<number>();

  // Track URLs and iterations
  useEffect(() => {
    if (!latestUpdate) return;

    if (latestUpdate.type === 'links' && latestUpdate.count) {
      setUrlsInCurrentIteration(latestUpdate.count);
      setProcessedUrls(0);
    } else if (latestUpdate.type === 'processing' && latestUpdate.url) {
      setProcessedUrls(prev => prev + 1);
    }
  }, [latestUpdate]);

  useEffect(() => {
    // Calculate target progress based on research stages
    let targetProgress = 0;
    
    if (latestUpdate?.type === 'complete') {
      targetProgress = 100;
    } else if (latestUpdate?.type === 'error') {
      targetProgress = 0;
    } else if (latestUpdate?.iteration) {
      // Base progress from iteration (max 80% for iterations)
      const iterationBase = (latestUpdate.iteration * 8);
      
      // Calculate progress within current iteration
      let iterationProgress = 0;
      if (urlsInCurrentIteration > 0) {
        // Each URL processing contributes to the iteration progress
        const urlProgress = (processedUrls / urlsInCurrentIteration) * 10;
        iterationProgress = Math.min(urlProgress, 10);
      }

      // Add stage-specific progress
      let stageProgress = 0;
      switch (latestUpdate.type) {
        case 'queries':
          stageProgress = 1;
          break;
        case 'links':
          stageProgress = 2;
          break;
        case 'processing':
          stageProgress = iterationProgress;
          break;
        case 'evaluation':
          stageProgress = iterationProgress;
          break;
        case 'context':
          stageProgress = iterationProgress + 1;
          break;
      }
      
      targetProgress = Math.min(iterationBase + stageProgress, 85);
    } else {
      // Initial stages
      switch (latestUpdate?.type) {
        case 'start':
          targetProgress = 5;
          break;
        case 'queries':
          targetProgress = 8;
          break;
        case 'progress':
          targetProgress = 10;
          break;
      }
    }

    // Only increase progress, never decrease (unless error/complete)
    if (latestUpdate?.type !== 'error' && targetProgress < prevProgress) {
      targetProgress = prevProgress;
    }

    // Smoothly animate to target progress
    if (progressTimeout.current) {
      clearTimeout(progressTimeout.current);
    }

    const step = () => {
      setProgress(current => {
        const next = current < targetProgress 
          ? Math.min(current + 1, targetProgress)
          : Math.max(current - 1, targetProgress);
        
        if (next !== targetProgress) {
          progressTimeout.current = setTimeout(step, 50);
        } else {
          setPrevProgress(next);
        }
        
        return next;
      });
    };

    step();

    return () => {
      if (progressTimeout.current) {
        clearTimeout(progressTimeout.current);
      }
    };
  }, [latestUpdate, prevProgress, urlsInCurrentIteration, processedUrls]);

  // Auto-scroll effect
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({
        top: scrollAreaRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [updates]);

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
            color={latestUpdate?.type === 'complete' ? 'teal' : 'blue'}
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