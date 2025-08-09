# ChattyCommander WebUI Test Plan

## Overview
This document outlines a comprehensive testing strategy for the ChattyCommander WebUI, covering backend API testing, frontend component testing, end-to-end workflows, performance validation, and user demonstration scenarios.

## Testing Phases

### Phase 1: Backend API Testing

#### 1.1 Authentication Testing
```python
# tests/backend/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAuthentication:
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/config")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_valid_token(self):
        """Test accessing protected endpoint with valid token"""
        # Login first
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = client.get("/api/v1/config", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
    
    def test_token_refresh(self):
        """Test JWT token refresh functionality"""
        # Login and get token
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        
        # Refresh token
        response = client.post("/api/v1/auth/refresh", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
```

#### 1.2 Configuration API Testing
```python
# tests/backend/test_config.py
class TestConfiguration:
    def test_get_config(self, authenticated_client):
        """Test retrieving complete configuration"""
        response = authenticated_client.get("/api/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert "model_actions" in data
        assert "state_models" in data
        assert "audio_settings" in data
    
    def test_update_config(self, authenticated_client):
        """Test updating configuration"""
        config_data = {
            "model_actions": {
                "test_command": {"keypress": "ctrl+t"}
            },
            "general_settings": {
                "debug_mode": True
            }
        }
        response = authenticated_client.put("/api/v1/config", json=config_data)
        assert response.status_code == 200
    
    def test_get_commands(self, authenticated_client):
        """Test retrieving all commands"""
        response = authenticated_client.get("/api/v1/config/commands")
        assert response.status_code == 200
        data = response.json()
        assert "commands" in data
        assert "total" in data
    
    def test_create_command(self, authenticated_client):
        """Test creating a new command"""
        command_data = {
            "name": "test_new_command",
            "action": {"keypress": "ctrl+shift+n"},
            "description": "Test command for automation"
        }
        response = authenticated_client.post("/api/v1/config/commands", json=command_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test_new_command"
    
    def test_update_command(self, authenticated_client):
        """Test updating an existing command"""
        command_data = {
            "name": "updated_command",
            "action": {"url": "http://localhost:3000/updated"},
            "description": "Updated test command"
        }
        response = authenticated_client.put("/api/v1/config/commands/test_command", json=command_data)
        assert response.status_code == 200
    
    def test_delete_command(self, authenticated_client):
        """Test deleting a command"""
        response = authenticated_client.delete("/api/v1/config/commands/test_command")
        assert response.status_code == 204
```

#### 1.3 Service Control Testing
```python
# tests/backend/test_service.py
class TestServiceControl:
    def test_get_service_status(self, authenticated_client):
        """Test retrieving service status"""
        response = authenticated_client.get("/api/v1/service/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "current_state" in data
        assert "loaded_models" in data
    
    def test_start_service(self, authenticated_client):
        """Test starting the voice service"""
        response = authenticated_client.post("/api/v1/service/start", json={
            "debug_mode": True
        })
        assert response.status_code in [200, 409]  # 409 if already running
    
    def test_stop_service(self, authenticated_client):
        """Test stopping the voice service"""
        response = authenticated_client.post("/api/v1/service/stop")
        assert response.status_code in [200, 404]  # 404 if not running
    
    def test_restart_service(self, authenticated_client):
        """Test restarting the voice service"""
        response = authenticated_client.post("/api/v1/service/restart")
        assert response.status_code == 200
```

#### 1.4 WebSocket Testing
```python
# tests/backend/test_websocket.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import WebSocket

class TestWebSocket:
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        with TestClient(app) as client:
            with client.websocket_connect("/ws/status") as websocket:
                # Test connection is established
                assert websocket is not None
    
    @pytest.mark.asyncio
    async def test_websocket_service_status_updates(self):
        """Test receiving service status updates via WebSocket"""
        with TestClient(app) as client:
            with client.websocket_connect("/ws/status") as websocket:
                # Trigger a service status change
                client.post("/api/v1/service/start")
                
                # Wait for WebSocket message
                data = websocket.receive_json()
                assert data["type"] == "service_status"
                assert "running" in data["payload"]
    
    @pytest.mark.asyncio
    async def test_websocket_audio_level_updates(self):
        """Test receiving audio level updates via WebSocket"""
        with TestClient(app) as client:
            with client.websocket_connect("/ws/status") as websocket:
                # Wait for audio level message
                data = websocket.receive_json()
                assert data["type"] == "audio_level"
                assert "level" in data["payload"]
                assert 0 <= data["payload"]["level"] <= 1
```

