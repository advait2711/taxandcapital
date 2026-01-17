import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getSections = async () => {
  const response = await api.get('/sections/');
  return response.data;
};

export const calculateTDS = async (entity, transactions) => {
  const response = await api.post('/calculate/', {
    entity,
    transactions,
  });
  return response.data;
};

export const downloadExcel = async (entity, results) => {
  try {
    // Use fetch instead of axios for better blob handling
    const response = await fetch(`${API_BASE_URL}/generate-excel/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        entity,
        results,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to generate Excel');
    }

    // Get the blob from response
    const blob = await response.blob();

    // Generate filename
    const sanitizedName = entity.entity_name.replace(/[^a-zA-Z0-9\s]/g, '').replace(/\s+/g, '_');
    const dateStr = new Date().toISOString().split('T')[0].replace(/-/g, '');
    const filename = `${sanitizedName}_Report_${dateStr}.xlsx`;

    // Create a temporary anchor element and trigger download
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = downloadUrl;
    a.download = filename;

    // Append to body, click, and remove
    document.body.appendChild(a);
    a.click();

    // Cleanup after a short delay
    setTimeout(() => {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    }, 150);

    return true;
  } catch (error) {
    console.error('Excel download error:', error);
    throw error;
  }
};

export default api;
