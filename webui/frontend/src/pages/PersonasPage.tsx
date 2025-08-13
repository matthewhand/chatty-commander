import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Box, Container, Typography, Grid, Card, CardContent, CardActions, Button, Chip, Stack, Tooltip } from '@mui/material';
import { apiService } from '../services/apiService';

const PersonasPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['advisorPersonas'],
    queryFn: () => apiService.getAdvisorPersonas(),
  });

  const switchMutation = useMutation({
    mutationFn: ({ contextKey, personaId }: { contextKey: string; personaId: string }) =>
      apiService.switchAdvisorPersona(contextKey, personaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['advisorContextStats'] });
    },
  });

  const { data: stats } = useQuery({
    queryKey: ['advisorContextStats'],
    queryFn: () => apiService.getAdvisorContextStats(),
  });

  const personas = data?.personas || [];
  const defaultPersona = data?.default_persona;

  const sampleContextKey = 'discord:c1:u1';

  return (
    <Box sx={{ flexGrow: 1, p: 3, background: 'linear-gradient(to right bottom, #2e3a4d, #1a202c)', minHeight: 'calc(100vh - 64px)' }}>
      <Container maxWidth="lg">
        <Typography variant="h4" gutterBottom sx={{ color: 'white', mb: 4 }}>
          Personas
        </Typography>

        {isLoading && <Typography>Loading personas...</Typography>}
        {isError && <Typography color="error">{(error as Error)?.message || 'Failed to load personas'}</Typography>}

        <Grid container spacing={3}>
          {personas.map((p: any) => (
            <Grid item xs={12} sm={6} md={4} key={p.id}>
              <Card sx={{ borderRadius: 2, height: '100%' }}>
                <CardContent>
                  <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
                    <Typography variant="h6">{p.name}</Typography>
                    {p.is_default && <Chip label="Default" color="primary" size="small" />}
                  </Stack>
                  {p.system_prompt && (
                    <Tooltip title={p.system_prompt} placement="top">
                      <Typography variant="body2" sx={{ mt: 1 }} noWrap>
                        {p.system_prompt}
                      </Typography>
                    </Tooltip>
                  )}
                </CardContent>
                <CardActions>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => switchMutation.mutate({ contextKey: sampleContextKey, personaId: p.id })}
                    disabled={switchMutation.isPending}
                  >
                    Use for Sample Context
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>

        {stats && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6">Context Stats</Typography>
            <Typography variant="body2">Total Contexts: {stats.total_contexts}</Typography>
          </Box>
        )}
      </Container>
    </Box>
  );
};

export default PersonasPage;