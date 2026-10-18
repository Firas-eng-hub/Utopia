import { useState } from 'react';
import { motion } from 'framer-motion';
import { Github, Loader2, X, ExternalLink } from 'lucide-react';
import { API_BASE_URL } from '../../services/api-config';

interface FootprintScanFormProps {
  onComplete: () => void;
  onCancel: () => void;
}

export default function FootprintScanForm({ onComplete, onCancel }: FootprintScanFormProps) {
  const [githubUsername, setGithubUsername] = useState('');
  const [stackoverflowId, setStackoverflowId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!githubUsername && !stackoverflowId) {
      setError('Please provide at least one profile (GitHub or Stack Overflow)');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/footprint/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          github_username: githubUsername || undefined,
          stackoverflow_user_id: stackoverflowId ? parseInt(stackoverflowId) : undefined
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Scan complete:', data);
        onComplete();
      } else {
        const errorData = await response.json();
        let errorMessage = errorData.detail || 'Failed to scan profiles';
        
        // Make error messages more user-friendly
        if (response.status === 404) {
          errorMessage = errorData.detail || `GitHub user "${githubUsername}" not found. Please check your username.`;
        } else if (response.status === 401) {
          errorMessage = 'Your session has expired. Please log in again.';
        } else if (response.status === 500) {
          errorMessage = 'Server error. Please try again later or contact support.';
        }
        
        setError(errorMessage);
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error('Scan error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm p-8 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-2xl w-full"
      >
        <div className="bg-white rounded-3xl p-8 border border-gray-200 shadow-2xl">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Scan Your Footprint</h2>
              <p className="text-gray-600">Analyze your professional presence across platforms</p>
            </div>
            <button
              onClick={onCancel}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              disabled={loading}
            >
              <X className="w-6 h-6 text-gray-600" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* GitHub Input */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <div className="flex items-center gap-2">
                  <Github className="w-5 h-5" />
                  GitHub Username (required)
                </div>
              </label>
              <input
                type="text"
                value={githubUsername}
                onChange={(e) => setGithubUsername(e.target.value)}
                placeholder="octocat"
                className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                disabled={loading}
              />
              <div className="mt-2 space-y-1">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <ExternalLink className="w-4 h-4" />
                  <a
                    href="https://github.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-primary-600 transition-colors"
                  >
                    Find your GitHub username
                  </a>
                </div>
                <p className="text-xs text-gray-500 ml-6">
                  💡 Your username appears in your GitHub URL: github.com/<strong>username</strong>
                </p>
              </div>
            </div>

            {/* Stack Overflow Input */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.986 21.865v-6.404h2.134V24H1.844v-8.539h2.13v6.404h15.012zM6.111 19.731H16.85v-2.137H6.111v2.137zm.259-4.852l10.48 2.189.451-2.07-10.478-2.187-.453 2.068zm1.359-5.056l9.705 4.53.903-1.95-9.706-4.53-.902 1.936v.014zm2.715-4.785l8.217 6.855 1.359-1.62-8.216-6.853-1.35 1.617-.01.001zM15.751 0l-1.746 1.294 6.405 8.604 1.746-1.294L15.749 0h.002z"/>
                  </svg>
                  Stack Overflow User ID (Optional)
                </div>
              </label>
              <input
                type="text"
                value={stackoverflowId}
                onChange={(e) => setStackoverflowId(e.target.value)}
                placeholder="22656"
                className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
                disabled={loading}
              />
              <div className="mt-2 flex items-center gap-2 text-sm text-gray-600">
                <ExternalLink className="w-4 h-4" />
                <a
                  href="https://stackoverflow.com/users"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-primary-600 transition-colors"
                >
                  Find your Stack Overflow ID
                </a>
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-red-50 border border-red-200 rounded-xl"
              >
                <p className="text-red-600 text-sm">{error}</p>
              </motion.div>
            )}

            {/* Submit Button */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onCancel}
                className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-xl font-semibold hover:bg-gray-300 transition-colors"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-6 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Scanning...
                  </>
                ) : (
                  'Start Scan'
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 p-4 bg-primary-50 border border-primary-200 rounded-xl">
            <p className="text-sm text-primary-700">
              <strong>💡 Tip:</strong> Scanning may take 10-30 seconds. We analyze your contribution history, 
              repositories, and community activity to generate your professional footprint score.
            </p>
          </div>
          
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl">
            <p className="text-sm text-blue-900 font-semibold mb-1">
              📌 How to find your GitHub username:
            </p>
            <ul className="text-sm text-blue-800 space-y-1 ml-4 list-disc">
              <li>Go to <a href="https://github.com" target="_blank" className="underline font-medium">github.com</a> and sign in</li>
              <li>Your username appears in the URL: <code className="bg-blue-100 px-1 rounded">github.com/<strong>username</strong></code></li>
              <li>It's <strong>not</strong> your full name (no spaces allowed)</li>
              <li>Examples: "octocat", "torvalds", "gvanrossum"</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
