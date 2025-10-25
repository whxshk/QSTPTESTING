import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Gap {
  title: string;
  rule_ref: string;
  evidence: string;
  explanation: string;
  severity: 'low' | 'medium' | 'high';
}

export interface SeverityBreakdown {
  count: number;
  deduction_per_gap: number;
  total_deduction: number;
}

export interface ScoreBreakdown {
  base_score: number;
  final_score: number;
  total_deductions: number;
  gap_count: number;
  severity_breakdown: {
    high: SeverityBreakdown;
    medium: SeverityBreakdown;
    low: SeverityBreakdown;
  };
  grade: string;
  category: string;
  color: string;
  needs_expert_review: boolean;
}

export interface Program {
  program_id: string;
  program_name: string;
  focus_areas: string[];
  description: string;
  eligibility: string;
  contact: string;
}

export interface Expert {
  expert_id: string;
  name: string;
  specialization: string;
  experience_years: number;
  background: string;
  availability: string;
  contact: string;
}

export interface Recommendation {
  gap_title: string;
  gap_ref: string;
  severity: string;
  programs: Program[];
  experts: Expert[];
}

export interface AnalysisResult {
  success: boolean;
  score: number;
  grade: string;
  category: string;
  color: string;
  needs_expert_review: boolean;
  gaps: Gap[];
  gap_count: number;
  score_breakdown: ScoreBreakdown;
  recommendations: Recommendation[];
  notes: string[];
  context_chunks_used: number;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  chunks_indexed: number;
  files_processed: number;
  embedding_dimension: number;
}

export const uploadDocuments = async (files: File[]): Promise<UploadResponse> => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const analyzeCompliance = async (summary: string): Promise<AnalysisResult> => {
  const response = await api.post('/analyze', { summary });
  return response.data;
};

export const getHealthStatus = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getRules = async () => {
  const response = await api.get('/rules');
  return response.data;
};

export const getResources = async () => {
  const response = await api.get('/resources');
  return response.data;
};

export const clearIndex = async () => {
  const response = await api.post('/clear');
  return response.data;
};

export default api;
