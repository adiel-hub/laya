/**
 * Calls API Service
 */

import apiClient from './api';

export const callsApi = {
  // Get all calls
  getCalls: async (params = {}) => {
    const response = await apiClient.get('/api/calls', { params });
    return response.data;
  },

  // Get single call
  getCall: async (callId) => {
    const response = await apiClient.get(`/api/calls/${callId}`);
    return response.data;
  },

  // Get call result
  getCallResult: async (callId) => {
    const response = await apiClient.get(`/api/calls/${callId}/result`);
    return response.data;
  },

  // Get call details (call + lead + result)
  getCallDetails: async (callId) => {
    const response = await apiClient.get(`/api/calls/${callId}/details`);
    return response.data;
  },

  // Trigger new call
  triggerCall: async (leadId) => {
    const response = await apiClient.post('/api/calls/trigger', { lead_id: leadId });
    return response.data;
  },

  // Get calls count
  getCallsCount: async (params = {}) => {
    const response = await apiClient.get('/api/calls/stats/count', { params });
    return response.data;
  },
};
