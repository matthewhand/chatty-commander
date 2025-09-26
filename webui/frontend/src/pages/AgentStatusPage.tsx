import React from "react";
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Paper,
  Chip,
  Alert,
  CircularProgress,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { fetchAgentStatus, Agent } from "../services/api";

const AgentStatusPage: React.FC = () => {
  const { data, isLoading, isError, error } = useQuery<Agent[]>({
    queryKey: ["agentStatus"],
    queryFn: fetchAgentStatus,
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 2,
  });

  const getStatusColor = (status: Agent["status"]) => {
    switch (status) {
      case "online":
        return "success";
      case "offline":
        return "default";
      case "error":
        return "error";
      case "processing":
        return "warning";
      default:
        return "default";
    }
  };

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="50vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Agent Status
      </Typography>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error.message ||
            "Failed to fetch agent status. Please try again later."}
        </Alert>
      )}

      <Grid container spacing={3}>
        {data?.map((agent) => (
          <Grid item xs={12} sm={6} md={4} key={agent.id}>
            <Card>
              <CardContent>
                <Box
                  display="flex"
                  justifyContent="space-between"
                  alignItems="center"
                  mb={2}
                >
                  <Typography variant="h6">{agent.name}</Typography>
                  <Chip
                    label={agent.status.toUpperCase()}
                    color={getStatusColor(agent.status)}
                    size="small"
                  />
                </Box>

                {agent.error && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {agent.error}
                  </Alert>
                )}

                <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Last Message Sent:</strong> {agent.lastMessageSent}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Last Message Received:</strong>{" "}
                    {agent.lastMessageReceived}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Message Content:</strong> {agent.lastMessageContent}
                  </Typography>
                </Paper>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default AgentStatusPage;