### Phase 2: Frontend Component Testing

#### 2.1 Authentication Components
```typescript
// tests/frontend/components/LoginForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LoginForm from '../../../src/components/auth/LoginForm';
import { AuthProvider } from '../../../src/components/auth/AuthProvider';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
};

describe('LoginForm', () => {
  test('renders login form elements', () => {
    render(<LoginForm />, { wrapper: createWrapper() });
    
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });
  
  test('shows validation errors for empty fields', async () => {
    render(<LoginForm />, { wrapper: createWrapper() });
    
    const loginButton = screen.getByRole('button', { name: /login/i });
    fireEvent.click(loginButton);
    
    await waitFor(() => {
      expect(screen.getByText(/username is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });
  
  test('submits form with valid credentials', async () => {
    const mockLogin = jest.fn();
    render(<LoginForm onLogin={mockLogin} />, { wrapper: createWrapper() });
    
    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'admin' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' },
    });
    
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'admin',
        password: 'password123',
      });
    });
  });
});
```

#### 2.2 Configuration Components
```typescript
// tests/frontend/components/ConfigManager.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ConfigManager from '../../../src/components/config/ConfigManager';
import { mockConfig } from '../../mocks/config';

describe('ConfigManager', () => {
  test('displays configuration sections', () => {
    render(<ConfigManager config={mockConfig} />);
    
    expect(screen.getByText(/commands/i)).toBeInTheDocument();
    expect(screen.getByText(/states/i)).toBeInTheDocument();
    expect(screen.getByText(/audio settings/i)).toBeInTheDocument();
  });
  
  test('allows editing command actions', async () => {
    const mockUpdateConfig = jest.fn();
    render(<ConfigManager config={mockConfig} onUpdate={mockUpdateConfig} />);
    
    // Click edit button for a command
    const editButton = screen.getByTestId('edit-command-take_screenshot');
    fireEvent.click(editButton);
    
    // Modify the keypress
    const keypressInput = screen.getByDisplayValue('alt+print_screen');
    fireEvent.change(keypressInput, { target: { value: 'ctrl+shift+s' } });
    
    // Save changes
    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockUpdateConfig).toHaveBeenCalledWith({
        ...mockConfig,
        model_actions: {
          ...mockConfig.model_actions,
          take_screenshot: { keypress: 'ctrl+shift+s' },
        },
      });
    });
  });
});
```

#### 2.3 Service Control Components
```typescript
// tests/frontend/components/ServiceControl.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ServiceControl from '../../../src/components/service/ServiceControl';
import { mockServiceStatus } from '../../mocks/service';

describe('ServiceControl', () => {
  test('displays service status', () => {
    render(<ServiceControl status={mockServiceStatus} />);
    
    expect(screen.getByText(/running/i)).toBeInTheDocument();
    expect(screen.getByText(/idle/i)).toBeInTheDocument();
    expect(screen.getByText(/uptime/i)).toBeInTheDocument();
  });
  
  test('allows starting stopped service', async () => {
    const mockStartService = jest.fn();
    const stoppedStatus = { ...mockServiceStatus, running: false };
    
    render(<ServiceControl status={stoppedStatus} onStart={mockStartService} />);
    
    const startButton = screen.getByRole('button', { name: /start/i });
    fireEvent.click(startButton);
    
    await waitFor(() => {
      expect(mockStartService).toHaveBeenCalled();
    });
  });
  
  test('allows stopping running service', async () => {
    const mockStopService = jest.fn();
    
    render(<ServiceControl status={mockServiceStatus} onStop={mockStopService} />);
    
    const stopButton = screen.getByRole('button', { name: /stop/i });
    fireEvent.click(stopButton);
    
    await waitFor(() => {
      expect(mockStopService).toHaveBeenCalled();
    });
  });
});
```

