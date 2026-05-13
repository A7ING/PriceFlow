import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, Legend
} from 'recharts';

export default function AnalyticsTab({ analyticsData }) {
  if (!analyticsData) {
    return (
      <div className="text-center text-slate-500 dark:text-slate-400 mt-20 animate-pulse font-medium transition-colors">
        Loading intelligence data...
      </div>
    );
  }

  const { metrics, charts, logs } = analyticsData;

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-lg rounded-lg p-3 text-sm transition-colors">
          <p className="font-semibold text-slate-800 dark:text-white">{`${payload[0].value}`}</p>
        </div>
      );
    }
    return null;
  };

  const metricsData = [
    {
      label: 'Total Monitored Value',
      value: `${metrics.total_value.toLocaleString()} UAH`,
      color: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400',
      icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    },
    {
      label: 'Active Products',
      value: `${metrics.active_items} Items`,
      color: 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
      icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    },
    {
      label: 'Checks Performed',
      value: `${metrics.checks_performed} Scans`,
      color: 'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400',
      icon: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    }
  ];

  return (
    <div className="max-w-7xl mx-auto animate-in fade-in duration-300">
      <div className="mb-10 text-center mt-4 transition-colors duration-300">
        <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-3 transition-colors">Global Market Insights</h2>
        <p className="text-lg text-slate-500 dark:text-slate-400 transition-colors">Real-time analytics and parsing statistics.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {metricsData.map((m, i) => (
          <div key={i} className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center gap-5 transition-colors duration-300">
            <div className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${m.color}`}>
               <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">{m.icon}</svg>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1 transition-colors">{m.label}</p>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white transition-colors">{m.value}</h3>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm h-[400px] flex flex-col transition-colors duration-300">
          <h3 className="font-bold text-slate-800 dark:text-white mb-6 transition-colors">Platform Distribution</h3>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={charts.platforms} cx="50%" cy="50%" innerRadius={80} outerRadius={120} paddingAngle={5} dataKey="value">
                {charts.platforms.map((entry, index) => <Cell key={index} fill={entry.fill} stroke="transparent" />)}
              </Pie>
              <RechartsTooltip content={<CustomTooltip />} />
              <Legend verticalAlign="bottom" height={36} wrapperStyle={{ color: 'inherit' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm h-[400px] flex flex-col transition-colors duration-300">
          <h3 className="font-bold text-slate-800 dark:text-white mb-6 transition-colors">Price Segments Overview</h3>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={charts.price_segments}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" strokeOpacity={0.2} />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 12}} />
              <YAxis axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 12}} />
              <RechartsTooltip content={<CustomTooltip />} cursor={{fill: '#f1f5f9', opacity: 0.1}} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={60}>
                {charts.price_segments.map((entry, index) => <Cell key={index} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="w-full mb-12 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden transition-colors duration-300">
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50 flex justify-between items-center transition-colors">
          <h3 className="font-semibold text-slate-800 dark:text-white transition-colors">Live Activity Log</h3>
          <span className="flex h-2.5 w-2.5 relative">
            <span className="animate-ping absolute h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
        </div>
        <div className="divide-y divide-slate-100 dark:divide-slate-800 transition-colors">
          {logs && logs.map((log, index) => (
            <div key={index} className="px-6 py-4 flex items-start gap-4 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
              <div className={`mt-1.5 w-2.5 h-2.5 rounded-full flex-shrink-0 ${log.type === 'add' ? 'bg-purple-500' : 'bg-emerald-500'}`} />
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300 transition-colors">{log.message}</p>
                <span className="text-xs text-slate-400 dark:text-slate-500 mt-1 block transition-colors">{log.date}</span>
              </div>
            </div>
          ))}
          {(!logs || logs.length === 0) && (
            <div className="px-6 py-6 text-center text-sm text-slate-500 dark:text-slate-400 transition-colors">
              No recent activity.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
