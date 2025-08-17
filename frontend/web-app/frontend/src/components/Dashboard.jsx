import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Divider,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Settings,
  Refresh,
  VolumeUp,
  Computer,
  Chat,
  Home,
  CheckCircle,
  Error,
  Warning,
  Info,
  Send,
  History,
  Code,
  Api
} from '@mui/icons-material';
import { useWebSocket } from '../hooks/useWebSocket';
import { apiService } from '../services/apiService';

const Dashboard = () => {
  // State management
  const [systemStatus, setSystemStatus] = useState(null);
  const [currentState, setCurrentState] = useState('idle');
  const [activeModels, setActiveModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [configDialog, setConfigDialog] = useState(false);
  const [commandDialog, setCommandDialog] = useState(false);
  const [commandHistory, setCommandHistory] = useState([]);
  const [realTimeEvents, setRealTimeEvents] = useState([]);
  const [config, setConfig] = useState(null);
  const [newCommand, setNewCommand] = useState({ command: '', parameters: {} });
  const [autoRefresh, setAutoRefresh] = useState(true);

  // WebSocket connection
  const {
    isConnected,
    lastMessage,
    sendMessage,
    connectionStatus
  } = useWebSocket('ws://localhost:8100/ws');

  // Load initial data
  const loadSystemData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [statusResponse, stateResponse, configResponse] = await Promise.all([
        apiService.getStatus(),
        apiService.getState(),
        apiService.getConfig()
      ]);

      setSystemStatus(statusResponse);
      setCurrentState(stateResponse.current_state);
      setActiveModels(stateResponse.active_models);
      setConfig(configResponse);

    } catch (err) {
      setError(`Failed to load system data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      const message = JSON.parse(lastMessage.data);

      // Add to real-time events
      setRealTimeEvents(prev => [
        {
          id: Date.now(),
          timestamp: new Date().toLocaleTimeString(),
          type: message.type,
          data: message.data
        },
        ...prev.slice(0, 49) // Keep last 50 events
      ]);

      // Handle specific message types
      switch (message.type) {
        case 'state_change':
          setCurrentState(message.data.new_state);
          break;
        case 'command_detected':
        case 'command_executed':
          setCommandHistory(prev => [
            {
              id: Date.now(),
              command: message.data.command,
              timestamp: new Date().toLocaleTimeString(),
              type: message.type,
              success: message.data.success,
              executionTime: message.data.execution_time
            },
            ...prev.slice(0, 19) // Keep last 20 commands
          ]);
          break;
        case 'config_updated':
          loadSystemData(); // Reload data when config changes
          break;
      }
    }
  }, [lastMessage, loadSystemData]);

  // Auto-refresh data
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(loadSystemData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, loadSystemData]);

  // Initial load
  useEffect(() => {
    loadSystemData();
  }, [loadSystemData]);

  // Handle state change
  const handleStateChange = async (newState) => {
    try {
      await apiService.changeState(newState);
      setCurrentState(newState);
    } catch (err) {
      setError(`Failed to change state: ${err.message}`);
    }
  };

  // Handle command execution
  const handleExecuteCommand = async () => {
    try {
      const result = await apiService.executeCommand(newCommand.command, newCommand.parameters);
      setCommandHistory(prev => [
        {
          id: Date.now(),
          command: newCommand.command,
          timestamp: new Date().toLocaleTimeString(),
          type: 'manual_execution',
          success: result.success,
          executionTime: result.execution_time,
          message: result.message
        },
        ...prev.slice(0, 19)
      ]);
      setCommandDialog(false);
      setNewCommand({ command: '', parameters: {} });
    } catch (err) {
      setError(`Failed to execute command: ${err.message}`);
    }
  };

  // Get state color and icon
  const getStateInfo = (state) => {
    switch (state) {
      case 'idle':
        return { color: 'default', icon: <Home />, label: 'Idle' };
      case 'computer':
        return { color: 'primary', icon: <Computer />, label: 'Computer' };
      case 'chatty':
        return { color: 'secondary', icon: <Chat />, label: 'Chatty' };
      default:
        return { color: 'default', icon: <Home />, label: 'Unknown' };
    }
  };

  // Get event icon
  const getEventIcon = (type) => {
    switch (type) {
      case 'state_change':
        return <Settings color="primary" />;
      case 'command_detected':
        return <VolumeUp color="success" />;
      case 'command_executed':
        return <PlayArrow color="info" />;
      case 'system_event':
        return <Info color="warning" />;
      default:
        return <Info />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading Dashboard...</Typography>
      </Box>
    );
  }

  const stateInfo = getStateInfo(currentState);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          ChattyCommander Dashboard
        </Typography>
        <Box display="flex" gap={1}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                size="small"
              />
            }
            label="Auto Refresh"
          />
          <Tooltip title="Refresh Data">
            <IconButton onClick={loadSystemData} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<Settings />}
            onClick={() => setConfigDialog(true)}
          >
            Config
          </Button>
          <Button
            variant="contained"
            startIcon={<Send />}
            onClick={() => setCommandDialog(true)}
          >
            Execute Command
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Status Cards */}
      <Grid container spacing={3} mb={3}>
        {/* System Status */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <CheckCircle color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">System Status</Typography>
              </Box>
              <Typography variant="h4" color="success.main">
                {systemStatus?.status || 'Unknown'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Uptime: {systemStatus?.uptime || 'Unknown'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Version: {systemStatus?.version || 'Unknown'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Current State */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                {stateInfo.icon}
                <Typography variant="h6" sx={{ ml: 1 }}>Current State</Typography>
              </Box>
              <Chip
                label={stateInfo.label}
                color={stateInfo.color}
                size="large"
                sx={{ fontSize: '1.1rem', height: 40 }}
              />
              <Box mt={2}>
                <Button
                  size="small"
                  onClick={() => handleStateChange('idle')}
                  disabled={currentState === 'idle'}
                  sx={{ mr: 1, mb: 1 }}
                >
                  Idle
                </Button>
                <Button
                  size="small"
                  onClick={() => handleStateChange('computer')}
                  disabled={currentState === 'computer'}
                  sx={{ mr: 1, mb: 1 }}
                >
                  Computer
                </Button>
                <Button
                  size="small"
                  onClick={() => handleStateChange('chatty')}
                  disabled={currentState === 'chatty'}
                  sx={{ mb: 1 }}
                >
                  Chatty
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Models */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Code color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Active Models</Typography>
              </Box>
              <Typography variant="h4" color="primary.main">
                {activeModels.length}
              </Typography>
              <Box mt={1}>
                {activeModels.map((model, index) => (
                  <Chip
                    key={index}
                    label={model}
                    size="small"
                    sx={{ mr: 0.5, mb: 0.5 }}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* WebSocket Status */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Api color={isConnected ? 'success' : 'error'} sx={{ mr: 1 }} />
                <Typography variant="h6">Connection</Typography>
              </Box>
              <Chip
                label={isConnected ? 'Connected' : 'Disconnected'}
                color={isConnected ? 'success' : 'error'}
                size="large"
                sx={{ fontSize: '1.1rem', height: 40 }}
              />
              <Typography variant="body2" color="text.secondary" mt={1}>
                Status: {connectionStatus}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Real-time Events and Command History */}
      <Grid container spacing={3}>
        {/* Real-time Events */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" mb={2}>
                Real-time Events
              </Typography>
              <Paper sx={{ maxHeight: 400, overflow: 'auto' }}>
                <List dense>
                  {realTimeEvents.length === 0 ? (
                    <ListItem>
                      <ListItemText primary="No events yet" secondary="Events will appear here in real-time" />
                    </ListItem>
                  ) : (
                    realTimeEvents.map((event) => (
                      <ListItem key={event.id}>
                        <ListItemIcon>
                          {getEventIcon(event.type)}
                        </ListItemIcon>
                        <ListItemText
                          primary={event.type.replace('_', ' ').toUpperCase()}
                          secondary={`${event.timestamp} - ${JSON.stringify(event.data).substring(0, 100)}...`}
                        />
                      </ListItem>
                    ))
                  )}
                </List>
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Command History */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <History sx={{ mr: 1 }} />
                <Typography variant="h6">Command History</Typography>
              </Box>
              <Paper sx={{ maxHeight: 400, overflow: 'auto' }}>
                <List dense>
                  {commandHistory.length === 0 ? (
                    <ListItem>
                      <ListItemText primary="No commands yet" secondary="Command history will appear here" />
                    </ListItem>
                  ) : (
                    commandHistory.map((cmd) => (
                      <ListItem key={cmd.id}>
                        <ListItemIcon>
                          {cmd.success ? <CheckCircle color="success" /> : <Error color="error" />}
                        </ListItemIcon>
                        <ListItemText
                          primary={cmd.command}
                          secondary={`${cmd.timestamp} - ${cmd.type} ${cmd.executionTime ? `(${cmd.executionTime}ms)` : ''}`}
                        />
                      </ListItem>
                    ))
                  )}
                </List>
              </Paper>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Configuration Dialog */}
      <Dialog open={configDialog} onClose={() => setConfigDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>System Configuration</DialogTitle>
        <DialogContent>
          {config ? (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>Model Paths</Typography>
              <Typography variant="body2">General Models: {config.general_models_path || 'Not set'}</Typography>
              <Typography variant="body2">System Models: {config.system_models_path || 'Not set'}</Typography>
              <Typography variant="body2">Chat Models: {config.chat_models_path || 'Not set'}</Typography>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>Available Commands</Typography>
              {config.model_actions && Object.keys(config.model_actions).length > 0 ? (
                Object.entries(config.model_actions).map(([command, action]) => (
                  <Box key={command} sx={{ mb: 1 }}>
                    <Typography variant="body2" fontWeight="bold">{command}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {action.keypress ? `Keypress: ${action.keypress}` : ''}
                      {action.url ? `URL: ${action.url}` : ''}
                    </Typography>
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">No commands configured</Typography>
              )}
            </Box>
          ) : (
            <CircularProgress />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Command Execution Dialog */}
      <Dialog open={commandDialog} onClose={() => setCommandDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Execute Command</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Command"
              value={newCommand.command}
              onChange={(e) => setNewCommand(prev => ({ ...prev, command: e.target.value }))}
              margin="normal"
              helperText="Enter the command name to execute"
            />
            <TextField
              fullWidth
              label="Parameters (JSON)"
              value={JSON.stringify(newCommand.parameters)}
              onChange={(e) => {
                try {
                  const params = JSON.parse(e.target.value || '{}');
                  setNewCommand(prev => ({ ...prev, parameters: params }));
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              margin="normal"
              multiline
              rows={3}
              helperText="Optional parameters in JSON format"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommandDialog(false)}>Cancel</Button>
          <Button
            onClick={handleExecuteCommand}
            variant="contained"
            disabled={!newCommand.command.trim()}
          >
            Execute
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Dashboard;
