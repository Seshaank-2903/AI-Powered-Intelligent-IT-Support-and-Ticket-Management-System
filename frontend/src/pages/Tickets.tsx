import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  MessageSquare, 
  CheckCircle2, 
  X, 
  BrainCircuit, 
  Send, 
  ShieldAlert, 
  Loader2, 
  ChevronRight, 
  Clock, 
  RefreshCw, 
  UserCheck, 
  Check, 
  Lock, 
  FileText,
  Building,
  Mail
} from 'lucide-react';
import clsx from 'clsx';
import axios from 'axios';

interface MessageItem {
  id: string;
  sender_type: string;
  sender_id?: string;
  message: string;
  source?: string;
  created_at?: string;
}

interface TicketItem {
  id: string;
  ticket_number: string;
  user_name?: string;
  user_email?: string;
  title: string;
  category?: string;
  description?: string;
  status: string;
  priority?: string;
  visibility?: string;
  resolution_source?: string;
  created_at: string;
  closed_at?: string;
}

const Tickets = () => {
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Selected Ticket & Message Drawer State
  const [selectedTicket, setSelectedTicket] = useState<TicketItem | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [adminReply, setAdminReply] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Fetch Tickets from Backend API
  const fetchTickets = async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    try {
      const token = localStorage.getItem('token');
      let resData = null;
      try {
        const res = await axios.get('http://localhost:8000/api/tickets/', {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        resData = res.data;
      } catch (e) {
        const retryRes = await axios.get('http://localhost:8000/api/tickets/').catch(() => null);
        resData = retryRes?.data;
      }

      if (Array.isArray(resData)) {
        setTickets(resData);
      }
    } catch (err) {
      console.warn("API Tickets fetch warning:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTickets();
    // Auto-refresh tickets every 5 seconds for real-time monitoring
    const interval = setInterval(() => {
      fetchTickets();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch Messages for Selected Ticket
  const fetchMessages = async (ticketId: string) => {
    setLoadingMessages(true);
    try {
      const token = localStorage.getItem('token');
      let msgsData = null;
      try {
        const res = await axios.get(`http://localhost:8000/api/tickets/${ticketId}/messages`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        msgsData = res.data;
      } catch (e) {
        const retryRes = await axios.get(`http://localhost:8000/api/tickets/${ticketId}/messages`).catch(() => null);
        msgsData = retryRes?.data;
      }

      if (Array.isArray(msgsData)) {
        setMessages(msgsData);
      } else {
        setMessages([]);
      }
    } catch (err) {
      console.warn("Error fetching ticket messages:", err);
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleSelectTicket = (ticket: TicketItem) => {
    setSelectedTicket(ticket);
    fetchMessages(ticket.id);
  };

  // IT Admin Action: Mark Ticket Resolved
  const handleMarkResolved = async () => {
    if (!selectedTicket) return;
    setActionLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`http://localhost:8000/api/tickets/${selectedTicket.id}/resolve`, {}, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      setTickets(prev => prev.map(t => t.id === selectedTicket.id ? { ...t, status: 'RESOLVED' } : t));
      setSelectedTicket(prev => prev ? { ...prev, status: 'RESOLVED' } : null);
    } catch (err) {
      console.error("Error marking ticket resolved:", err);
    } finally {
      setActionLoading(false);
    }
  };

  // IT Admin Action: Close Ticket
  const handleCloseTicket = async () => {
    if (!selectedTicket) return;
    setActionLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`http://localhost:8000/api/tickets/${selectedTicket.id}/close`, {}, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      setTickets(prev => prev.map(t => t.id === selectedTicket.id ? { ...t, status: 'CLOSED' } : t));
      setSelectedTicket(prev => prev ? { ...prev, status: 'CLOSED' } : null);
    } catch (err) {
      console.error("Error closing ticket:", err);
    } finally {
      setActionLoading(false);
    }
  };

  // IT Admin Action: Post Direct Specialist Reply
  const handleSendAdminReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminReply.trim() || !selectedTicket) return;

    setActionLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`http://localhost:8000/api/tickets/${selectedTicket.id}/messages`, {
        message: adminReply,
        sender_type: 'IT_AGENT',
        sender_id: 'IT_ADMIN'
      }, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });

      if (res.data) {
        setMessages(prev => [...prev, res.data]);
        setAdminReply('');
      }
    } catch (err) {
      console.error("Error posting IT admin reply:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RESOLVED': 
        return <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center w-fit"><CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-emerald-400" /> RESOLVED</span>;
      case 'CLOSED': 
        return <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-slate-800 text-slate-400 border border-slate-700 flex items-center w-fit"><Lock className="w-3.5 h-3.5 mr-1.5 text-slate-400" /> CLOSED</span>;
      case 'ESCALATED': 
        return <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center w-fit"><ShieldAlert className="w-3.5 h-3.5 mr-1.5 text-rose-400" /> ESCALATED TO IT</span>;
      case 'WAITING_FOR_USER': 
        return <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center w-fit"><Clock className="w-3.5 h-3.5 mr-1.5 text-amber-400" /> WAITING FOR USER</span>;
      case 'PROTOCOL_ATTEMPTED':
      case 'AI_ASSISTED':
        return <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center w-fit"><BrainCircuit className="w-3.5 h-3.5 mr-1.5 text-purple-400" /> AI ASSISTED</span>;
      case 'IT_IN_PROGRESS':
        return <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center w-fit"><UserCheck className="w-3.5 h-3.5 mr-1.5 text-indigo-400" /> IT IN PROGRESS</span>;
      default: 
        return <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center w-fit"><BrainCircuit className="w-3.5 h-3.5 mr-1.5 text-blue-400" /> AI PROCESSING</span>;
    }
  };

  const getPriorityBadge = (priority: string = 'MEDIUM') => {
    switch (priority.toUpperCase()) {
      case 'URGENT': return <span className="text-[10px] font-extrabold text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-lg border border-rose-500/20">URGENT</span>;
      case 'HIGH': return <span className="text-[10px] font-extrabold text-orange-400 bg-orange-500/10 px-2.5 py-1 rounded-lg border border-orange-500/20">HIGH</span>;
      case 'MEDIUM': return <span className="text-[10px] font-bold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-lg border border-blue-500/20">MEDIUM</span>;
      default: return <span className="text-[10px] font-medium text-slate-400 bg-slate-800 px-2.5 py-1 rounded-lg">LOW</span>;
    }
  };

  // Filtered Tickets
  const filteredTickets = tickets.filter(t => {
    const status = t.status ? t.status.toUpperCase() : 'NEW';
    const matchesTab = 
      activeTab === 'all' ? true :
      activeTab === 'open' ? (['NEW', 'WAITING_FOR_USER', 'CLASSIFYING', 'PROTOCOL_SEARCH', 'PROTOCOL_ATTEMPTED', 'AI_ASSISTED', 'IT_IN_PROGRESS'].includes(status)) :
      activeTab === 'escalated' ? status === 'ESCALATED' :
      activeTab === 'resolved' ? (status === 'RESOLVED' || status === 'CLOSED') : true;

    const matchesSearch = 
      t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (t.user_name && t.user_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (t.user_email && t.user_email.toLowerCase().includes(searchQuery.toLowerCase())) ||
      t.ticket_number.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesTab && matchesSearch;
  });

  const openCount = tickets.filter(t => ['NEW', 'WAITING_FOR_USER', 'CLASSIFYING', 'PROTOCOL_SEARCH', 'PROTOCOL_ATTEMPTED', 'AI_ASSISTED', 'IT_IN_PROGRESS'].includes(t.status)).length;
  const escalatedCount = tickets.filter(t => t.status === 'ESCALATED').length;
  const resolvedCount = tickets.filter(t => ['RESOLVED', 'CLOSED'].includes(t.status)).length;

  return (
    <div className="space-y-6">
      
      {/* Admin Console Top Header Bar */}
      <div className="glass-panel rounded-3xl p-8 relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-6 shadow-xl glow-blue">
        <div className="absolute top-[-50%] right-[-10%] w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10">
          <div className="inline-flex items-center space-x-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase mb-3">
            <UserCheck className="w-3.5 h-3.5 text-blue-400" />
            <span>IT Admin Audit Console</span>
          </div>
          <h2 className="text-3xl font-extrabold text-white tracking-tight">Support Ticket Audit & Monitoring</h2>
          <p className="text-slate-400 text-sm mt-1.5">Real-time tickets raised by employees via Zulip chat and API integrations</p>
        </div>

        <div className="relative z-10 flex items-center space-x-3">
          <button 
            onClick={() => fetchTickets(true)}
            disabled={refreshing}
            className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold px-5 py-3 rounded-2xl shadow-lg shadow-blue-500/20 transition-all text-sm backdrop-blur-md border border-white/10"
          >
            <RefreshCw className={clsx("w-4 h-4", refreshing && "animate-spin")} />
            <span>{refreshing ? "Refreshing..." : "Refresh Live"}</span>
          </button>
        </div>
      </div>

      {/* Metrics Summary Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card rounded-2xl p-5 border-slate-800">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Tickets</p>
          <p className="text-3xl font-extrabold text-white mt-1">{tickets.length}</p>
        </div>
        <div className="glass-card rounded-2xl p-5 border-amber-500/20 bg-amber-500/5">
          <p className="text-xs font-bold uppercase tracking-wider text-amber-400">Open & Active</p>
          <p className="text-3xl font-extrabold text-amber-300 mt-1">{openCount}</p>
        </div>
        <div className="glass-card rounded-2xl p-5 border-rose-500/20 bg-rose-500/5">
          <p className="text-xs font-bold uppercase tracking-wider text-rose-400">Pending Escalations</p>
          <p className="text-3xl font-extrabold text-rose-300 mt-1">{escalatedCount}</p>
        </div>
        <div className="glass-card rounded-2xl p-5 border-emerald-500/20 bg-emerald-500/5">
          <p className="text-xs font-bold uppercase tracking-wider text-emerald-400">Resolved / Closed</p>
          <p className="text-3xl font-extrabold text-emerald-300 mt-1">{resolvedCount}</p>
        </div>
      </div>

      {/* Tickets Table Container */}
      <div className="glass-panel rounded-3xl shadow-xl overflow-hidden flex flex-col min-h-[500px]">
        {/* Filter Tabs & Search Bar */}
        <div className="p-6 border-b border-slate-800/80 bg-slate-900/40">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex space-x-1 bg-slate-900/80 p-1.5 rounded-2xl border border-slate-800">
              {[
                { id: 'all', label: 'All Tickets' },
                { id: 'open', label: `Open (${openCount})` },
                { id: 'escalated', label: `Escalated (${escalatedCount})` },
                { id: 'resolved', label: `Resolved (${resolvedCount})` }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={clsx(
                    "px-4 py-2 text-xs font-bold rounded-xl transition-all",
                    activeTab === tab.id 
                      ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20" 
                      : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="flex items-center space-x-3 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-72">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 transform -translate-y-1/2 text-slate-400" />
                <input 
                  type="text" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search ticket #, employee..." 
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/80 border border-slate-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all text-xs text-white placeholder:text-slate-500"
                />
              </div>
              <button 
                onClick={() => fetchTickets(true)}
                className="p-2.5 bg-slate-900/80 border border-slate-800 rounded-2xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
                title="Filter & Refresh"
              >
                <Filter className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Tickets Data Table */}
        <div className="flex-1 overflow-x-auto">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-24 text-slate-400 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <p className="text-sm font-semibold">Loading live support tickets...</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/60 border-b border-slate-800 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="px-6 py-4">Ticket ID</th>
                  <th className="px-6 py-4">Employee</th>
                  <th className="px-6 py-4">Issue Request</th>
                  <th className="px-6 py-4">Priority</th>
                  <th className="px-6 py-4">AI Ingestion</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Audit Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {filteredTickets.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-20 text-slate-500 text-sm">
                      <FileText className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                      No tickets found matching your search criteria.
                    </td>
                  </tr>
                ) : (
                  filteredTickets.map((ticket) => (
                    <tr 
                      key={ticket.id} 
                      onClick={() => handleSelectTicket(ticket)}
                      className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-white text-xs tracking-tight">{ticket.ticket_number}</span>
                          {ticket.visibility === 'CONFIDENTIAL' && (
                            <span className="text-[10px] font-bold text-purple-300 bg-purple-500/20 border border-purple-500/30 px-2 py-0.5 rounded-full inline-flex items-center">
                              🔒 Confidential
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-1 font-medium">
                          {ticket.created_at ? new Date(ticket.created_at).toLocaleString() : 'Recent'}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 flex items-center justify-center font-bold text-xs flex-shrink-0">
                            {(ticket.user_name || ticket.user_email || 'Emp').charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-bold text-white text-xs">{ticket.user_name || 'Employee'}</p>
                            <p className="text-[10px] text-slate-400 font-medium">{ticket.user_email || 'via Zulip'}</p>
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4 max-w-xs">
                        <span className="text-slate-200 font-semibold text-xs line-clamp-1">{ticket.title}</span>
                        <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5 font-normal">{ticket.description || 'Zulip support ticket'}</p>
                      </td>

                      <td className="px-6 py-4">
                        {getPriorityBadge(ticket.priority)}
                      </td>

                      <td className="px-6 py-4">
                        {ticket.resolution_source === 'PROTOCOL' ? (
                          <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full inline-flex items-center">
                            <CheckCircle2 className="w-3 h-3 mr-1" /> RAG Protocol
                          </span>
                        ) : ticket.resolution_source === 'MISTRAL' ? (
                          <span className="text-[10px] font-semibold text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2.5 py-1 rounded-full inline-flex items-center">
                            <BrainCircuit className="w-3 h-3 mr-1" /> AI Model
                          </span>
                        ) : (
                          <span className="text-[10px] font-medium text-slate-400 bg-slate-800 px-2.5 py-1 rounded-full">
                            Pending
                          </span>
                        )}
                      </td>

                      <td className="px-6 py-4">
                        {getStatusBadge(ticket.status)}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectTicket(ticket);
                          }}
                          className="inline-flex items-center space-x-1.5 text-xs font-bold text-blue-400 hover:text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 px-3.5 py-2 rounded-xl transition-all"
                        >
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span>Audit Log</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* IT Admin Audit Log & Chat Drawer */}
      {selectedTicket && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="bg-[#0f172a] w-full max-w-2xl h-full shadow-2xl flex flex-col border-l border-slate-800 animate-in slide-in-from-right duration-300">
            
            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-800 flex justify-between items-start bg-slate-900/90 backdrop-blur-xl text-white">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-blue-400 text-sm">{selectedTicket.ticket_number}</span>
                  {getStatusBadge(selectedTicket.status)}
                </div>
                <h3 className="font-bold text-white text-lg mt-1">{selectedTicket.title}</h3>
                
                <div className="flex items-center space-x-4 text-xs text-slate-400 mt-2">
                  <span className="flex items-center"><Mail className="w-3.5 h-3.5 mr-1 text-slate-500" /> {selectedTicket.user_email || 'Zulip User'}</span>
                  <span className="flex items-center"><Building className="w-3.5 h-3.5 mr-1 text-slate-500" /> Acme Corp</span>
                </div>
              </div>
              
              <button 
                onClick={() => setSelectedTicket(null)}
                className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Admin Action Control Strip */}
            <div className="p-4 bg-slate-900/40 border-b border-slate-800 flex items-center justify-between gap-3">
              <span className="text-xs font-bold text-slate-300">IT Admin Ticket Controls:</span>
              <div className="flex items-center space-x-2">
                {selectedTicket.status !== 'RESOLVED' && (
                  <button
                    onClick={handleMarkResolved}
                    disabled={actionLoading}
                    className="inline-flex items-center space-x-1 text-xs font-bold text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 px-3.5 py-1.5 rounded-xl transition-all disabled:opacity-50"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Mark Resolved</span>
                  </button>
                )}
                {selectedTicket.status !== 'CLOSED' && (
                  <button
                    onClick={handleCloseTicket}
                    disabled={actionLoading}
                    className="inline-flex items-center space-x-1 text-xs font-bold text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3.5 py-1.5 rounded-xl transition-all disabled:opacity-50"
                  >
                    <Lock className="w-3.5 h-3.5" />
                    <span>Close Ticket</span>
                  </button>
                )}
              </div>
            </div>

            {/* Message Stream & Conversation History */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-[#0b0f19]/80">
              {loadingMessages ? (
                <div className="flex items-center justify-center py-16 text-slate-500 space-y-2">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                </div>
              ) : messages.length === 0 ? (
                <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 text-slate-400 text-xs leading-relaxed space-y-2">
                  <p className="font-bold text-white text-sm">Issue Description:</p>
                  <p>{selectedTicket.description || selectedTicket.title}</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div 
                    key={msg.id}
                    className={clsx(
                      "flex flex-col max-w-[85%] space-y-1",
                      msg.sender_type === 'USER' ? "ml-auto items-end" : "mr-auto items-start"
                    )}
                  >
                    <div className="flex items-center space-x-2 px-1">
                      <span className="text-xs font-bold text-slate-400">
                        {msg.sender_type === 'USER' ? selectedTicket.user_name || 'Employee' : msg.sender_type === 'BOT' ? 'Nexus AI' : 'IT Specialist'}
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : 'Just now'}
                      </span>
                    </div>
                    
                    <div 
                      className={clsx(
                        "p-4 rounded-2xl text-xs leading-relaxed shadow-sm border",
                        msg.sender_type === 'USER' 
                          ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white border-blue-500/30 rounded-tr-none" 
                          : msg.sender_type === 'BOT'
                          ? "bg-slate-900 border-slate-800 text-slate-200 rounded-tl-none"
                          : "bg-emerald-600/90 text-white border-emerald-500/30 rounded-tl-none"
                      )}
                    >
                      <p className="whitespace-pre-wrap">{msg.message}</p>
                      {msg.source && (
                        <div className="mt-2 pt-2 border-t border-white/10 text-[10px] font-bold text-blue-300">
                          Source: {msg.source}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* IT Specialist Direct Response Form */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/90">
              <form onSubmit={handleSendAdminReply} className="flex items-center space-x-2">
                <input 
                  type="text"
                  value={adminReply}
                  onChange={(e) => setAdminReply(e.target.value)}
                  placeholder="Type official IT Specialist response..."
                  className="flex-1 px-4 py-3 bg-slate-950 border border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 text-xs text-white placeholder-slate-500"
                />
                <button
                  type="submit"
                  disabled={!adminReply.trim() || actionLoading}
                  className="p-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl shadow-lg transition-all disabled:opacity-40"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tickets;
