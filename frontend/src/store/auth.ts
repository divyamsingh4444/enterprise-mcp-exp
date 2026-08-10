import { create } from 'zustand';
import { api, AuthResponse } from '../services/api';

interface AuthState {
  token: string | null;
  user: AuthResponse | null;
  isLoading: boolean;
  error: string | null;
  signup: (email: string, password: string, org_id: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('mcp_token'),
  user: null,
  isLoading: false,
  error: null,

  signup: async (email: string, password: string, org_id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.signup({ email, password, org_id });
      set({ user: response, token: response.token, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Signup failed', isLoading: false });
      throw error;
    }
  },

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.login({ email, password });
      set({ user: response, token: response.token, isLoading: false });
    } catch (error: any) {
      set({ error: error.response?.data?.detail || 'Login failed', isLoading: false });
      throw error;
    }
  },

  logout: () => {
    api.logout();
    set({ token: null, user: null, error: null });
  },

  clearError: () => set({ error: null }),
}));
