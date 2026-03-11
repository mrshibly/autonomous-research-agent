import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred.';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

/**
 * Submit a new research topic.
 */
export const submitResearch = async (topic, maxPapers = 5) => {
  const response = await api.post('/research', {
    topic,
    max_papers: maxPapers,
  });
  return response.data;
};

/**
 * Get the status of a research task.
 */
export const getResearchStatus = async (taskId) => {
  const response = await api.get(`/research/${taskId}/status`);
  return response.data;
};

export const getResearchReport = async (taskId) => {
  const response = await api.get(`/research/${taskId}/report`);
  return response.data;
};

/**
 * Chat with a specific research task.
 */
export const chatWithResearch = async (taskId, message) => {
  const response = await api.post(`/research/${taskId}/chat`, { message });
  return response.data;
};

/**
 * Export URLs.
 */
export const getPDFExportUrl = (taskId) => `${API_BASE_URL}/research/${taskId}/export/pdf`;
export const getBibTeXExportUrl = (taskId) => `${API_BASE_URL}/research/${taskId}/export/bibtex`;

/**
 * Get research history.
 */
export const getResearchHistory = async (page = 1, pageSize = 20) => {
  const response = await api.get('/research/history', {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

/**
 * Delete a research task.
 */
export const deleteResearch = async (taskId) => {
  await api.delete(`/research/${taskId}`);
};

export default api;
