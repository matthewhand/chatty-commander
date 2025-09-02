import React, { useState, useEffect } from "react";
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  IconButton,
  Tooltip,
  Alert,
  Snackbar,
  Switch,
  FormControlLabel,
} from "@mui/material";
import {
  Brightness4,
  Brightness7,
  GitHub,
  Settings,
  Info,
} from "@mui/icons-material";
import Dashboard from "./components/Dashboard";
import { apiService } from "./services/apiService";

function App() {
  // Theme state
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("chatty-commander-dark-mode");
    return saved ? JSON.parse(saved) : true; // Default to dark mode
  });

  // App state
  const [serverReachable, setServerReachable] = useState(null);
  const [appVersion, setAppVersion] = useState("unknown");
  const [notification, setNotification] = useState({
    open: false,
    message: "",
    severity: "info",
  });

  // Create theme
  const theme = createTheme({
    palette: {
      mode: darkMode ? "dark" : "light",
      primary: {
        main: "#2196f3",
      },
      secondary: {
        main: "#f50057",
      },
      background: {
        default: darkMode ? "#121212" : "#f5f5f5",
        paper: darkMode ? "#1e1e1e" : "#ffffff",
      },
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      h4: {
        fontWeight: 600,
      },
      h6: {
        fontWeight: 500,
      },
    },
    components: {
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            boxShadow: darkMode
              ? "0 4px 6px rgba(0, 0, 0, 0.3)"
              : "0 2px 4px rgba(0, 0, 0, 0.1)",
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            textTransform: "none",
            fontWeight: 500,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 16,
          },
        },
      },
    },
  });

  // Toggle dark mode
  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem("chatty-commander-dark-mode", JSON.stringify(newMode));
  };

  // Show notification
  const showNotification = (message, severity = "info") => {
    setNotification({ open: true, message, severity });
  };

  // Close notification
  const closeNotification = () => {
    setNotification((prev) => ({ ...prev, open: false }));
  };

  // Check server connectivity
  const checkServerConnectivity = async () => {
    try {
      const reachable = await apiService.isServerReachable();
      setServerReachable(reachable);

      if (reachable) {
        const version = await apiService.getVersion();
        setAppVersion(version);
      } else {
        showNotification(
          "Unable to connect to ChattyCommander server",
          "warning",
        );
      }
    } catch (error) {
      console.error("Error checking server connectivity:", error);
      setServerReachable(false);
      showNotification("Server connectivity check failed", "error");
    }
  };

  // Initial server check
  useEffect(() => {
    checkServerConnectivity();

    // Check connectivity every 30 seconds
    const interval = setInterval(checkServerConnectivity, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle server connectivity changes
  useEffect(() => {
    if (serverReachable === false) {
      showNotification(
        "Lost connection to ChattyCommander server. Please check if the server is running.",
        "error",
      );
    } else if (serverReachable === true) {
      // Only show success message if we previously had connection issues
      const wasDisconnected = localStorage.getItem(
        "chatty-commander-was-disconnected",
      );
      if (wasDisconnected) {
        showNotification(
          "Successfully connected to ChattyCommander server",
          "success",
        );
        localStorage.removeItem("chatty-commander-was-disconnected");
      }
    }

    // Store disconnection state
    if (serverReachable === false) {
      localStorage.setItem("chatty-commander-was-disconnected", "true");
    }
  }, [serverReachable]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: "100vh" }}>
        {/* App Bar */}
        <AppBar
          position="static"
          elevation={0}
          sx={{
            backgroundColor: theme.palette.background.paper,
            borderBottom: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Toolbar>
            <Typography
              variant="h6"
              component="div"
              sx={{
                flexGrow: 1,
                color: theme.palette.text.primary,
                fontWeight: 600,
              }}
            >
              ChattyCommander Web UI
            </Typography>

            {/* Server Status Indicator */}
            <Box sx={{ display: "flex", alignItems: "center", mr: 2 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor:
                    serverReachable === null
                      ? theme.palette.warning.main
                      : serverReachable
                        ? theme.palette.success.main
                        : theme.palette.error.main,
                  mr: 1,
                }}
              />
              <Typography variant="body2" color="text.secondary">
                {serverReachable === null
                  ? "Checking..."
                  : serverReachable
                    ? `Connected (v${appVersion})`
                    : "Disconnected"}
              </Typography>
            </Box>

            {/* Dark Mode Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={darkMode}
                  onChange={toggleDarkMode}
                  size="small"
                />
              }
              label={darkMode ? "Dark" : "Light"}
              sx={{ mr: 1 }}
            />

            <Tooltip title={`Switch to ${darkMode ? "light" : "dark"} mode`}>
              <IconButton
                onClick={toggleDarkMode}
                color="inherit"
                sx={{ color: theme.palette.text.primary }}
              >
                {darkMode ? <Brightness7 /> : <Brightness4 />}
              </IconButton>
            </Tooltip>

            <Tooltip title="Settings">
              <IconButton
                color="inherit"
                sx={{ color: theme.palette.text.primary }}
                onClick={() =>
                  showNotification("Settings panel coming soon!", "info")
                }
              >
                <Settings />
              </IconButton>
            </Tooltip>

            <Tooltip title="About">
              <IconButton
                color="inherit"
                sx={{ color: theme.palette.text.primary }}
                onClick={() =>
                  showNotification(
                    `ChattyCommander Web UI v${appVersion}`,
                    "info",
                  )
                }
              >
                <Info />
              </IconButton>
            </Tooltip>

            <Tooltip title="View on GitHub">
              <IconButton
                color="inherit"
                component="a"
                href="https://github.com/your-username/chatty-commander"
                target="_blank"
                rel="noopener noreferrer"
                sx={{ color: theme.palette.text.primary }}
              >
                <GitHub />
              </IconButton>
            </Tooltip>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Container maxWidth="xl" sx={{ mt: 0, pb: 4 }}>
          {serverReachable === false ? (
            <Box sx={{ mt: 4 }}>
              <Alert
                severity="error"
                sx={{ mb: 2 }}
                action={
                  <IconButton
                    color="inherit"
                    size="small"
                    onClick={checkServerConnectivity}
                  >
                    <Tooltip title="Retry connection">
                      <Settings />
                    </Tooltip>
                  </IconButton>
                }
              >
                <Typography variant="h6" gutterBottom>
                  Unable to connect to ChattyCommander server
                </Typography>
                <Typography variant="body2">
                  Please ensure the ChattyCommander server is running on the
                  expected port (default: 8100). You can start the server by
                  running: <code>python main.py --web</code>
                </Typography>
              </Alert>
            </Box>
          ) : (
            <Dashboard />
          )}
        </Container>

        {/* Notification Snackbar */}
        <Snackbar
          open={notification.open}
          autoHideDuration={6000}
          onClose={closeNotification}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        >
          <Alert
            onClose={closeNotification}
            severity={notification.severity}
            variant="filled"
            sx={{ width: "100%" }}
          >
            {notification.message}
          </Alert>
        </Snackbar>
      </Box>
    </ThemeProvider>
  );
}

export default App;
