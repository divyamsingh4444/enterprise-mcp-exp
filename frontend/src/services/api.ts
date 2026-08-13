import axios, { AxiosInstance } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

// Debug: Log which API URL is being used
if (typeof window !== 'undefined') {
  console.log('🔗 API URL:', API_URL);
  console.log('🔗 VITE_API_URL env:', import.meta.env.VITE_API_URL);
}

interface SignupRequest {
  email: string;
  password: string;
  org_id: string;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface AuthResponse {
  token: string;
  type: string;
  expires_in_seconds: number;
  org_id: string;
  scopes: string[];
}

interface Tool {
  name: string;
  description: string;
  required_scope: string;
  input_schema: any;
}

interface ToolsListResponse {
  tools: Tool[];
  total: number;
}

interface ToolCallRequest {
  tool: string;
  arguments: Record<string, any>;
}

interface ToolCallResponse {
  success: boolean;
  result?: any;
  error?: string;
  duration_ms: number;
}

class McpAPI {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load token from localStorage
    this.token = localStorage.getItem('mcp_token');
    if (this.token) {
      this.setAuthHeader(this.token);
    }

    // Add request interceptor for auth
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });
  }

  private setAuthHeader(token: string) {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  async healthCheck(): Promise<any> {
    const response = await this.client.get('/health');
    return response.data;
  }

  async signup(data: SignupRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/signup', data);
    this.token = response.data.token;
    localStorage.setItem('mcp_token', this.token);
    this.setAuthHeader(this.token);
    return response.data;
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/login', data);
    this.token = response.data.token;
    localStorage.setItem('mcp_token', this.token);
    this.setAuthHeader(this.token);
    return response.data;
  }

  async logout(): Promise<void> {
    this.token = null;
    localStorage.removeItem('mcp_token');
    delete this.client.defaults.headers.common['Authorization'];
  }

  async getMe(): Promise<any> {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  async listTools(): Promise<ToolsListResponse> {
    const response = await this.client.get<ToolsListResponse>('/api/v1/mcp/tools/list');
    return response.data;
  }

  async callTool(request: ToolCallRequest): Promise<ToolCallResponse> {
    const response = await this.client.post<ToolCallResponse>('/api/v1/mcp/tools/call', request);
    return response.data;
  }

  async getMetrics(): Promise<any> {
    const response = await this.client.get('/metrics');
    return response.data;
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  getToken(): string | null {
    return this.token;
  }
}

export const api = new McpAPI();

export type {
  SignupRequest,
  LoginRequest,
  AuthResponse,
  Tool,
  ToolsListResponse,
  ToolCallRequest,
  ToolCallResponse,
};
