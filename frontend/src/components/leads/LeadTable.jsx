/**
 * Leads Table Component
 */

import { useState } from 'react';

const LeadTable = ({ leads, onEdit, onDelete, onCall, loading }) => {
  const getStatusBadge = (status) => {
    const badges = {
      pending: { class: 'badge-gray', text: 'ממתין' },
      calling: { class: 'badge-warning', text: 'בשיחה' },
      called: { class: 'badge-info', text: 'התקשרנו' },
      completed: { class: 'badge-success', text: 'הושלם' },
    };
    const badge = badges[status] || badges.pending;
    return <span className={`badge ${badge.class}`}>{badge.text}</span>;
  };

  const getTypeBadge = (type) => {
    return type === 'drop-off' ? (
      <span className="badge badge-danger">נפל בהרשמה</span>
    ) : (
      <span className="badge badge-warning">לא פעיל</span>
    );
  };

  if (loading) {
    return <div className="text-center py-8">טוען...</div>;
  }

  if (!leads || leads.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        אין לידים להצגה. הוסף ליד חדש להתחלה.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              שם
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              טלפון
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              סוג
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              סטטוס
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              תאריך יצירה
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              פעולות
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {leads.map((lead) => (
            <tr key={lead.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {lead.name}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {lead.phone}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {getTypeBadge(lead.type)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {getStatusBadge(lead.status)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {new Date(lead.created_at).toLocaleDateString('he-IL')}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2 space-x-reverse">
                <button
                  onClick={() => onCall(lead)}
                  disabled={lead.status === 'calling'}
                  className="btn btn-success text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  📞 התקשר
                </button>
                <button
                  onClick={() => onEdit(lead)}
                  className="btn btn-secondary text-xs"
                >
                  ✏️ ערוך
                </button>
                <button
                  onClick={() => onDelete(lead.id)}
                  className="btn btn-danger text-xs"
                >
                  🗑️ מחק
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LeadTable;
