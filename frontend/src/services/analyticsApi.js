/**
 * Analytics API Service
 */

import apiClient from './api';

export const analyticsApi = {
  // Get summary analytics
  getSummary: async () => {
    const response = await apiClient.get('/api/analytics/summary');
    return response.data;
  },

  // Get trends over time
  getTrends: async (days = 30) => {
    const response = await apiClient.get('/api/analytics/trends', {
      params: { days }
    });
    return response.data;
  },

  // Get disposition breakdown
  getDispositions: async () => {
    const response = await apiClient.get('/api/analytics/dispositions');
    return response.data;
  },

  // Get leads status breakdown
  getLeadsStatus: async () => {
    const response = await apiClient.get('/api/analytics/leads/status');
    return response.data;
  },

  // Get performance metrics
  getPerformance: async () => {
    const response = await apiClient.get('/api/analytics/performance');
    return response.data;
  },
};
