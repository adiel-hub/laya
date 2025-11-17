/**
 * Main App Component
 */

import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useWebSocket } from './hooks/useWebSocket';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import LeadsPage from './pages/LeadsPage';

function App() {
  const [activeCalls, setActiveCalls] = useState([]);
  const [recentResults, setRecentResults] = useState([]);

  // Handle WebSocket messages
  const handleWebSocketMessage = (message) => {
    console.log('WebSocket message received:', message);

    if (message.type === 'call_started') {
      // Add to active calls
      setActiveCalls(prev => [...prev, {
        call_id: message.call_id,
        lead_id: message.lead_id,
        lead_name: message.lead_name,
        timestamp: message.timestamp,
      }]);
    } else if (message.type === 'call_ended') {
      // Remove from active calls
      setActiveCalls(prev => prev.filter(call => call.call_id !== message.call_id));
    } else if (message.type === 'call_result') {
      // Add to recent results
      setRecentResults(prev => [{
        call_id: message.call_id,
        disposition: message.disposition,
        cx_score: message.cx_score,
        summary: message.summary,
        timestamp: new Date().toISOString(),
      }, ...prev].slice(0, 10)); // Keep last 10

      // Show notification
      if (Notification.permission === 'granted') {
        new Notification('שיחה הסתיימה', {
          body: `Disposition: ${message.disposition}, CX: ${message.cx_score}/10`,
        });
      }
    }
  };

  // Request notification permission on load
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const { isConnected } = useWebSocket(handleWebSocketMessage);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout isWsConnected={isConnected} />}>
          <Route index element={<Dashboard activeCalls={activeCalls} />} />
          <Route path="leads" element={<LeadsPage />} />
          <Route path="calls" element={<div className="card"><h1 className="text-xl font-bold">Call History (Coming Soon)</h1></div>} />
          <Route path="analytics" element={<div className="card"><h1 className="text-xl font-bold">Analytics (Coming Soon)</h1></div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
