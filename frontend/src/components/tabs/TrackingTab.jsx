import { useState } from 'react';

export default function TrackingTab({
  products,
  updateFreq,
  setUpdateFreq,
  notifyOn,
  setNotifyOn,
  notifyMethod,
  setNotifyMethod,
  contactInfo,
  setContactInfo,
  isFreqOpen,
  setIsFreqOpen,
  saveSettings,
  handleForceUpdate
}) {
  const [showTelegramTooltip, setShowTelegramTooltip] = useState(false);

  const freqOptions = [
    { id: '6h', label: 'Every 6 hours' },
    { id: '12h', label: 'Every 12 hours' },
    { id: '24h', label: 'Once a day' },
    { id: '72h', label: 'Every 3 days' }
  ];

  return (
    <div className="max-w-6xl mx-auto animate-in fade-in duration-300">
      <div className="mb-8">
        <div className="text-center max-w-2xl mx-auto mb-12 mt-4">
          <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-3 transition-colors">
            System Tracking & Alerts
          </h2>
          <p className="text-lg text-slate-500 dark:text-slate-400 transition-colors">
            Manage how and when the system checks prices.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden transition-colors duration-300">
          <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50 flex justify-between items-center transition-colors">
            <h3 className="font-semibold text-slate-800 dark:text-white transition-colors">
              Parser Status
            </h3>
            <span className="text-xs font-medium px-2.5 py-1 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 rounded-full transition-colors">
              System Online
            </span>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800 transition-colors">
            {products.map(product => (
              <div
                key={product.id}
                className="p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-white rounded-lg border border-slate-100 dark:border-slate-700 flex items-center justify-center p-1 transition-colors">
                    <img
                      src={product.image_url}
                      alt=""
                      className="max-h-full object-contain mix-blend-multiply opacity-80"
                    />
                  </div>
                  <div>
                    <h4
                      className="font-medium text-slate-900 dark:text-white line-clamp-1 max-w-[300px] transition-colors"
                      title={product.name}
                    >
                      {product.name}
                    </h4>
                    <div className="flex items-center gap-3 text-xs mt-1">
                      <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium transition-colors">
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                        Tracked active
                      </span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleForceUpdate(product.id)}
                  className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 hover:text-emerald-600 dark:hover:text-emerald-400 hover:border-emerald-200 dark:hover:border-emerald-500/50 transition-all whitespace-nowrap"
                >
                  Update Now
                </button>
              </div>
            ))}
            {products.length === 0 && (
              <div className="p-6 text-center text-slate-500 dark:text-slate-400 transition-colors">
                No active tracking tasks.
              </div>
            )}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm h-fit transition-colors duration-300">
          <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50 transition-colors">
            <h3 className="font-semibold text-slate-800 dark:text-white transition-colors">
              Alert Preferences
            </h3>
          </div>
          <div className="p-6 space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 transition-colors">
                Parser Frequency
              </label>
              <div className="relative">
                <div
                  className="w-full h-11 px-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between cursor-pointer hover:bg-white dark:hover:bg-slate-800 transition-colors"
                  onClick={() => setIsFreqOpen(!isFreqOpen)}
                >
                  <span className="text-sm text-slate-700 dark:text-slate-200 transition-colors">
                    {freqOptions.find(o => o.id === updateFreq)?.label}
                  </span>
                  <svg
                    className={`w-4 h-4 text-slate-400 dark:text-slate-500 transition-transform ${isFreqOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
                {isFreqOpen && (
                  <div className="absolute top-full left-0 w-full mt-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg overflow-hidden z-10 transition-colors">
                    {freqOptions.map(option => (
                      <div
                        key={option.id}
                        className={`px-4 py-3 text-sm cursor-pointer hover:bg-emerald-50 dark:hover:bg-slate-700 transition-colors border-b border-slate-50 dark:border-slate-700/50 last:border-0 ${updateFreq === option.id ? 'text-emerald-600 dark:text-emerald-400 font-medium bg-emerald-50/30 dark:bg-slate-700/50' : 'text-slate-600 dark:text-slate-300'}`}
                        onClick={() => {
                          setUpdateFreq(option.id);
                          setIsFreqOpen(false);
                        }}
                      >
                        {option.label}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 transition-colors">
                Notify me when...
              </label>
              <div className="space-y-3">
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${notifyOn.drop ? 'bg-emerald-500 border-emerald-500' : 'border-slate-300 dark:border-slate-600 group-hover:border-emerald-400 dark:bg-slate-800'}`}>
                    {notifyOn.drop && (
                      <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
                      </svg>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={notifyOn.drop}
                    onChange={() => setNotifyOn({...notifyOn, drop: !notifyOn.drop})}
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300 transition-colors">
                    Price drops (Discount)
                  </span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${notifyOn.rise ? 'bg-emerald-500 border-emerald-500' : 'border-slate-300 dark:border-slate-600 group-hover:border-emerald-400 dark:bg-slate-800'}`}>
                    {notifyOn.rise && (
                      <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
                      </svg>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={notifyOn.rise}
                    onChange={() => setNotifyOn({...notifyOn, rise: !notifyOn.rise})}
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300 transition-colors">
                    Price increases
                  </span>
                </label>
              </div>
            </div>

            <hr className="border-slate-100 dark:border-slate-800 transition-colors" />

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 transition-colors">
                Delivery Method
              </label>
              <div className="flex gap-2 mb-3">
                <button
                  onClick={() => setNotifyMethod('email')}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg border transition-colors ${notifyMethod === 'email'
                    ? 'bg-slate-900 dark:bg-emerald-600 text-white border-slate-900 dark:border-emerald-600'
                    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
                  }`}
                >
                  Email
                </button>
                <button
                  onClick={() => setNotifyMethod('telegram')}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg border transition-colors ${notifyMethod === 'telegram'
                    ? 'bg-[#229ED9] text-white border-[#229ED9]'
                    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
                  }`}
                >
                  Telegram
                </button>
              </div>
              <div className="relative flex items-center">
                <input
                  type="text"
                  placeholder={notifyMethod === 'email'
                    ? 'your@email.com'
                    : 'Chat ID (digits only)'
                  }
                  value={contactInfo}
                  onChange={(e) => setContactInfo(e.target.value)}
                  className="w-full h-11 px-3 pr-10 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-slate-900 dark:text-white focus:bg-white dark:focus:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors text-sm"
                />
                {notifyMethod === 'telegram' && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center z-10">
                    <button
                      type="button"
                      onMouseEnter={() => setShowTelegramTooltip(true)}
                      onMouseLeave={() => setShowTelegramTooltip(false)}
                      onClick={() => setShowTelegramTooltip(true)}
                      onBlur={() => setShowTelegramTooltip(false)}
                      className="w-5 h-5 rounded-full border-2 border-slate-300 dark:border-slate-600 text-slate-400 dark:text-slate-500 flex items-center justify-center text-xs font-bold hover:border-[#229ED9] hover:text-[#229ED9] transition-colors"
                    >
                      i
                    </button>
                    {showTelegramTooltip && (
                      <div className="absolute bottom-full right-0 mb-2 w-64 p-4 bg-slate-800 dark:bg-slate-700 text-white text-xs rounded-xl shadow-xl">
                        <p className="font-semibold mb-2 text-[#229ED9] text-sm">
                          How to get your Chat ID:
                        </p>
                        <ol className="list-decimal ml-4 space-y-1.5 text-slate-300">
                          <li>
                            Open Telegram and search for
                            <span className="text-white font-medium">
                              {' '}@getmyid_bot
                            </span>
                          </li>
                          <li>
                            Send the
                            <span className="bg-slate-700 dark:bg-slate-900 px-1.5 py-0.5 rounded text-white">
                              {' '}/start{' '}
                            </span>
                            command
                          </li>
                          <li>
                            Copy the digits from <b>Your user ID</b>
                          </li>
                        </ol>
                        <div className="absolute top-full right-[6px] border-[6px] border-transparent border-t-slate-800 dark:border-t-slate-700"></div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={saveSettings}
              className="w-full h-11 bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-xl shadow-sm transition-colors mt-2"
            >
              Save Preferences
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}