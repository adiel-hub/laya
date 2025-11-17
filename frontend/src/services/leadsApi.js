/**
 * Leads API Service
 */

import apiClient from './api';

export const leadsApi = {
  // Get all leads
  getLeads: async (params = {}) => {
    const response = await apiClient.get('/api/leads', { params });
    return response.data;
  },

  // Get single lead
  getLead: async (leadId) => {
    const response = await apiClient.get(`/api/leads/${leadId}`);
    return response.data;
  },

  // Create new lead
  createLead: async (leadData) => {
    const response = await apiClient.post('/api/leads', leadData);
    return response.data;
  },

  // Update lead
  updateLead: async (leadId, leadData) => {
    const response = await apiClient.put(`/api/leads/${leadId}`, leadData);
    return response.data;
  },

  // Delete lead
  deleteLead: async (leadId) => {
    const response = await apiClient.delete(`/api/leads/${leadId}`);
    return response.data;
  },

  // Update lead status
  updateLeadStatus: async (leadId, status) => {
    const response = await apiClient.patch(`/api/leads/${leadId}/status`, null, {
      params: { new_status: status }
    });
    return response.data;
  },

  // Get leads count
  getLeadsCount: async (params = {}) => {
    const response = await apiClient.get('/api/leads/stats/count', { params });
    return response.data;
  },
};
