import React from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Ticket, 
  FileText, 
  LogOut,
  BrainCircuit,
  ShieldCheck
} from 'lucide-react';
import clsx from 'clsx';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Tickets from './pages/Tickets';
import Protocols from './pages/Protocols';

const SidebarItem = ({ icon: Icon, label, path, active }: any) => {
  const navigate = useNavigate();
  return (
    <button 
      onClick={() => navigate(path)}
      className={clsx(
        "w-full flex items-center space-x-3 px-4 py-3.5 rounded-xl transition-all duration-200 group font-semibold text-sm",
        active 
          ? "bg-gradient-to-r from-blue-600/20 to-indigo-600/20 text-blue-400 border border-blue-500/30 shadow-lg shadow-blue-500/10" 
          : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
      )}
    >
      <Icon className={clsx("w-5 h-5 transition-transform group-hover:scale-110", active ? "text-blue-400" : "text-slate-500 group-hover:text-slate-300")} />
      <span>{label}</span>
    </button>
  );
};

const Layout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const getPageTitle = () => {
    const p = location.pathname.split('/')[1];
    if (p === 'tickets') return 'Ticket Management & Audit';
    if (p === 'protocols') return 'Knowledge Base & AI Ingestion';
    return 'Executive Overview';
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex selection:bg-blue-600 selection:text-white">
      {/* Sidebar */}
      <aside className="w-72 bg-[#0f172a]/90 backdrop-blur-xl border-r border-slate-800/80 flex flex-col fixed h-full z-20 shadow-2xl">
        <div className="h-20 flex items-center px-6 border-b border-slate-800/80 justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25 ring-1 ring-white/20">
              <BrainCircuit className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-extrabold text-white text-base tracking-tight leading-tight">Nexus AI</h1>
              <p className="text-[10px] font-bold text-blue-400 tracking-wider uppercase">IT SUPPORT HUB</p>
            </div>
          </div>
          <span className="flex h-2 w-2 relative" title="Live Zulip Engine Connected">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          <SidebarItem icon={LayoutDashboard} label="Dashboard" path="/dashboard" active={location.pathname === '/dashboard'} />
          <SidebarItem icon={Ticket} label="Tickets" path="/tickets" active={location.pathname.startsWith('/tickets')} />
          <SidebarItem icon={FileText} label="Protocols & AI" path="/protocols" active={location.pathname.startsWith('/protocols')} />
        </nav>

        <div className="p-4 border-t border-slate-800/80">
          <button 
            onClick={() => navigate('/login')}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-all duration-200 border border-rose-500/20 font-semibold text-sm"
          >
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 ml-72 flex flex-col min-h-screen">
        {/* Top Navbar */}
        <header className="h-20 bg-[#0f172a]/70 backdrop-blur-xl border-b border-slate-800/80 flex items-center justify-between px-8 sticky top-0 z-10">
          <div className="flex items-center space-x-3">
            <h2 className="text-xl font-bold text-white tracking-tight">
              {getPageTitle()}
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center">
              <ShieldCheck className="w-3 h-3 mr-1 text-blue-400" />
              ZULIP REAL-TIME ACTIVE
            </span>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3 bg-slate-900/80 border border-slate-800 px-4 py-2 rounded-2xl shadow-inner">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-md">
                AD
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-xs font-bold text-white leading-tight">Admin User</p>
                <p className="text-[10px] font-medium text-slate-400">Acme Corp IT</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-8 overflow-x-hidden">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
      <Route path="/tickets" element={<Layout><Tickets /></Layout>} />
      <Route path="/protocols" element={<Layout><Protocols /></Layout>} />
      {/* Fallbacks */}
      <Route path="*" element={<Layout><div className="text-center py-20 text-slate-400">Page under construction</div></Layout>} />
    </Routes>
  );
};

export default App;
