# Chatty Commander WebUI - Guided Tour

## Overview

The Chatty Commander WebUI is a modern React-based interface for managing voice commands, agents, and system configuration. It uses React Router for navigation, DaisyUI for styling, and includes real-time WebSocket connectivity.

**Current Status:** WebUI server running at http://localhost:3001

---

## 🗺️ Navigation Structure

### Public Routes
- `/` - Redirects to `/dashboard` (if authenticated) or `/login`
- `/login` - Authentication page

### Protected Routes (Requires Authentication)
- `/dashboard` - Main dashboard and agent cards
- `/configuration` - System settings and configuration
- `/commands` - Command management and execution
- `/commands/authoring` - Create and edit commands

---

## 📄 Page-by-Page Guide

### 1. Login Page (`/login`)

**Purpose:** User authentication and login

**Features:**
- Username/password input fields
- Authentication via backend API
- Redirects to dashboard upon successful login
- Supports "no-auth mode" for development (skip login)

**Access:** http://localhost:3001/login

---

### 2. Dashboard Page (`/dashboard`)

**Purpose:** Main dashboard showing agent cards and system overview

**Features:**
- Agent cards display with status indicators
- Real-time agent status updates via WebSocket
- Quick access to commands and configuration
- Responsive grid layout for agent cards
- Memoized agent cards for performance (recent PR #550)

**Key Components:**
- AgentCard components
- Status indicators (online/offline)
- Action buttons for each agent
- Dashboard statistics

**Access:** http://localhost:3001/dashboard

---

### 3. Commands Page (`/commands`)

**Purpose:** Manage and execute voice commands

**Features:**
- List of all configured commands
- Command execution buttons
- Command details and parameters
- Search/filter functionality
- Accessibility improvements (ARIA labels on modals - PRs #547, #546, #544, #543)

**Key Components:**
- Command list/table
- Execute button with disabled state handling
- Modal dialogs for command details
- Search and filter controls

**Access:** http://localhost:3001/commands

---

### 4. Command Authoring Page (`/commands/authoring`)

**Purpose:** Create and edit custom voice commands

**Features:**
- Command name and description fields
- Action type selection (keypress, shell, HTTP, message)
- Parameter configuration
- Command testing interface
- Save and export functionality

**Key Components:**
- Form inputs for command properties
- Action type selector
- Parameter configuration panel
- Test execution button
- Save/Export controls

**Access:** http://localhost:3001/commands/authoring

---

### 5. Configuration Page (`/configuration`)

**Purpose:** System-wide settings and configuration management

**Features:**
- Backend configuration options
- Voice recognition settings
- Agent configuration
- Theme and display settings
- WebSocket connection settings
- Accessibility options

**Key Components:**
- Configuration sections (collapsible)
- Input fields for various settings
- Save/Apply buttons
- Reset to defaults option
- Theme selector

**Access:** http://localhost:3001/configuration

---

## 🎨 UI Components

### MainLayout
- Navigation sidebar
- Header with user info
- Main content area
- Responsive design (mobile-friendly)

### Navigation
- Dashboard link
- Commands link
- Configuration link
- Logout button
- Breadcrumb navigation

### Modals
- DaisyUI modal components
- ARIA labels for accessibility (PRs #549, #532, #531, #529)
- Backdrop close functionality
- Keyboard (Escape) support

### Forms
- Input validation
- Error handling
- Loading states
- Success feedback

---

## 🔧 Technical Stack

- **Framework:** React 18 with TypeScript
- **Routing:** React Router v6
- **Styling:** DaisyUI + TailwindCSS
- **State Management:** React Query (@tanstack/react-query)
- **Real-time:** WebSocket integration
- **Build Tool:** Vite
- **Testing:** Playwright for E2E, Vitest for unit tests

---

## ♿ Accessibility Features

Recent improvements (from merged PRs):
- ARIA labels on modal backdrops (#547, #546, #544, #543)
- Descriptive labels for dropdowns (#534, #530, #528)
- Tooltip on disabled buttons (#525, #524)
- Vector icons replacing text characters (#527, #518)
- Select element labels (#526)
- WCAG 2.5.3 compliance (#534)

---

## 🚀 Performance Optimizations

Recent improvements (from merged PRs):
- Memoized agent cards (#550, #548)
- Memoized JSX elements (#545, #536)
- Optimized mask_sensitive_data function (#533)
- Route-level code splitting (lazy loading)

---

## 📱 Responsive Design

The WebUI is designed to work across:
- Desktop (1920x1080)
- Laptop (1366x768)
- Tablet (768x1024)
- Mobile (375x812)

---

## 🔌 WebSocket Integration

Real-time features:
- Agent status updates
- Command execution feedback
- System notifications
- Live log streaming

---

## 🎯 How to Navigate

1. **Start the WebUI:**
   ```bash
   cd webui/frontend
   npm run dev
   ```
   Server runs at http://localhost:3001

2. **Access Pages:**
   - Open browser to http://localhost:3001
   - Login (or skip if in no-auth mode)
   - Navigate using sidebar menu

3. **Test Commands:**
   - Go to `/commands`
   - Click execute button on any command
   - View execution status

4. **Configure System:**
   - Go to `/configuration`
   - Modify settings as needed
   - Click Save/Apply

---

## 📸 Screenshots

*Note: Automated screenshot capture requires Playwright Chrome installation. Current Chrome version mismatch (installed 148.0.7778.97, required 131.0.6778.204).*

To capture screenshots manually:
1. Navigate to each page in browser
2. Take screenshots using browser tools
3. Save to `docs/screenshots/` directory

---

## 🔍 Testing

Run E2E tests:
```bash
cd webui/frontend
npm run test:e2e
```

Run unit tests:
```bash
npm run test
```

---

## 📝 Notes

- WebUI requires backend API to be running for full functionality
- WebSocket connection provides real-time updates
- All pages are protected by authentication (except login)
- No-auth mode available for development
- Dark theme enabled by default

---

**Last Updated:** May 30, 2026
**WebUI Version:** 1.0.0
