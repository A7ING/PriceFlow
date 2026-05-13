import { useState } from 'react';

export default function AuthScreen({ onAuthSuccess, showToast }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        // Логіка Вход
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData,
        });

        if (res.ok) {
          const data = await res.json();
          onAuthSuccess(data.access_token);
          showToast('Welcome back!', 'success');
        } else {
          showToast('Invalid username or password', 'error');
        }
      } else {
        // Логіка реестрації
        const res = await fetch('/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });

        if (res.ok) {
          showToast('Account created! Please log in.', 'success');
          setIsLogin(true);
          setPassword('');
        } else {
          const errorData = await res.json();
          let errorMessage = 'Registration failed';

          if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail;
          }
          //Помилка валідації 422
          else if (Array.isArray(errorData.detail)) {
              const errorType = errorData.detail[0]?.type;
              if (errorType && errorType.includes('pattern')) {
                  errorMessage = 'Your username can only contain letters, numbers, and underscores (no spaces or @ symbols)';
              } else if (errorType && errorType.includes('too_short')) {
                  errorMessage = 'Your password must be at least 6 characters long';
              } else {
                  errorMessage = 'Invalid login format. Please check your username and password';
              }
          }

          showToast(errorMessage, 'error');
        }
      }
    } catch (error) {
      showToast('No connection to server. Please wait.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAFA] dark:bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 selection:bg-emerald-100 selection:text-emerald-900 animate-in fade-in duration-500 transition-colors">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
        <div className="flex items-center justify-center gap-2">
          <svg
            width="36"
            height="36"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-emerald-500"
          >
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>

          <span className="font-extrabold text-4xl tracking-tight text-slate-900 dark:text-white">
            PriceFlow
          </span>
        </div>

        <p className="mt-3 text-slate-500 dark:text-slate-400 font-medium">
          Your personal price intelligence hub
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-slate-800 py-8 px-6 shadow-xl shadow-slate-200/40 dark:shadow-none sm:rounded-2xl sm:px-10 border border-slate-100 dark:border-slate-700 transition-colors">

          {/* Перемикач вкладок */}
          <div className="flex p-1 mb-8 bg-slate-100 dark:bg-slate-900 rounded-xl transition-colors">
            <button
              type="button"
              onClick={() => {
                setIsLogin(true);
                setUsername('');
                setPassword('');
              }}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all duration-200 ${
                isLogin
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
              }`}
            >
              Sign In
            </button>

            <button
              type="button"
              onClick={() => {
                setIsLogin(false);
                setUsername('');
                setPassword('');
              }}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all duration-200 ${
                !isLogin
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
              }`}
            >
              Create Account
            </button>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>

            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Username
              </label>

              <div className="relative flex items-center">
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value.replace(/\s/g, ''))}
                  className="w-full h-11 px-4 pr-10 rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900/50 text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors text-sm"
                  placeholder="your_username"
                />

                {/* Іконка підказки (tooltip) */}
                {!isLogin && (
                  <div className="absolute right-3 flex items-center group cursor-help">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-slate-400 hover:text-emerald-500 transition-colors">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                    </svg>

                    <div className="absolute bottom-full right-[-10px] mb-2 hidden group-hover:block w-56 p-2.5 text-xs text-white bg-slate-800 dark:bg-slate-700 rounded-lg shadow-xl z-10 text-center font-medium">
                      One word only. Letters, numbers, and underscores allowed (no spaces).
                      <svg className="absolute text-slate-800 dark:text-slate-700 h-2 w-full left-0 top-full flex justify-end pr-[14px]" x="0px" y="0px" viewBox="0 0 255 255" xmlSpace="preserve"><polygon className="fill-current" points="0,0 127.5,127.5 255,0"/></svg>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Password
              </label>

              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-11 px-4 rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900/50 text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors text-sm"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 flex justify-center items-center bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl shadow-sm transition-all disabled:opacity-70 mt-2"
            >
              {loading ? (
                <svg
                  className="animate-spin -ml-1 mr-2 h-5 w-5 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>

                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
              ) : isLogin ? (
                'Sign In to Dashboard'
              ) : (
                'Register Account'
              )}
            </button>

          </form>
        </div>
      </div>
    </div>
  );
}