import { useState, useEffect } from 'react';
import { TicketCheck, Clock, ShieldAlert, Sparkles, TrendingUp, TrendingDown, BrainCircuit, ArrowRight, RefreshCw, FileText } from 'lucide-react';
import axios from 'axios';

const StatCard = ({ title, value, icon: Icon, trend, isPositive, color }: any) => (
  <div className="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 group hover:-translate-y-1">
    <div className="flex justify-between items-start">
      <div>
        <p className="text-slate-400 font-semibold text-xs tracking-wider uppercase mb-1">{title}</p>
        <h3 className="text-3xl font-extrabold text-white tracking-tight mt-1">{value}</h3>
      </div>
      <div className={`p-3.5 rounded-2xl ${color} shadow-lg ring-1 ring-white/10 group-hover:scale-110 transition-transform`}>
        <Icon className="w-6 h-6" />
      </div>
    </div>
    <div className="mt-5 flex items-center text-xs font-semibold">
      {isPositive ? (
        <TrendingUp className="w-4 h-4 text-emerald-400 mr-1.5" />
      ) : (
        <TrendingDown className="w-4 h-4 text-rose-400 mr-1.5" />
      )}
      <span className={isPositive ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
        {trend}
      </span>
      <span className="text-slate-500 ml-2 font-normal">vs previous cycle</span>
    </div>
  </div>
);

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_tickets: 0,
    open_tickets: 0,
    ai_resolution_rate: 0,
    avg_resolution_time_hours: 0,
    escalated_tickets: 0
  });
  const [recentTickets, setRecentTickets] = useState<any[]>([]);
  const [knowledgeGaps, setKnowledgeGaps] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = async () => {
    setRefreshing(true);
    try {
      const token = localStorage.getItem('token');
      const authHeader = token ? { Authorization: `Bearer ${token}` } : {};

      // 1. Overview analytics
      let overviewData: any = null;
      try {
        const overviewRes = await axios.get('http://localhost:8000/api/analytics/overview', { headers: authHeader });
        overviewData = overviewRes.data;
      } catch (e) {
        const retryRes = await axios.get('http://localhost:8000/api/analytics/overview').catch(() => null);
        overviewData = retryRes?.data;
      }

      // 2. Recent tickets
      let ticketsData: any[] = [];
      try {
        const ticketsRes = await axios.get('http://localhost:8000/api/tickets/', { headers: authHeader });
        ticketsData = Array.isArray(ticketsRes.data) ? ticketsRes.data : [];
      } catch (e) {
        const retryTickets = await axios.get('http://localhost:8000/api/tickets/').catch(() => null);
        ticketsData = Array.isArray(retryTickets?.data) ? retryTickets.data : [];
      }

      // 3. Knowledge gaps
      let gapsData: any[] = [];
      try {
        const gapsRes = await axios.get('http://localhost:8000/api/knowledge-gaps/', { headers: authHeader });
        gapsData = Array.isArray(gapsRes.data) ? gapsRes.data : [];
      } catch (e) {
        const retryGaps = await axios.get('http://localhost:8000/api/knowledge-gaps/').catch(() => null);
        gapsData = Array.isArray(retryGaps?.data) ? retryGaps.data : [];
      }

      if (overviewData) {
        const openT = ticketsData.filter(t => !['RESOLVED', 'CLOSED'].includes(t.status)).length;
        const escT = ticketsData.filter(t => t.status === 'ESCALATED').length;
        setStats({
          total_tickets: overviewData.total_tickets || ticketsData.length,
          open_tickets: openT > 0 ? openT : (overviewData.open_tickets || 0),
          ai_resolution_rate: Math.round(overviewData.ai_resolution_rate || (ticketsData.length > 0 ? (ticketsData.filter(t => ['RESOLVED', 'CLOSED'].includes(t.status)).length / ticketsData.length) * 100 : 0)),
          avg_resolution_time_hours: overviewData.average_resolution_time_hours || 0.4,
          escalated_tickets: escT > 0 ? escT : (overviewData.escalated_tickets || 0)
        });
      } else if (ticketsData.length > 0) {
        const openT = ticketsData.filter(t => !['RESOLVED', 'CLOSED'].includes(t.status)).length;
        const escT = ticketsData.filter(t => t.status === 'ESCALATED').length;
        const resT = ticketsData.filter(t => ['RESOLVED', 'CLOSED'].includes(t.status)).length;
        const aiRate = ticketsData.length > 0 ? Math.round((resT / ticketsData.length) * 100) : 0;
        setStats({
          total_tickets: ticketsData.length,
          open_tickets: openT,
          ai_resolution_rate: aiRate,
          avg_resolution_time_hours: 0.4,
          escalated_tickets: escT
        });
      }

      setRecentTickets(ticketsData.slice(0, 8));
      setKnowledgeGaps(gapsData);
    } catch (err) {
      console.warn("Dashboard sync warning:", err);
    } finally {
      setTimeout(() => setRefreshing(false), 400);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="glass-panel rounded-3xl p-8 relative overflow-hidden glow-blue">
        <div className="absolute top-[-50%] right-[-10%] w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <div className="inline-flex items-center space-x-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Real-Time IT Engine Active</span>
            </div>
            <h2 className="text-3xl font-extrabold text-white tracking-tight">IT Executive Dashboard</h2>
            <p className="text-slate-400 text-sm mt-1.5 max-w-xl">Live analytics from Zulip channels, RAG vector searches, and employee tickets</p>
          </div>

          <button
            onClick={fetchDashboardData}
            disabled={refreshing}
            className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold px-5 py-3 rounded-2xl shadow-lg shadow-blue-500/20 transition-all text-sm backdrop-blur-md border border-white/10"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? "Syncing..." : "Sync Real-Time Data"}</span>
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Open Tickets" 
          value={stats.open_tickets} 
          icon={TicketCheck} 
          trend="Active" 
          isPositive={true}
          color="bg-blue-500/10 text-blue-400"
        />
        <StatCard 
          title="AI Resolution Rate" 
          value={`${stats.ai_resolution_rate}%`} 
          icon={Sparkles} 
          trend="Live RAG" 
          isPositive={true}
          color="bg-purple-500/10 text-purple-400"
        />
        <StatCard 
          title="Avg. Resolution Time" 
          value={`${stats.avg_resolution_time_hours.toFixed(1)}h`} 
          icon={Clock} 
          trend="Automated" 
          isPositive={true}
          color="bg-emerald-500/10 text-emerald-400"
        />
        <StatCard 
          title="Pending Escalations" 
          value={stats.escalated_tickets} 
          icon={ShieldAlert} 
          trend="Needs IT Review" 
          isPositive={stats.escalated_tickets === 0}
          color="bg-rose-500/10 text-rose-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Activity */}
        <div className="lg:col-span-2 glass-panel rounded-3xl overflow-hidden flex flex-col shadow-xl">
          <div className="p-6 border-b border-slate-800/80 flex justify-between items-center bg-slate-900/40">
            <h3 className="font-bold text-white text-lg tracking-tight">Real-Time AI Activity Feed</h3>
            <span className="text-xs font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">Live Zulip Stream</span>
          </div>
          <div className="p-6 flex-1">
            <div className="space-y-5">
              {recentTickets.length === 0 ? (
                <div className="text-center py-16 text-slate-500 text-sm">
                  <FileText className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                  No tickets logged yet. Post a message on Zulip to see live feed.
                </div>
              ) : (
                recentTickets.map((t, i) => (
                  <div key={t.id || i} className="glass-card p-4 rounded-2xl flex items-start space-x-4 transition-all hover:bg-slate-800/50">
                    <div className={`mt-1.5 w-3 h-3 rounded-full flex-shrink-0 shadow-lg ${t.status === 'RESOLVED' ? 'bg-emerald-400 shadow-emerald-500/50' : t.status === 'ESCALATED' ? 'bg-rose-500 shadow-rose-500/50' : 'bg-amber-400 shadow-amber-500/50'}`}></div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-bold text-white truncate">
                          {t.ticket_number} <span className="font-normal text-slate-400">— {t.user_name || t.user_email || 'Zulip User'}</span>
                        </p>
                        {t.visibility === 'CONFIDENTIAL' && (
                          <span className="text-[10px] font-bold text-purple-300 bg-purple-500/20 border border-purple-500/30 px-2 py-0.5 rounded-full">
                            🔒 Confidential
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-300 mt-1 line-clamp-1">{t.title}</p>
                      <p className="text-[11px] text-slate-500 mt-1.5 font-medium">
                        {t.created_at ? new Date(t.created_at).toLocaleString() : 'Just now'} • Source: {t.resolution_source || 'AI Ingestion'}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Knowledge Gaps */}
        <div className="glass-panel rounded-3xl overflow-hidden flex flex-col relative shadow-xl glow-purple">
          <div className="p-6 border-b border-slate-800/80 bg-slate-900/40">
            <h3 className="font-bold text-white text-lg flex items-center tracking-tight">
              <BrainCircuit className="w-5 h-5 mr-2 text-purple-400" />
              Detected Knowledge Gaps
            </h3>
            <p className="text-slate-400 text-xs mt-1">Topics AI couldn't resolve from current protocols.</p>
          </div>
          
          <div className="p-6 space-y-4">
            {knowledgeGaps.length === 0 ? (
              <div className="bg-slate-900/60 rounded-2xl p-6 border border-slate-800 text-slate-400 text-xs text-center leading-relaxed">
                No knowledge gaps detected. All employee questions successfully resolved.
              </div>
            ) : (
              knowledgeGaps.map((gap, i) => (
                <div key={gap.id || i} className="glass-card rounded-2xl p-4 flex items-center justify-between group hover:bg-slate-800/80 transition-all cursor-pointer border-slate-800">
                  <div>
                    <h4 className="text-white font-semibold text-sm">{gap.topic_summary || gap.query_text}</h4>
                    <p className="text-xs font-bold text-purple-400 mt-1">{gap.occurrence_count || 1} occurrences</p>
                  </div>
                  <div className="w-9 h-9 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center group-hover:bg-purple-600 group-hover:text-white transition-all shadow-md">
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
