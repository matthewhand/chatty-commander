import React, { useState } from 'react';
import { Box, Typography, TextField, Button, Switch, FormControlLabel, Container, Grid, Paper } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Save as SaveIcon, Settings as SettingsIcon } from '@mui/icons-material';

// Assuming a service for saving config
const saveConfig = async (config: any) => {
  // Placeholder API call
  console.log('Saving config:', config);
  return new Promise((resolve) => setTimeout(resolve, 1000));
};

const ConfigurationPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState({
    apiKey: '',
    enableVoice: true,
    theme: 'dark',
  });

  const mutation = useMutation({
    mutationFn: saveConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfig({ ...config, [e.target.name]: e.target.value });
  };

  const handleSwitch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfig({ ...config, [e.target.name]: e.target.checked });
  };

  const handleSubmit = () => {
    mutation.mutate(config);
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3, background: 'linear-gradient(to right bottom, #2e3a4d, #1a202c)', minHeight: 'calc(100vh - 64px)' }}>
      <Container maxWidth="md">
        <Typography variant="h4" gutterBottom sx={{ color: 'white', mb: 4 }}>
          <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Configuration
        </Typography>
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>General Settings</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="API Key"
                name="apiKey"
                type="password"
                value={config.apiKey}
                onChange={handleChange}
                fullWidth
                helperText="Enter your API key for external services."
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Theme"
                name="theme"
                value={config.theme}
                onChange={handleChange}
                fullWidth
                select
                SelectProps={{ native: true }}
                helperText="Choose the application theme."
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.enableVoice}
                    onChange={handleSwitch}
                    name="enableVoice"
                    color="primary"
                  />
                }
                label="Enable Voice Commands"
              />
            </Grid>
            <Grid item xs={12} sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={mutation.isPending}
                startIcon={<SaveIcon />}
              >
                {mutation.isPending ? 'Saving...' : 'Save Configuration'}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      </Container>
    </Box>
  );
};

export default ConfigurationPage;