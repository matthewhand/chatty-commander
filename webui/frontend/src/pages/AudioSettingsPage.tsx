import React, { useState } from 'react';
import { Box, Typography, Select, MenuItem, FormControl, InputLabel, Button, Container, Grid, Paper } from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Save as SaveIcon, Mic as MicIcon, VolumeUp as VolumeUpIcon } from '@mui/icons-material';

// Placeholder services for audio devices
const getAudioDevices = async () => {
  // Simulate fetching devices
  console.log('Fetching audio devices...');
  return { input: ['Default Microphone', 'External USB Mic'], output: ['Default Speakers', 'Headphones'] };
};
const saveAudioSettings = async (settings: any) => {
  // Placeholder save
  console.log('Saving audio settings:', settings);
  return new Promise((resolve) => setTimeout(resolve, 1000));
};

const AudioSettingsPage: React.FC = () => {
  const [inputDevice, setInputDevice] = useState('');
  const [outputDevice, setOutputDevice] = useState('');

  const { data: devices } = useQuery({
    queryKey: ['audioDevices'],
    queryFn: getAudioDevices,
  });

  const mutation = useMutation({
    mutationFn: saveAudioSettings,
  });

  const handleSave = () => {
    mutation.mutate({ inputDevice, outputDevice });
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3, background: 'linear-gradient(to right bottom, #2e3a4d, #1a202c)', minHeight: 'calc(100vh - 64px)' }}>
      <Container maxWidth="md">
        <Typography variant="h4" gutterBottom sx={{ color: 'white', mb: 4 }}>
          <MicIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Audio Settings
        </Typography>
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>Audio Devices</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel id="input-device-label">Input Device</InputLabel>
                <Select
                  labelId="input-device-label"
                  value={inputDevice}
                  onChange={(e) => setInputDevice(e.target.value as string)}
                  startAdornment={<MicIcon sx={{ mr: 1, color: 'action.active' }} />}
                >
                  {devices?.input.map((dev) => (
                    <MenuItem key={dev} value={dev}>{dev}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel id="output-device-label">Output Device</InputLabel>
                <Select
                  labelId="output-device-label"
                  value={outputDevice}
                  onChange={(e) => setOutputDevice(e.target.value as string)}
                  startAdornment={<VolumeUpIcon sx={{ mr: 1, color: 'action.active' }} />}
                >
                  {devices?.output.map((dev) => (
                    <MenuItem key={dev} value={dev}>{dev}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                onClick={handleSave}
                disabled={mutation.isPending}
                startIcon={<SaveIcon />}
              >
                {mutation.isPending ? 'Saving...' : 'Save Settings'}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      </Container>
    </Box>
  );
};

export default AudioSettingsPage;