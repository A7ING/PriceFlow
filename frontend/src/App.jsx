import { useState, useEffect, useCallback } from 'react';
import ProductsTab from './components/tabs/ProductsTab';
import TrackingTab from './components/tabs/TrackingTab';
import AnalyticsTab from './components/tabs/AnalyticsTab';
import AuthScreen from './components/AuthScreen';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const [activeTab, setActiveTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);

  const [updateFreq, setUpdateFreq] = useState('12h');
  const [notifyOn, setNotifyOn] = useState({ drop: true, rise: false });
  const [notifyMethod, setNotifyMethod] = useState('email');
  const [contactInfo, setContactInfo] = useState('');
  const [isFreqOpen, setIsFreqOpen] = useState(false);

  const [toast, setToast] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);

  useEffect(() => {
    const isDark = localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
    if (isDark) {
      document.documentElement.classList.add('dark');
      setIsDarkMode(true);
    } else {
      document.documentElement.classList.remove('dark');
      setIsDarkMode(false);
    }
  }, []);

  const toggleTheme = () => {
    if (isDarkMode) {
      document.documentElement.classList.remove('dark');
      localStorage.theme = 'light';
      setIsDarkMode(false);
    } else {
      document.documentElement.classList.add('dark');
      localStorage.theme = 'dark';
      setIsDarkMode(true);
    }
  };

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleAuthSuccess = (newToken) => {
    setToken(newToken);
    localStorage.setItem('token', newToken);
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('token');
    setProducts([]);
    setAnalyticsData(null);
    showToast('Logged out successfully', 'info');
  };

  const getHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  });

  const fetchProducts = useCallback(async () => {
    try {
      const res = await fetch('/api/products', { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json();
        setProducts(data);
      } else if (res.status === 401) handleLogout();
    } catch (e) { console.error(e); }
  }, [token]);

  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch('/api/settings', { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json();
        setUpdateFreq(data.update_freq || '12h');
        setNotifyOn({ drop: data.notify_drop, rise: data.notify_rise });
        setNotifyMethod(data.notify_method || 'email');
        setContactInfo(data.contact_info || '');
      }
    } catch (e) { console.error(e); }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchProducts();
      fetchSettings();
      if (activeTab === 'analytics') {
        fetch('/api/analytics', { headers: getHeaders() })
          .then(r => r.json())
          .then(data => {
            if (data.status === 'success') setAnalyticsData(data);
          })
          .catch(e => console.error(e));
      }
    }
  }, [activeTab, token, fetchProducts, fetchSettings]);

  const handleAdd = async () => {
    if (!url) return;
    setLoading(true);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 90000);

    try {
      const res = await fetch('/api/track', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ url }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (res.ok) {
        setUrl('');
        fetchProducts();
        showToast('Product tracked successfully!', 'success');
      } else {
        const err = await res.json();
        showToast(err.detail || 'Failed to add product', 'error');
      }
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        showToast('Request took too long. The product might still be added soon.', 'info');
      } else {
        showToast('Error tracking product', 'error');
      }
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const confirmDelete = async () => {
    if (!itemToDelete) return;
    try {
      const res = await fetch(`/api/products/${itemToDelete.id}`, {
        method: 'DELETE',
        headers: getHeaders()
      });
      if (res.ok) {
        setItemToDelete(null);
        fetchProducts();
        showToast('Product removed from tracking', 'info');
      }
    } catch (error) {
      showToast('Error deleting product', 'error');
    }
  };

  const handleForceUpdate = async (id) => {
    showToast(`Starting parser for product #${id}...`, 'info');
    try {
      const res = await fetch(`/api/products/${id}/force-update`, {
        method: 'POST',
        headers: getHeaders()
      });
      if (res.ok) {
        fetchProducts();
        showToast("Price updated successfully!", "success");
      }
    } catch (error) {
      showToast('Failed to update price.', 'error');
    }
  };

  const saveSettings = async () => {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        update_freq: updateFreq, notify_drop: notifyOn.drop,
        notify_rise: notifyOn.rise, notify_method: notifyMethod, contact_info: contactInfo
      })
    });
    if (res.ok) showToast("Settings saved successfully", "success");
  };

  if (!token) {
    return (
      <>
        {toast && (
          <div className={`fixed bottom-8 right-8 px-6 py-4 rounded-xl shadow-2xl z-50 text-white ${toast.type === 'error' ? 'bg-red-600' : toast.type === 'success' ? 'bg-emerald-600' : 'bg-slate-800'}`}>
            {toast.message}
          </div>
        )}
        <AuthScreen onAuthSuccess={handleAuthSuccess} showToast={showToast} />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAFAFA] dark:bg-slate-950 font-sans text-slate-900 dark:text-white pb-16 transition-colors duration-300">

      {toast && (
        <div className={`fixed bottom-8 right-8 px-6 py-4 rounded-xl shadow-2xl z-50 text-white flex items-center gap-2 ${toast.type === 'error' ? 'bg-red-600' : toast.type === 'success' ? 'bg-emerald-600' : 'bg-slate-800 dark:bg-slate-700'}`}>
          <span className="font-medium text-sm">{toast.message}</span>
        </div>
      )}
      <header className="sticky top-0 z-40 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 mb-8 md:mb-12 transition-colors">
        <div className="w-full mx-auto px-4 md:px-8 py-3 md:py-0 md:h-16 flex flex-wrap md:flex-nowrap items-center justify-between relative">

          <div className="flex items-center gap-2 cursor-pointer z-10 w-full md:w-auto justify-between md:justify-start" onClick={() => setActiveTab('products')}>
            <div className="flex items-center gap-2">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-500">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
              <span className="font-bold text-lg text-slate-900 dark:text-white tracking-tight">PriceFlow</span>
            </div>

            <div className="flex md:hidden items-center gap-2">
              <button onClick={toggleTheme} className="px-2 py-1 text-[11px] font-semibold rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                {isDarkMode ? 'Light' : 'Dark'}
              </button>
              <button onClick={handleLogout} className="bg-slate-900 dark:bg-emerald-600 text-white px-2 py-1 rounded text-[11px] font-medium shadow-sm">
                Log out
              </button>
            </div>
          </div>

          <nav className="w-full md:w-auto flex items-center justify-start md:justify-center gap-6 md:gap-10 overflow-x-auto mt-4 md:mt-0 md:absolute md:left-1/2 md:-translate-x-1/2 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
            {['products', 'tracking', 'analytics'].map(t => (
              <button
                key={t}
                onClick={() => setActiveTab(t)}
                className={`text-[15px] md:text-[16px] font-semibold capitalize transition-all duration-200 whitespace-nowrap relative focus:outline-none ${
                  activeTab === t
                    ? 'text-emerald-600 dark:text-emerald-500 border-b-2 border-emerald-500 pb-1.5'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white pb-1.5 border-b-2 border-transparent'
                }`}
              >
                {t}
              </button>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-4 z-10 ml-auto">
            <button onClick={toggleTheme} className="px-4 py-2 text-sm font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition-all">
              {isDarkMode ? 'Light Mode' : 'Dark Mode'}
            </button>
            <button onClick={handleLogout} className="bg-slate-900 dark:bg-emerald-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-slate-800 dark:hover:bg-emerald-500 transition-all shadow-md">
              Log out
            </button>
          </div>

        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 md:px-8">
        {activeTab === 'products' && (
          <ProductsTab products={products} url={url} setUrl={setUrl} loading={loading} handleAdd={handleAdd} setItemToDelete={setItemToDelete} />
        )}
        {activeTab === 'tracking' && (
          <TrackingTab
            products={products} updateFreq={updateFreq} setUpdateFreq={setUpdateFreq}
            notifyOn={notifyOn} setNotifyOn={setNotifyOn} notifyMethod={notifyMethod}
            setNotifyMethod={setNotifyMethod} contactInfo={contactInfo} setContactInfo={setContactInfo}
            isFreqOpen={isFreqOpen} setIsFreqOpen={setIsFreqOpen} saveSettings={saveSettings}
            handleForceUpdate={handleForceUpdate}
          />
        )}
        {activeTab === 'analytics' && <AnalyticsTab analyticsData={analyticsData} />}
      </main>

      {itemToDelete && (
        <div className="fixed inset-0 bg-slate-900/40 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in transition-colors">
          <div className="bg-white dark:bg-slate-900 border dark:border-slate-800 rounded-2xl shadow-xl max-w-md w-full p-6 transition-colors">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Delete Product</h3>
            <p className="text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
              Are you sure you want to stop tracking <span className="font-medium text-slate-700 dark:text-slate-200">{itemToDelete.name}</span>? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setItemToDelete(null)} className="flex-1 h-11 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl font-medium transition-colors">Cancel</button>
              <button onClick={confirmDelete} className="flex-1 h-11 bg-red-600 hover:bg-red-700 text-white rounded-xl font-medium transition-colors shadow-sm">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;