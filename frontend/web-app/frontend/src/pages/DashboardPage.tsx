import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Paper,
  Container,
} from "@mui/material";
import { useWebSocket } from "../components/WebSocketProvider";
import { useQuery } from "@tanstack/react-query";
import { Dns, Timer, Terminal, Wifi, WifiOff } from "@mui/icons-material";

const DashboardPage: React.FC = () => {
  const { ws, isConnected } = useWebSocket();
  const [messages, setMessages] = useState<string[]>([]);

  const { data: systemStatus, isLoading } = useQuery({
    queryKey: ["systemStatus"],
    queryFn: async () => {
      // Placeholder for fetching system status
      return { status: "Online", uptime: "2 hours", commandsExecuted: 45 };
    },
  });

  useEffect(() => {
    if (ws) {
      ws.onmessage = (event) => {
        setMessages((prev) => [...prev, event.data]);
      };
    }
  }, [ws]);

  const StatCard = ({
    title,
    value,
    icon,
  }: {
    title: string;
    value: string | number;
    icon: React.ReactNode;
  }) => (
    <Grid item xs={12} sm={6} md={3}>
      <Paper
        elevation={3}
        sx={{ p: 2, display: "flex", alignItems: "center", borderRadius: 2 }}
      >
        {icon}
        <Box sx={{ ml: 2 }}>
          <Typography variant="h6">{value}</Typography>
          <Typography color="text.secondary">{title}</Typography>
        </Box>
      </Paper>
    </Grid>
  );

  if (isLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        flexGrow: 1,
        p: 3,
        background: "linear-gradient(to right bottom, #2e3a4d, #1a202c)",
        minHeight: "calc(100vh - 64px)",
      }}
    >
      <Container maxWidth="lg">
        <Typography variant="h4" gutterBottom sx={{ color: "white", mb: 4 }}>
          Dashboard
        </Typography>
        <Grid container spacing={3}>
          <StatCard
            title="Status"
            value={systemStatus?.status || "Unknown"}
            icon={<Dns sx={{ fontSize: 40, color: "primary.main" }} />}
          />
          <StatCard
            title="Uptime"
            value={systemStatus?.uptime || "N/A"}
            icon={<Timer sx={{ fontSize: 40, color: "primary.main" }} />}
          />
          <StatCard
            title="Commands Executed"
            value={systemStatus?.commandsExecuted || 0}
            icon={<Terminal sx={{ fontSize: 40, color: "primary.main" }} />}
          />
          <StatCard
            title="WebSocket"
            value={isConnected ? "Connected" : "Disconnected"}
            icon={
              isConnected ? (
                <Wifi sx={{ fontSize: 40, color: "green" }} />
              ) : (
                <WifiOff sx={{ fontSize: 40, color: "red" }} />
              )
            }
          />
        </Grid>
        <Grid container spacing={3} sx={{ mt: 4 }}>
          <Grid item xs={12}>
            <Card sx={{ borderRadius: 2 }}>
              <CardContent>
                <Typography variant="h6">Real-time Command Log</Typography>
                <Paper
                  variant="outlined"
                  sx={{
                    mt: 2,
                    p: 2,
                    height: 300,
                    overflowY: "auto",
                    backgroundColor: "#1a202c",
                    color: "white",
                  }}
                >
                  <List>
                    {messages.length > 0 ? (
                      messages.slice(-10).map((msg, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={`> ${msg}`} />
                        </ListItem>
                      ))
                    ) : (
                      <Typography sx={{ p: 2, color: "text.secondary" }}>
                        No commands received yet...
                      </Typography>
                    )}
                  </List>
                </Paper>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default DashboardPage;
