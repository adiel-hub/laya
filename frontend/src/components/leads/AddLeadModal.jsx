/**
 * Add/Edit Lead Modal Component
 */

import { useState } from 'react';

const AddLeadModal = ({ isOpen, onClose, onSave, editLead = null }) => {
  const [formData, setFormData] = useState(editLead || {
    name: '',
    phone: '',
    type: 'drop-off',
    drop_stage: '',
    last_active: '',
    notes: '',
  });

  const [errors, setErrors] = useState({});

  if (!isOpen) return null;

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'שם חובה';
    }

    if (!formData.phone.trim()) {
      newErrors.phone = 'טלפון חובה';
    } else if (!/^\+?[1-9]\d{1,14}$/.test(formData.phone)) {
      newErrors.phone = 'פורמט טלפון לא תקין (דוגמה: +972501234567)';
    }

    if (formData.type === 'drop-off' && !formData.drop_stage) {
      newErrors.drop_stage = 'שלב נפילה חובה עבור drop-off';
    }

    if (formData.type === 'dormant' && !formData.last_active) {
      newErrors.last_active = 'תאריך פעילות אחרונה חובה עבור dormant';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (validateForm()) {
      onSave(formData);
      onClose();
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">
            {editLead ? 'עריכת ליד' : 'הוספת ליד חדש'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="label">שם מלא</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={`input ${errors.name ? 'border-red-500' : ''}`}
              placeholder="יוסי כהן"
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name}</p>
            )}
          </div>

          {/* Phone */}
          <div>
            <label className="label">טלפון</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className={`input ${errors.phone ? 'border-red-500' : ''}`}
              placeholder="+972501234567"
            />
            {errors.phone && (
              <p className="text-red-500 text-sm mt-1">{errors.phone}</p>
            )}
          </div>

          {/* Type */}
          <div>
            <label className="label">סוג</label>
            <select
              name="type"
              value={formData.type}
              onChange={handleChange}
              className="input"
            >
              <option value="drop-off">נפל בהרשמה (Drop-off)</option>
              <option value="dormant">לא פעיל (Dormant)</option>
            </select>
          </div>

          {/* Drop Stage (conditional) */}
          {formData.type === 'drop-off' && (
            <div>
              <label className="label">שלב נפילה</label>
              <select
                name="drop_stage"
                value={formData.drop_stage}
                onChange={handleChange}
                className={`input ${errors.drop_stage ? 'border-red-500' : ''}`}
              >
                <option value="">בחר שלב...</option>
                <option value="identity_verify">אימות זהות</option>
                <option value="funding">טעינת כסף</option>
                <option value="card_setup">הגדרת כרטיס</option>
                <option value="other">אחר</option>
              </select>
              {errors.drop_stage && (
                <p className="text-red-500 text-sm mt-1">{errors.drop_stage}</p>
              )}
            </div>
          )}

          {/* Last Active (conditional) */}
          {formData.type === 'dormant' && (
            <div>
              <label className="label">תאריך פעילות אחרונה</label>
              <input
                type="date"
                name="last_active"
                value={formData.last_active}
                onChange={handleChange}
                className={`input ${errors.last_active ? 'border-red-500' : ''}`}
              />
              {errors.last_active && (
                <p className="text-red-500 text-sm mt-1">{errors.last_active}</p>
              )}
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="label">הערות</label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              className="input"
              rows="3"
              placeholder="הערות נוספות..."
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              className="btn btn-primary flex-1"
            >
              {editLead ? 'עדכן' : 'שמור'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary flex-1"
            >
              ביטול
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddLeadModal;
