import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';

export default function ProductsTab({ products, url, setUrl, loading, handleAdd, setItemToDelete }) {
  const [openChartIndex, setOpenChartIndex] = useState(null);

  const toggleChart = (index) => {
    setOpenChartIndex(prevIndex => (prevIndex === index ? null : index));
  };

  const getCurrency = (productUrl) => {
    if (!productUrl) return '';
    if (productUrl.includes('.ua') || productUrl.includes('rozetka') || productUrl.includes('prom')) {
      return ' ₴';
    }
    return '';
  };

  const DefaultProductIcon = () => (
    <div className="flex flex-col items-center gap-3 transition-colors text-slate-300 dark:text-slate-600">
      <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
        <path d="M3.27 6.96 12 12.01l8.73-5.05"/>
        <path d="M12 22.08V12"/>
        <circle cx="17.5" cy="17.5" r="3.5" strokeWidth="1.5" className="text-emerald-500"/>
        <path d="M16 19 19 16" strokeWidth="1.5" className="text-emerald-500"/>
      </svg>
      <span className="text-xs font-medium">No Image Found</span>
    </div>
  );

  const handleImageError = (e) => {
    e.target.style.display = 'none';
    e.target.parentElement.classList.add('flex', 'items-center', 'justify-center');
    e.target.parentElement.querySelector('.default-icon-wrapper').style.display = 'flex';
  };

  return (
    <div className="space-y-6 md:space-y-8">
      <div className="text-center max-w-2xl mx-auto mb-10 md:mb-12 mt-2 md:mt-4 transition-colors duration-300">
        <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-3 transition-colors">
          Automated Price Intelligence
        </h2>
        <p className="text-base md:text-lg text-slate-500 dark:text-slate-400 transition-colors">
          Track product prices in real-time. Paste a URL, and our system handles the analytics.
        </p>
      </div>

      <div className="flex flex-col md:flex-row items-center gap-3 bg-white dark:bg-slate-900 p-4 rounded-xl shadow border border-slate-100 dark:border-slate-800 transition-colors duration-300">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste product URL here (Rozetka, Prom)..."
          className="w-full md:flex-1 h-12 md:h-11 px-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 dark:placeholder:text-slate-500 transition-colors duration-300"
        />
        <button
          onClick={handleAdd}
          disabled={loading}
          className="w-full md:w-auto h-12 md:h-11 px-6 bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-lg shadow transition-colors disabled:opacity-70 flex items-center justify-center gap-2 whitespace-nowrap"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              Tracking...
            </>
          ) : (
            'Track Price'
          )}
        </button>
      </div>

      {products.length === 0 ? (
        <div className="text-center py-20 text-slate-500 dark:text-slate-400 flex flex-col items-center gap-4 transition-colors">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-slate-400 dark:text-slate-500 transition-colors">
            <path d="M11 19c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM4 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H6.21l-.94-2H2zm13 17c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
          </svg>
          <span className="font-medium text-[16px] text-slate-500 dark:text-slate-400">No products being tracked yet.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8 items-start">
          {products.map((p, index) => (
            <div key={index} className="bg-white dark:bg-slate-900 p-5 md:p-6 rounded-xl md:rounded-2xl shadow border border-slate-100 dark:border-slate-800 transition-colors duration-300 flex flex-col">

              {/*Блок з картинкою тепер є клікабельним посиланням на магазин*/}
              <a
                href={p.url}
                target="_blank"
                rel="noopener noreferrer"
                title="Відкрити сторінку товару"
                className="h-40 md:h-44 w-full mb-5 md:mb-6 rounded-lg bg-white p-2 border border-slate-100 dark:border-slate-800 flex items-center justify-center transition-colors relative hover:border-emerald-400 dark:hover:border-emerald-600 block cursor-pointer group"
              >
                {p.image_url ? (
                  <>
                    <img
                      src={p.image_url}
                      alt={p.name}
                      className="max-h-full max-w-full object-contain mix-blend-multiply transition-transform duration-300 group-hover:scale-105"
                      onError={handleImageError}
                    />
                    <div className="default-icon-wrapper hidden flex-col items-center justify-center absolute inset-0 bg-white dark:bg-slate-900 rounded-lg">
                      <DefaultProductIcon />
                    </div>
                  </>
                ) : (
                  <DefaultProductIcon />
                )}
              </a>

              <h3 className="text-sm md:text-[15px] font-semibold text-slate-900 dark:text-white line-clamp-2 mb-3 md:mb-4 h-[40px] md:h-[44px] transition-colors" title={p.name}>{p.name}</h3>
              <div className="flex items-end justify-between gap-4">
                <span className="text-xl md:text-2xl font-bold text-slate-950 dark:text-white tracking-tight transition-colors">
                  {p.current_price ? (
                    <>
                      {p.current_price}
                      <span className="text-[16px] md:text-[18px] ml-1 font-medium">{getCurrency(p.url)}</span>
                    </>
                  ) : (
                    <span className="text-slate-400 dark:text-slate-500 text-base font-normal">No price</span>
                  )}
                </span>
                <span className="text-xs text-slate-400 dark:text-slate-500 transition-colors">{new Date(p.added_at).toLocaleDateString()}</span>
              </div>

              {openChartIndex === index && p.history && p.history.length > 0 && (
                <div className="h-28 w-full mt-5 mb-1 animate-in fade-in slide-in-from-top-4 duration-300">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={p.history}>
                      {/* Додано вісь X для дати та змінено форматування*/}
                      <XAxis dataKey="checked_at" hide />
                      <YAxis domain={['dataMin', 'dataMax']} hide />
                      <RechartsTooltip
                        contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '12px', padding: '6px 10px' }}
                        itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
                        labelFormatter={(label) => {
                          if (!label) return '';
                          const date = new Date(label);
                          return date.toLocaleDateString() + ', ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                        }}
                        formatter={(value) => [`${value}${getCurrency(p.url)}`, 'Price']}
                      />
                      <Line type="monotone" dataKey="price" stroke="#10b981" strokeWidth={2.5} dot={{ r: 3.5, fill: '#10b981', strokeWidth: 2, stroke: '#fff' }} activeDot={{ r: 5 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              <div className="pt-4 mt-auto mt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2 transition-colors">
                <a
                  href={`https://www.google.com/search?q=${encodeURIComponent(p.name)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 py-2 text-xs font-medium text-center text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                >
                  Find Similar
                </a>
                <button
                  onClick={() => toggleChart(index)}
                  className={`px-4 py-2 flex items-center justify-center border rounded-lg transition-colors ${openChartIndex === index ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-800 text-emerald-600 dark:text-emerald-400' : 'border-slate-200 dark:border-slate-700 text-slate-400 hover:text-emerald-500 hover:border-emerald-200 dark:hover:border-emerald-800'}`}
                  title="Price History Chart"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                  </svg>
                </button>
                <button
                  onClick={() => setItemToDelete(p)}
                  className="flex-1 py-2 text-xs font-medium text-red-600 dark:text-red-400 border border-red-100 dark:border-red-900/40 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}