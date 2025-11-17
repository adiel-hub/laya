/**
 * Main Dashboard Page
 */

import { useState, useEffect } from 'react';
import { analyticsApi } from '../services/analyticsApi';
import { callsApi } from '../services/callsApi';

const Dashboard = ({ activeCalls = [] }) => {
  const [analytics, setAnalytics] = useState(null);
  const [recentCalls, setRecentCalls] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [analyticsData, callsData] = await Promise.all([
        analyticsApi.getSummary(),
        callsApi.getCalls({ limit: 10 }),
      ]);
      setAnalytics(analyticsData);
      setRecentCalls(callsData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">טוען נתונים...</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">לוח בקרה</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="card">
          <div className="text-sm text-gray-600">סה"כ שיחות</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            {analytics?.total_calls || 0}
          </div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600">שיחות שהושלמו</div>
          <div className="text-3xl font-bold text-green-600 mt-2">
            {analytics?.completed_calls || 0}
          </div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600">ממוצע CX Score</div>
          <div className="text-3xl font-bold text-primary-600 mt-2">
            {analytics?.avg_cx_score?.toFixed(1) || '0.0'}
          </div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600">ממוצע משך שיחה</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            {Math.round(analytics?.avg_duration_seconds / 60) || 0} דק'
          </div>
        </div>
      </div>

      {/* Active Calls */}
      {activeCalls.length > 0 && (
        <div className="card mb-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">
            🔴 שיחות פעילות ({activeCalls.length})
          </h2>
          <div className="space-y-2">
            {activeCalls.map((call) => (
              <div
                key={call.call_id}
                className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg"
              >
                <div>
                  <div className="font-medium">{call.lead_name}</div>
                  <div className="text-sm text-gray-600">
                    {call.lead_type === 'drop-off' ? 'נפל בהרשמה' : 'לא פעיל'}
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {call.timestamp && new Date(call.timestamp).toLocaleTimeString('he-IL')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Calls */}
      <div className="card">
        <h2 className="text-lg font-bold text-gray-900 mb-4">
          📜 שיחות אחרונות
        </h2>
        <div className="space-y-2">
          {recentCalls.length === 0 ? (
            <p className="text-gray-500 text-center py-4">אין שיחות עדיין</p>
          ) : (
            recentCalls.map((call) => (
              <div
                key={call.call_id}
                className="flex justify-between items-center p-3 hover:bg-gray-50 rounded-lg"
              >
                <div>
                  <div className="font-medium">Call ID: {call.call_id.substring(0, 8)}...</div>
                  <div className="text-sm text-gray-600">
                    Status: {call.status}
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {call.started_at && new Date(call.started_at).toLocaleString('he-IL')}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