### Phase 3: End-to-End Testing

#### 3.1 Authentication Flow
```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('complete login flow', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Fill login form
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'password123');
    
    // Submit form
    await page.click('[data-testid="login-button"]');
    
    // Verify redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });
  
  test('invalid credentials show error', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');
    await page.click('[data-testid="login-button"]');
    
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
  });
  
  test('logout functionality', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    
    // Logout
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');
    
    // Verify redirect to login
    await expect(page).toHaveURL('/login');
  });
});
```

#### 3.2 Configuration Management Flow
```typescript
// tests/e2e/config.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Configuration Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
  });
  
  test('create new command', async ({ page }) => {
    await page.goto('/config');
    
    // Click add command button
    await page.click('[data-testid="add-command-button"]');
    
    // Fill command form
    await page.fill('[data-testid="command-name-input"]', 'test_e2e_command');
    await page.selectOption('[data-testid="action-type-select"]', 'keypress');
    await page.fill('[data-testid="keypress-input"]', 'ctrl+e');
    await page.fill('[data-testid="description-input"]', 'E2E test command');
    
    // Save command
    await page.click('[data-testid="save-command-button"]');
    
    // Verify command appears in list
    await expect(page.locator('[data-testid="command-test_e2e_command"]')).toBeVisible();
  });
  
  test('edit existing command', async ({ page }) => {
    await page.goto('/config');
    
    // Click edit button for existing command
    await page.click('[data-testid="edit-command-take_screenshot"]');
    
    // Modify keypress
    await page.fill('[data-testid="keypress-input"]', 'ctrl+shift+s');
    
    // Save changes
    await page.click('[data-testid="save-command-button"]');
    
    // Verify changes are saved
    await expect(page.locator('[data-testid="command-take_screenshot"]')).toContainText('ctrl+shift+s');
  });
  
  test('delete command', async ({ page }) => {
    await page.goto('/config');
    
    // Click delete button
    await page.click('[data-testid="delete-command-test_e2e_command"]');
    
    // Confirm deletion
    await page.click('[data-testid="confirm-delete-button"]');
    
    // Verify command is removed
    await expect(page.locator('[data-testid="command-test_e2e_command"]')).not.toBeVisible();
  });
});
```

#### 3.3 Service Control Flow
```typescript
// tests/e2e/service.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Service Control', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
  });
  
  test('start and stop service', async ({ page }) => {
    await page.goto('/service');
    
    // Stop service if running
    const stopButton = page.locator('[data-testid="stop-service-button"]');
    if (await stopButton.isVisible()) {
      await stopButton.click();
      await expect(page.locator('[data-testid="service-status"]')).toContainText('Stopped');
    }
    
    // Start service
    await page.click('[data-testid="start-service-button"]');
    await expect(page.locator('[data-testid="service-status"]')).toContainText('Running');
    
    // Stop service
    await page.click('[data-testid="stop-service-button"]');
    await expect(page.locator('[data-testid="service-status"]')).toContainText('Stopped');
  });
  
  test('restart service', async ({ page }) => {
    await page.goto('/service');
    
    // Restart service
    await page.click('[data-testid="restart-service-button"]');
    
    // Verify service is running after restart
    await expect(page.locator('[data-testid="service-status"]')).toContainText('Running');
  });
});
```

### Phase 4: Performance Testing

#### 4.1 API Load Testing
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import json

class ChattyCommanderUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get auth token"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def get_config(self):
        """Test config retrieval performance"""
        self.client.get("/api/v1/config", headers=self.headers)
    
    @task(2)
    def get_service_status(self):
        """Test service status performance"""
        self.client.get("/api/v1/service/status", headers=self.headers)
    
    @task(1)
    def get_commands(self):
        """Test commands listing performance"""
        self.client.get("/api/v1/config/commands", headers=self.headers)
    
    @task(1)
    def create_command(self):
        """Test command creation performance"""
        command_data = {
            "name": f"perf_test_command_{self.environment.runner.user_count}",
            "action": {"keypress": "ctrl+p"},
            "description": "Performance test command"
        }
        self.client.post("/api/v1/config/commands", 
                        json=command_data, headers=self.headers)
```

#### 4.2 Frontend Performance Testing
```typescript
// tests/performance/lighthouse.config.js
module.exports = {
  extends: 'lighthouse:default',
  settings: {
    formFactor: 'desktop',
    throttling: {
      rttMs: 40,
      throughputKbps: 10240,
      cpuSlowdownMultiplier: 1,
      requestLatencyMs: 0,
      downloadThroughputKbps: 0,
      uploadThroughputKbps: 0,
    },
    screenEmulation: {
      mobile: false,
      width: 1350,
      height: 940,
      deviceScaleFactor: 1,
      disabled: false,
    },
    emulatedUserAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36',
  },
  audits: [
    'first-contentful-paint',
    'largest-contentful-paint',
    'first-meaningful-paint',
    'speed-index',
    'interactive',
    'total-blocking-time',
    'cumulative-layout-shift',
  ],
};
```

### Phase 5: User Demonstration Scenarios

#### 5.1 Interactive Demo Script
```markdown
# ChattyCommander WebUI Demo Script

## Demo Environment Setup
1. **Backend Service**: Running on http://localhost:8000
2. **Frontend Application**: Running on http://localhost:3000
3. **Test Data**: Pre-configured with sample commands and states
4. **Audio Setup**: Microphone connected for voice testing

## Demo Flow (15 minutes)

### 1. Authentication & Dashboard (2 minutes)
- **Action**: Navigate to http://localhost:3000
- **Show**: Login form with clean, modern UI
- **Action**: Login with demo credentials
- **Show**: Dashboard with service status, quick actions, system metrics
- **Highlight**: Real-time status updates, responsive design

### 2. Configuration Management (5 minutes)
- **Action**: Navigate to Configuration section
- **Show**: Commands list with search and filtering
- **Action**: Create new voice command
  - Name: "open_calculator"
  - Action: keypress "ctrl+alt+c"
  - Description: "Open system calculator"
- **Show**: Real-time validation, intuitive form design
- **Action**: Edit existing command (change keypress)
- **Show**: Inline editing capabilities
- **Action**: Test command execution
- **Show**: Command testing with feedback

### 3. Service Control & Monitoring (3 minutes)
- **Action**: Navigate to Service Control
- **Show**: Current service status, loaded models, resource usage
- **Action**: Stop service
- **Show**: Real-time status updates via WebSocket
- **Action**: Start service with debug mode
- **Show**: Live log streaming, process monitoring
- **Action**: View system metrics
- **Show**: CPU, memory, disk usage charts

### 4. Audio & Voice Testing (3 minutes)
- **Action**: Navigate to Audio Settings
- **Show**: Device selection, audio level meter
- **Action**: Adjust microphone settings
- **Show**: Real-time audio level visualization
- **Action**: Test voice recognition
  - Upload audio file
  - Live microphone test
- **Show**: Recognition results, confidence scores, processing time

### 5. Real-time Features (2 minutes)
- **Action**: Open multiple browser tabs
- **Show**: Synchronized updates across sessions
- **Action**: Trigger voice command
- **Show**: Real-time command recognition notifications
- **Action**: Monitor audio levels
- **Show**: Live audio visualization
```

#### 5.2 Video Demo Scenarios
```markdown
# Video Demo Production Plan

## Video 1: "Quick Start Guide" (3 minutes)
- **Scene 1**: Login and dashboard overview
- **Scene 2**: Basic configuration setup
- **Scene 3**: Service start and voice command test
- **Target**: New users, basic functionality

## Video 2: "Advanced Configuration" (5 minutes)
- **Scene 1**: Complex command creation (URL actions, system commands)
- **Scene 2**: State management and model assignment
- **Scene 3**: Bulk import/export of configurations
- **Target**: Power users, advanced features

