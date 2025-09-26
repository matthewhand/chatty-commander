import React from "react";
import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Badge,
  Chip,
} from "@mui/material";
import { Link } from "react-router-dom";
import DashboardIcon from "@mui/icons-material/Dashboard";
import SettingsIcon from "@mui/icons-material/Settings";
import MicIcon from "@mui/icons-material/Mic";
import LogoutIcon from "@mui/icons-material/Logout";
import { useAuth } from "../hooks/useAuth";
import GroupIcon from "@mui/icons-material/Group";
import AssessmentIcon from "@mui/icons-material/Assessment";
import ErrorIcon from "@mui/icons-material/Error";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";

const Navigation: React.FC = () => {
  const { logout } = useAuth();
  // Mock system health status - in real app this would come from API
  const systemHealthy = true; // This could be fetched from an API endpoint
  const hasErrors = false; // This could be fetched from an API endpoint

  return (
    <Box
      sx={{
        width: 240,
        height: "100vh",
        position: "fixed",
        backgroundColor: "background.paper",
        borderRight: "1px solid",
        borderColor: "divider",
      }}
    >
      <List>
        <ListItem button component={Link} to="/dashboard">
          <ListItemIcon>
            <DashboardIcon />
          </ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>
        <ListItem button component={Link} to="/configuration">
          <ListItemIcon>
            <SettingsIcon />
          </ListItemIcon>
          <ListItemText primary="Configuration" />
        </ListItem>
        <ListItem button component={Link} to="/audio-settings">
          <ListItemIcon>
            <MicIcon />
          </ListItemIcon>
          <ListItemText primary="Audio Settings" />
        </ListItem>
        <ListItem button component={Link} to="/personas">
          <ListItemIcon>
            <GroupIcon />
          </ListItemIcon>
          <ListItemText primary="Personas" />
        </ListItem>
        <ListItem button component={Link} to="/agent-status">
          <ListItemIcon>
            <Badge
              color={hasErrors ? "error" : "success"}
              variant="dot"
              invisible={!hasErrors && !systemHealthy}
            >
              <AssessmentIcon />
            </Badge>
          </ListItemIcon>
          <ListItemText
            primary="Agent Status"
            secondary={
              <Box
                sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}
              >
                <Chip
                  size="small"
                  icon={systemHealthy ? <CheckCircleIcon /> : <ErrorIcon />}
                  label={systemHealthy ? "Healthy" : "Issues"}
                  color={systemHealthy ? "success" : "error"}
                  variant="outlined"
                />
              </Box>
            }
          />
        </ListItem>
      </List>
      <Divider />
      <List>
        <ListItem button onClick={logout}>
          <ListItemIcon>
            <LogoutIcon />
          </ListItemIcon>
          <ListItemText primary="Logout" />
        </ListItem>
      </List>
    </Box>
  );
};

export default Navigation;
