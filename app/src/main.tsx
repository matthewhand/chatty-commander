import React from 'react';
import ReactDOM from 'react-dom/client';
import { initTelemetry, recordHydration } from './lib/telemetry';
import TopBar from './app-shell/TopBar';
import GridLayout from './app-shell/Grid';
import ChatPane from './panes/ChatPane';
import CanvasPane from './panes/CanvasPane';
import SidecarPane from './panes/SidecarPane';
import './styles/index.css';

function App() {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100">
      <TopBar />
      <GridLayout>
        <ChatPane />
        <CanvasPane />
        <SidecarPane />
      </GridLayout>
    </div>
  );
}

initTelemetry();
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
recordHydration();
