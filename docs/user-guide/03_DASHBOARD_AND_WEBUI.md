# Dashboard & Web UI

ChattyCommander includes a rich WebUI built with React and Vite.

## Accessing the Dashboard
By default, the dashboard is served at `http://localhost:8100/` when the application is running.

## Features
- **Real-time Metrics**: View CPU usage, Memory Usage, and total API Commands Executed on the home page.
- **WebSocket Streaming**: All AI generated logs, state transitions, and system errors are streamed directly to the UI.
- **Interactive Command Log**:
  - View real-time command execution history with precise timestamps.
  - Logs are color-coded (Green: Success, Red: Error, Blue: Info) for easy monitoring.
  - Clear the log history with a single click using the "Clear" button.
- **Configuration Hot-Reload**: Update Settings and prompts without needing to restart the backend.

## Screenshots

Screenshots of the UI are stored in [`docs/screenshots/`](../screenshots/).

---

## Documentation Maintenance

### Generating Screenshots

Screenshots are automatically generated using Playwright and committed to the repository.

**Automated Update (GitHub Actions)**: Trigger the [Update Documentation Screenshots](https://github.com/matthewhand/chatty-commander/actions/workflows/screenshots.yml) workflow manually from the Actions tab. It also runs automatically on pushes to `main` when frontend or backend routes change.

**Manual Update (Local)**:

```bash
cd webui/frontend
npm run generate-docs
```

This runs the E2E tests in `tests/e2e/screenshots.spec.ts`, captures each UI page, and saves the images to `docs/screenshots/`.
