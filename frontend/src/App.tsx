import { useEffect, useState } from 'react';
import { Login } from './components/Login';
import { Dashboard } from './components/Dashboard';
import { useAuthStore } from './store/auth';
import { api } from './services/api';

function App() {
  const [isInitialized, setIsInitialized] = useState(false);
  const { token } = useAuthStore();

  useEffect(() => {
    // Check backend health on startup
    const checkHealth = async () => {
      try {
        await api.healthCheck();
      } catch (err) {
        console.error('Backend is not available');
      } finally {
        setIsInitialized(true);
      }
    };

    checkHealth();
  }, []);

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="text-4xl mb-4">🚀</div>
          <p className="text-xl">Loading MCP Dashboard...</p>
        </div>
      </div>
    );
  }

  return token ? (
    <Dashboard />
  ) : (
    <Login onSuccess={() => window.location.reload()} />
  );
}

export default App;
