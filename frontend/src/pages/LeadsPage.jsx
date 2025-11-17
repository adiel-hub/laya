/**
 * Leads Management Page
 */

import { useState, useEffect } from 'react';
import { leadsApi } from '../services/leadsApi';
import { callsApi } from '../services/callsApi';
import LeadTable from '../components/leads/LeadTable';
import AddLeadModal from '../components/leads/AddLeadModal';

const LeadsPage = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingLead, setEditingLead] = useState(null);

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      setLoading(true);
      const data = await leadsApi.getLeads();
      setLeads(data);
    } catch (error) {
      console.error('Error fetching leads:', error);
      alert('שגיאה בטעינת לידים');
    } finally {
      setLoading(false);
    }
  };

  const handleAddLead = () => {
    setEditingLead(null);
    setIsModalOpen(true);
  };

  const handleEditLead = (lead) => {
    setEditingLead(lead);
    setIsModalOpen(true);
  };

  const handleSaveLead = async (leadData) => {
    try {
      if (editingLead) {
        await leadsApi.updateLead(editingLead.id, leadData);
      } else {
        await leadsApi.createLead(leadData);
      }
      fetchLeads();
      alert(editingLead ? 'ליד עודכן בהצלחה' : 'ליד נוסף בהצלחה');
    } catch (error) {
      console.error('Error saving lead:', error);
      alert('שגיאה בשמירת ליד');
    }
  };

  const handleDeleteLead = async (leadId) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק ליד זה?')) {
      return;
    }

    try {
      await leadsApi.deleteLead(leadId);
      fetchLeads();
      alert('ליד נמחק בהצלחה');
    } catch (error) {
      console.error('Error deleting lead:', error);
      alert('שגיאה במחיקת ליד');
    }
  };

  const handleCallLead = async (lead) => {
    if (!confirm(`האם להתקשר ל-${lead.name}?`)) {
      return;
    }

    try {
      await callsApi.triggerCall(lead.id);
      alert('שיחה הופעלה בהצלחה');
      fetchLeads();
    } catch (error) {
      console.error('Error triggering call:', error);
      alert('שגיאה בהפעלת שיחה: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">ניהול לידים</h1>
        <button onClick={handleAddLead} className="btn btn-primary">
          ➕ הוסף ליד חדש
        </button>
      </div>

      <div className="card">
        <LeadTable
          leads={leads}
          loading={loading}
          onEdit={handleEditLead}
          onDelete={handleDeleteLead}
          onCall={handleCallLead}
        />
      </div>

      <AddLeadModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveLead}
        editLead={editingLead}
      />
    </div>
  );
};

export default LeadsPage;