## Video 3: "Real-time Monitoring" (4 minutes)
- **Scene 1**: Service monitoring and log analysis
- **Scene 2**: Performance metrics and troubleshooting
- **Scene 3**: Multi-user collaboration features
- **Target**: System administrators, monitoring

## Video 4: "Mobile Experience" (2 minutes)
- **Scene 1**: Responsive design on tablet
- **Scene 2**: Mobile phone interface
- **Scene 3**: Touch-optimized controls
- **Target**: Mobile users, accessibility
```

#### 5.3 Performance Metrics Dashboard
```typescript
// Demo performance metrics to showcase
interface PerformanceMetrics {
  api: {
    averageResponseTime: number; // < 200ms
    throughput: number; // requests/second
    errorRate: number; // < 1%
    uptime: number; // 99.9%
  };
  frontend: {
    loadTime: number; // < 3s
    firstContentfulPaint: number; // < 1.5s
    largestContentfulPaint: number; // < 2.5s
    cumulativeLayoutShift: number; // < 0.1
  };
  websocket: {
    connectionTime: number; // < 100ms
    messageLatency: number; // < 50ms
    reconnectionRate: number; // < 0.1%
  };
  system: {
    memoryUsage: number; // MB
    cpuUsage: number; // %
    diskUsage: number; // GB
    activeConnections: number;
  };
}

// Example metrics for demo
const demoMetrics: PerformanceMetrics = {
  api: {
    averageResponseTime: 145,
    throughput: 1250,
    errorRate: 0.2,
    uptime: 99.95
  },
  frontend: {
    loadTime: 2.1,
    firstContentfulPaint: 1.2,
    largestContentfulPaint: 2.0,
    cumulativeLayoutShift: 0.05
  },
  websocket: {
    connectionTime: 85,
    messageLatency: 35,
    reconnectionRate: 0.05
  },
  system: {
    memoryUsage: 256,
    cpuUsage: 12.5,
    diskUsage: 1.2,
    activeConnections: 15
  }
};
```

## Test Automation Strategy

### Continuous Integration Pipeline
```yaml
# .github/workflows/webui-tests.yml
name: WebUI Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd webui/backend
          pip install -r requirements.txt
          pip install pytest-cov
      - name: Run tests
        run: |
          cd webui/backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd webui/frontend
          npm ci
      - name: Run tests
        run: |
          cd webui/frontend
          npm run test:coverage
      - name: Run build
        run: |
          cd webui/frontend
          npm run build

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install Playwright
        run: |
          cd webui
          npm ci
          npx playwright install
      - name: Start services
        run: |
          cd webui
          docker-compose up -d
          sleep 30
      - name: Run E2E tests
        run: |
          cd webui
          npx playwright test
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-report
          path: webui/playwright-report/
```

## Success Criteria

### Functional Testing
- [ ] 100% API endpoint coverage
- [ ] All user workflows tested
- [ ] Cross-browser compatibility verified
- [ ] Mobile responsiveness confirmed
- [ ] Accessibility standards met (WCAG 2.1 AA)

### Performance Testing
- [ ] API response time < 200ms (95th percentile)
- [ ] Frontend load time < 3 seconds
- [ ] WebSocket latency < 50ms
- [ ] Support for 100+ concurrent users
- [ ] Memory usage < 512MB per instance

### Security Testing
- [ ] Authentication bypass attempts blocked
- [ ] SQL injection prevention verified
- [ ] XSS protection confirmed
- [ ] CSRF protection implemented
- [ ] Rate limiting functional

### User Experience
- [ ] Intuitive navigation (< 3 clicks to any feature)
- [ ] Clear error messages and feedback
- [ ] Consistent UI/UX across all pages
- [ ] Offline capability for cached data
- [ ] Real-time updates working reliably

This comprehensive test plan ensures the ChattyCommander WebUI meets production quality standards while providing an excellent user experience that matches or exceeds the desktop GUI functionality.