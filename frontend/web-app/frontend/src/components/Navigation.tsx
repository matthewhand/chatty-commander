import React from 'react';
import { List, ListItem, ListItemIcon, ListItemText, Divider, Box } from '@mui/material';
import { Link } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SettingsIcon from '@mui/icons-material/Settings';
import MicIcon from '@mui/icons-material/Mic';
import LogoutIcon from '@mui/icons-material/Logout';
import { useAuth } from '../hooks/useAuth';
import GroupIcon from '@mui/icons-material/Group';

const Navigation: React.FC = () => {
  const { logout } = useAuth();

  return (
    <Box
      sx={{
        width: 240,
        height: '100vh',
        position: 'fixed',
        backgroundColor: 'background.paper',
        borderRight: '1px solid',
        borderColor: 'divider',
      }}
    >
      <List>
        <ListItem button component={Link} to="/dashboard">
          <ListItemIcon><DashboardIcon /></ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>
        <ListItem button component={Link} to="/configuration">
          <ListItemIcon><SettingsIcon /></ListItemIcon>
          <ListItemText primary="Configuration" />
        </ListItem>
        <ListItem button component={Link} to="/audio-settings">
          <ListItemIcon><MicIcon /></ListItemIcon>
          <ListItemText primary="Audio Settings" />
        </ListItem>
        <ListItem button component={Link} to="/personas">
          <ListItemIcon><GroupIcon /></ListItemIcon>
          <ListItemText primary="Personas" />
        </ListItem>
      </List>
      <Divider />
      <List>
        <ListItem button onClick={logout}>
          <ListItemIcon><LogoutIcon /></ListItemIcon>
          <ListItemText primary="Logout" />
        </ListItem>
      </List>
    </Box>
  );
};

export default Navigation;
