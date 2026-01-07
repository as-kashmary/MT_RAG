// 



import React, { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { 
  MessageSquare, Plus, Search, Settings, LogOut, Moon, Sun, Menu, X, 
  ChevronDown, Box, Cpu, Database, FileText, Bot, Check, ArrowUp, 
  AlertTriangle, Eye, EyeOff, Loader, RefreshCw, Cloud, Shield, Code
} from 'lucide-react';

// IMPORT API LAYER
import { authAPI, productAPI, chatAPI, historyAPI, sessionManager } from './api';

/**
 * Constants & Helpers
 */
const COMPANY_ID = "1893ab51e6284c1b8ed64c88238b116b";

const UI_VARIANTS = [
  { icon: Database, color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-900/20', activeBg: 'bg-emerald-500' },
  { icon: FileText, color: 'text-orange-500', bg: 'bg-orange-50 dark:bg-orange-900/20', activeBg: 'bg-orange-500' },
  { icon: Cpu, color: 'text-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20', activeBg: 'bg-purple-500' },
  { icon: Cloud, color: 'text-sky-500', bg: 'bg-sky-50 dark:bg-sky-900/20', activeBg: 'bg-sky-500' },
  { icon: Shield, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20', activeBg: 'bg-red-500' },
  { icon: Code, color: 'text-pink-500', bg: 'bg-pink-50 dark:bg-pink-900/20', activeBg: 'bg-pink-500' },
];

const getInitials = (name) => {
  if (!name) return 'U';
  const parts = name.trim().split(' ');
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

// --- RESTORED: Date Grouping Logic ---
const getDateLabel = (dateString) => {
  if (!dateString) return 'Older';
  const date = new Date(dateString);
  const now = new Date();
  
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const sevenDaysAgo = new Date(today);
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

  if (date >= today) return 'Today';
  if (date >= yesterday) return 'Yesterday';
  if (date >= sevenDaysAgo) return 'Previous 7 Days';
  return 'Older';
};

const TIME_CATEGORIES = ['Today', 'Yesterday', 'Previous 7 Days', 'Older'];

// --- UI Components ---
const Button = ({ children, onClick, variant = 'primary', className = '', ...props }) => {
  const baseStyle = "px-4 py-2.5 rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-gradient-to-tr from-blue-500 to-purple-500 text-white hover:from-blue-600 hover:to-purple-600 shadow-md shadow-blue-500/20",
    secondary: "bg-zinc-100 text-zinc-900 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-100 dark:hover:bg-zinc-700",
    outline: "border border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
  };
  return <button onClick={onClick} className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>{children}</button>;
};

const Input = ({ label, type = "text", placeholder, className = "", ...props }) => {
  const [currentType, setCurrentType] = useState(type);
  return (
    <div className="flex flex-col gap-2 w-full">
      {label && <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">{label}</label>}
      <div className="relative">
        <input 
          type={currentType} 
          placeholder={placeholder}
          className={`w-full px-3 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 focus:border-blue-500 dark:focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all placeholder:text-zinc-400 text-zinc-900 dark:text-zinc-100 ${className} ${type === 'password' ? 'pr-10' : ''}`}
          {...props}
        />
        {type === 'password' && (
          <button
            type="button"
            onMouseDown={() => setCurrentType('text')}
            onMouseUp={() => setCurrentType('password')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 p-1"
          >
            {currentType === 'text' ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * MAIN APP
 */
export default function App() {
  // --- 1. AUTH STATE (FIXED: Correctly loads from Storage on Refresh) ---
  const [isAuthenticated, setIsAuthenticated] = useState(() => sessionManager.isAuthenticated());
  const [user, setUser] = useState(() => {
    const session = sessionManager.getSession();
    return session ? { ...session, initials: getInitials(session.name) } : { name: 'User', email: '', userId: null, initials: 'U' };
  });

  // Since we check auth synchronously above, we set 'dashboard' immediately if valid
  const [currentPage, setCurrentPage] = useState(() => sessionManager.isAuthenticated() ? 'dashboard' : 'login');
  
  const [authError, setAuthError] = useState('');
  const [isAuthLoading, setIsAuthLoading] = useState(false);

  // --- UI State ---
  const [isDarkMode, setIsDarkMode] = useState(() => JSON.parse(localStorage.getItem('rag_dark_mode') || 'false'));
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [showProductMenu, setShowProductMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showContextWarning, setShowContextWarning] = useState(false);

  // --- DATA STATE ---
  const [messages, setMessages] = useState([]);
  const [historyList, setHistoryList] = useState([]); // Raw list from DB
  const [activeChatId, setActiveChatId] = useState(null); 
  const [isLoadingHistory, setIsLoadingHistory] = useState(false); 
  const [isFetchingOldMessages, setIsFetchingOldMessages] = useState(false); 

  // Product State
  const [products, setProducts] = useState([]);
  const [isProductsLoading, setIsProductsLoading] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [pendingProduct, setPendingProduct] = useState(null);

  // Inputs
  const [inputValue, setInputValue] = useState('');
  const [searchQuery, setSearchQuery] = useState(''); // RESTORED: Sidebar Search
  const [productSearchQuery, setProductSearchQuery] = useState('');
  const [isThinking, setIsThinking] = useState(false);

  // Refs
  const messagesContainerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const userMenuRef = useRef(null);      // RESTORED: Click Outside
  const productMenuRef = useRef(null);   // RESTORED: Click Outside

  // ---------------------------------------------------------
  // RESTORED: Click Outside Handler
  // ---------------------------------------------------------
  useEffect(() => {
    const handleClickOutside = (event) => {
      // Close User Menu
      if (showUserMenu && userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
      // Close Product Menu
      if (showProductMenu && productMenuRef.current && !productMenuRef.current.contains(event.target)) {
        setShowProductMenu(false);
        setProductSearchQuery('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showUserMenu, showProductMenu]);


  // ---------------------------------------------------------
  // INITIAL DATA LOADING
  // ---------------------------------------------------------
  useEffect(() => {
    if (isAuthenticated && user.userId) {
      // Load History
      setIsLoadingHistory(true);
      historyAPI.getSessions(user.userId)
        .then(data => setHistoryList(data))
        .catch(console.error)
        .finally(() => setIsLoadingHistory(false));
      
      // Load Products
      setIsProductsLoading(true);
      productAPI.listByCompany(COMPANY_ID)
        .then(data => {
          const formatted = data.map((p, i) => ({
            id: p.id,
            name: p.name,
            description: p.description,
            ...UI_VARIANTS[i % UI_VARIANTS.length]
          }));
          setProducts(formatted);
        })
        .catch(() => setProducts([]))
        .finally(() => setIsProductsLoading(false));
    }
  }, [isAuthenticated, user.userId]); // Only runs when user is valid

  // Dark Mode
  useLayoutEffect(() => {
    const html = document.documentElement;
    isDarkMode ? html.classList.add('dark') : html.classList.remove('dark');
    localStorage.setItem('rag_dark_mode', JSON.stringify(isDarkMode));
  }, [isDarkMode]);


  // ---------------------------------------------------------
  // CHAT LOGIC (Infinite Scroll & Messaging)
  // ---------------------------------------------------------
  
  // Auto-scroll for new messages
  useEffect(() => {
    if (!isFetchingOldMessages) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isThinking]);

  const handleScroll = async (e) => {
    const { scrollTop } = e.target;
    if (scrollTop === 0 && activeChatId && !isFetchingOldMessages) {
      setIsFetchingOldMessages(true);
      try {
        const oldMessages = await historyAPI.getMessages(activeChatId, 20, messages.length);
        if (oldMessages.length > 0) {
          const currentScrollHeight = e.target.scrollHeight;
          setMessages(prev => [...oldMessages, ...prev]);
          requestAnimationFrame(() => {
             if(messagesContainerRef.current) {
                messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight - currentScrollHeight;
             }
          });
        }
      } catch (err) {
        console.error("Failed to load old messages", err);
      } finally {
        setIsFetchingOldMessages(false);
      }
    }
  };

  const handleStartNewChat = () => {
    setMessages([]);
    setActiveChatId(null);
    setSelectedProduct(null);
    setInputValue('');
    setIsThinking(false);
    if (window.innerWidth < 768) setIsSidebarOpen(false);
  };

  // const handleLoadChat = async (session) => {
  //   setActiveChatId(session.id);
  //   setMessages([]);
  //   setIsThinking(true);
    
  //   // Context Switch Logic
  //   const matchedProduct = products.find(p => p.id === session.product_id);
  //   setSelectedProduct(matchedProduct || null);

  //   try {
  //     const dbMessages = await historyAPI.getMessages(session.id);
  //     setMessages(dbMessages);
  //   } catch (err) {
  //     setMessages([{ id: 'err', role: 'assistant', content: 'Failed to load conversation history.' }]);
  //   } finally {
  //     setIsThinking(false);
  //     if (window.innerWidth < 768) setIsSidebarOpen(false);
  //   }
  // };


  const handleLoadChat = async (session) => {
    setActiveChatId(session.id);
    setSearchQuery(''); // <--- ADD THIS LINE (Exits search view)
    
    setMessages([]);
    setIsThinking(true);
    
    // Context Switch Logic
    const matchedProduct = products.find(p => p.id === session.product_id);
    setSelectedProduct(matchedProduct || null);

    try {
      const dbMessages = await historyAPI.getMessages(session.id);
      setMessages(dbMessages);
    } catch (err) {
      setMessages([{ id: 'err', role: 'assistant', content: 'Failed to load conversation history.' }]);
    } finally {
      setIsThinking(false);
      if (window.innerWidth < 768) setIsSidebarOpen(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const currentInput = inputValue;
    const tempId = Date.now();
    
    setMessages(prev => [...prev, { id: tempId, role: 'user', content: currentInput }]);
    setInputValue('');
    setIsThinking(true);

    try {
      const response = await chatAPI.sendMessage({
        userId: user.userId,
        productId: selectedProduct ? selectedProduct.id : "default",
        sessionId: activeChatId, 
        message: currentInput
      });

      if (!activeChatId && response.sessionId) {
        setActiveChatId(response.sessionId);
        // Optimistically add to history list at the top
        setHistoryList(prev => [{
            id: response.sessionId,
            title: currentInput.substring(0, 30) + (currentInput.length > 30 ? "..." : ""),
            updated_at: new Date().toISOString(),
            // Ensure product info is attached for filtering logic
            product_id: selectedProduct?.id
        }, ...prev]);
      }

      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: 'assistant', 
        content: response.content 
      }]);

    } catch (error) {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        role: 'assistant', 
        content: "⚠️ Network Error. Message not saved." 
      }]);
    } finally {
      setIsThinking(false);
    }
  };


  // ---------------------------------------------------------
  // AUTH & MENU HANDLERS
  // ---------------------------------------------------------
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    setIsAuthLoading(true);
    const formData = new FormData(e.currentTarget);
    
    try {
      if (currentPage === 'register') {
        const password = formData.get('password');
        if (password !== formData.get('confirmPassword')) throw new Error('Passwords do not match.');
        await authAPI.signup({ name: formData.get('fullName'), email: formData.get('email'), password });
        setCurrentPage('login');
        alert('Signup successful!');
      } else {
        const result = await authAPI.login(formData.get('email'), formData.get('password'));
        if (result.success) {
          const userData = { ...result, initials: getInitials(result.name) };
          sessionManager.saveSession(userData);
          setUser(userData);
          setIsAuthenticated(true);
          setCurrentPage('dashboard');
          chatAPI.warmup(result.userId);
        } else {
          throw new Error(result.message);
        }
      }
    } catch (error) {
      setAuthError(error.message);
    } finally {
      setIsAuthLoading(false);
    }
  };

  const handleLogout = () => {
    sessionManager.clearSession();
    setIsAuthenticated(false);
    setCurrentPage('login'); // Force switch back to login
    
    // UI Cleanup (Fix for erratic menus)
    setShowUserMenu(false);
    setShowProductMenu(false);
    setShowSettings(false);
    setIsSidebarOpen(false);
    
    // Data Cleanup
    setMessages([]);
    setHistoryList([]);
    setActiveChatId(null);
    setUser({ name: 'User', email: '', userId: null, initials: 'U' });
  };

  const handleProductSelect = (product) => {
    if (activeChatId && selectedProduct?.id !== product.id) {
       setPendingProduct(product);
       setShowContextWarning(true);
       setShowProductMenu(false);
    } else {
       setSelectedProduct(product);
       setShowProductMenu(false);
       setTimeout(() => inputRef.current?.focus(), 0);
    }
    setProductSearchQuery('');
  };

  const confirmContextSwitch = () => {
    handleStartNewChat();
    setSelectedProduct(pendingProduct);
    setPendingProduct(null);
    setShowContextWarning(false);
  };

  // ---------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------
  return (
    <>
      {/* LOGIN / REGISTER */}
      {(currentPage === 'login' || currentPage === 'register') && (
        <div className="min-h-screen flex items-center justify-center bg-zinc-50 dark:bg-zinc-950 px-4">
          <div className="w-full max-w-md bg-white dark:bg-zinc-900 rounded-2xl shadow-xl border border-zinc-100 dark:border-zinc-800 overflow-hidden">
            <div className="p-8">
              <div className="flex justify-center mb-8">
                <div className="w-12 h-12 bg-gradient-to-tr from-blue-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg">
                  <Bot className="w-6 h-6 text-white" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-center dark:text-white mb-2">{currentPage === 'login' ? 'Welcome Back' : 'Create Account'}</h2>
              
              <form onSubmit={handleLogin} className="space-y-4 mt-8">
                {currentPage === 'register' && <Input name="fullName" label="Full Name" required />}
                <Input name="email" label="Email" type="email" required />
                <Input name="password" label="Password" type="password" required />
                {currentPage === 'register' && <Input name="confirmPassword" label="Confirm Password" type="password" required />}
                
                {authError && <div className="p-3 text-sm text-red-500 bg-red-50 rounded-lg flex gap-2"><AlertTriangle className="w-4 h-4"/>{authError}</div>}
                
                <Button type="submit" className="w-full mt-4" disabled={isAuthLoading}>
                  {isAuthLoading ? <Loader className="w-4 h-4 animate-spin"/> : (currentPage === 'login' ? 'Sign In' : 'Sign Up')}
                </Button>
              </form>
              
              <div className="mt-6 text-center text-sm">
                <button onClick={() => setCurrentPage(currentPage === 'login' ? 'register' : 'login')} className="text-blue-600 hover:underline">
                  {currentPage === 'login' ? 'Create an account' : 'Already have an account?'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* DASHBOARD */}
      {currentPage === 'dashboard' && (
        <div className="flex h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 overflow-hidden transition-colors duration-300">
          
          {/* SIDEBAR */}
          <aside className={`fixed md:relative inset-y-0 left-0 z-50 w-72 bg-zinc-50 dark:bg-zinc-950 flex flex-col border-r border-zinc-200 dark:border-zinc-800 transition-transform duration-300 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
            <div className="p-4">
              <Button onClick={handleStartNewChat} variant="outline" className="w-full justify-between">
                <span className="flex items-center gap-2"><Plus className="w-4 h-4" /> New Chat</span>
                <MessageSquare className="w-4 h-4 opacity-50" />
              </Button>
            </div>

            {/* RESTORED: Sidebar Search */}
            <div className="px-4 pb-2">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-zinc-400" />
                <input 
                  type="text" 
                  placeholder="Search history..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg focus:outline-none focus:ring-1 focus:ring-zinc-400 placeholder:text-zinc-400"
                />
              </div>
            </div>

            {/* RESTORED: Grouped History List */}
            <div className="flex-1 overflow-y-auto px-2 space-y-4 scrollbar-thin scrollbar-thumb-zinc-200 dark:scrollbar-thumb-zinc-800 mt-2">
              {isLoadingHistory ? (
                <div className="flex justify-center p-4"><Loader className="w-5 h-5 animate-spin text-zinc-400" /></div>
              ) : historyList.length === 0 ? (
                <div className="text-center text-xs text-zinc-400 mt-4">No history found</div>
              ) : (
                /* Group By Date */
                TIME_CATEGORIES.map(category => {
                  const groupChats = historyList.filter(chat => {
                    const label = getDateLabel(chat.updated_at);
                    // Filter by Search Query too
                    const matchesSearch = chat.title.toLowerCase().includes(searchQuery.toLowerCase());
                    return label === category && matchesSearch;
                  });

                  if (groupChats.length === 0) return null;

                  return (
                    <div key={category}>
                      <h3 className="px-3 text-xs font-semibold text-zinc-400 mb-2 uppercase tracking-wider">{category}</h3>
                      <div className="space-y-0.5">
                        {groupChats.map(chat => (
                          <button 
                            key={chat.id} 
                            onClick={() => handleLoadChat(chat)}
                            className={`w-full text-left px-3 py-2.5 text-sm rounded-lg transition-colors truncate ${activeChatId === chat.id ? 'bg-zinc-200 dark:bg-zinc-800 font-medium' : 'hover:bg-zinc-100 dark:hover:bg-zinc-900'}`}
                          >
                            {chat.title}
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* USER PROFILE */}
            <div ref={userMenuRef} className="p-4 border-t border-zinc-200 dark:border-zinc-800 relative">
              <button onClick={() => setShowUserMenu(!showUserMenu)} className="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-900 transition-colors">
                <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm font-bold">{user.initials}</div>
                <div className="flex-1 text-left text-sm font-medium truncate">{user.name}</div>
                <Settings className="w-4 h-4 text-zinc-400" />
              </button>

              {showUserMenu && (
                <div className="absolute bottom-full left-4 right-4 mb-2 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-xl overflow-hidden z-50 animate-in fade-in slide-in-from-bottom-2">
                  <button onClick={() => { setShowSettings(true); setShowUserMenu(false); }} className="w-full px-4 py-3 text-left text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-2">
                    <Settings className="w-4 h-4" /> Settings
                  </button>
                  <button onClick={handleLogout} className="w-full px-4 py-3 text-left text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2">
                    <LogOut className="w-4 h-4" /> Log out
                  </button>
                </div>
              )}
            </div>
          </aside>

          {/* CHAT AREA */}
          <main className="flex-1 flex flex-col h-full relative w-full">
            <header className="md:hidden h-14 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between px-4 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md sticky top-0 z-30">
              <button onClick={() => setIsSidebarOpen(true)} className="p-2 -ml-2"><Menu className="w-5 h-5" /></button>
              <span className="font-semibold text-sm">RAG Chat</span>
              <div className="w-8" />
            </header>

            {/* MESSAGES */}
            <div 
               ref={messagesContainerRef}
               onScroll={handleScroll}
               className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-thin scrollbar-thumb-zinc-200 dark:scrollbar-thumb-zinc-800"
            >
              {isFetchingOldMessages && (
                 <div className="flex justify-center py-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-zinc-400" />
                 </div>
              )}

              {messages.length === 0 && !isThinking ? (
                <div className="h-full flex flex-col items-center justify-center opacity-50">
                  <div className="bg-zinc-100 dark:bg-zinc-900 p-4 rounded-2xl mb-4"><Bot className="w-8 h-8 text-zinc-400" /></div>
                  <p className="text-zinc-500 font-medium">Start a new conversation</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div key={msg.id} className={`flex gap-4 max-w-3xl mx-auto ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {msg.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-zinc-900 dark:bg-white flex items-center justify-center flex-shrink-0 mt-1">
                        <Bot className="w-4 h-4 text-white dark:text-zinc-900" />
                      </div>
                    )}
                    <div className={`flex flex-col gap-1 max-w-[85%] md:max-w-[75%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className="text-xs text-zinc-400 ml-1">{msg.role === 'user' ? 'You' : 'AI Assistant'}</div>
                      <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm ${msg.role === 'user' ? 'bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-tr-sm' : 'bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-tl-sm'}`}>
                        {msg.content}
                      </div>
                    </div>
                  </div>
                ))
              )}
              {isThinking && (
                 <div className="flex gap-4 max-w-3xl mx-auto justify-start">
                    <div className="w-8 h-8 rounded-full bg-zinc-900 dark:bg-white flex items-center justify-center mt-1"><Bot className="w-4 h-4 text-white dark:text-zinc-900 animate-pulse" /></div>
                    <div className="px-4 py-3 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-1 h-10">
                        <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                        <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                        <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce"></div>
                    </div>
                 </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* INPUT AREA */}
            <div className="p-4 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md border-t border-zinc-200 dark:border-zinc-800">
              <div className="max-w-3xl mx-auto relative">
                <div className={`relative flex flex-col bg-zinc-50 dark:bg-zinc-900 rounded-2xl border transition-all duration-200 ${showProductMenu ? 'border-zinc-400 ring-1 ring-zinc-400/20' : 'border-zinc-200 dark:border-zinc-800'} shadow-sm`}>
                  
                  {/* CONTEXT MENU */}
                  <div className="flex items-center gap-2 px-3 pt-3">
                    <div ref={productMenuRef} className="relative">
                      <button 
                        onClick={() => setShowProductMenu(!showProductMenu)}
                        className={`
                          flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 border
                          ${selectedProduct 
                            ? `${selectedProduct.activeBg} text-white border-transparent shadow-md` 
                            : 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 border-zinc-300 dark:border-zinc-500 hover:border-blue-500 dark:hover:border-blue-400 hover:ring-2 hover:ring-blue-500/20 shadow-sm animate-pulse'
                          }
                        `}
                      >
                        {selectedProduct ? (
                          <><selectedProduct.icon className="w-4 h-4" />{selectedProduct.name}</>
                        ) : (
                          <><div className="bg-blue-100 dark:bg-blue-900/30 p-1 rounded text-blue-600 dark:text-blue-400"><Box className="w-4 h-4" /></div><span>Select Context</span></>
                        )}
                        <ChevronDown className={`w-4 h-4 opacity-60 ml-auto transition-transform ${showProductMenu ? 'rotate-180' : ''}`} />
                      </button>

                      {showProductMenu && (
                        <div className="absolute bottom-full left-0 mb-2 w-64 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-xl overflow-hidden z-20 animate-in fade-in zoom-in-95">
                          <div className="p-2 border-b border-zinc-100 dark:border-zinc-800/50">
                            <input type="text" value={productSearchQuery} onChange={(e) => setProductSearchQuery(e.target.value)} placeholder="Search contexts..." className="w-full px-2 py-1.5 text-xs bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-md" autoFocus />
                          </div>
                          <div className="max-h-60 overflow-y-auto">
                            {products.filter(p => p.name.toLowerCase().includes(productSearchQuery.toLowerCase())).map(product => (
                              <button key={product.id} onClick={() => handleProductSelect(product)} className="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-zinc-50 dark:hover:bg-zinc-800 border-b border-zinc-100 dark:border-zinc-800/50 last:border-0">
                                <div className={`p-1.5 rounded-md ${product.bg} ${product.color}`}><product.icon className="w-4 h-4" /></div>
                                <span className="text-sm font-medium truncate">{product.name}</span>
                                {selectedProduct?.id === product.id && <Check className="w-4 h-4 ml-auto" />}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <textarea
                    ref={inputRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }}
                    placeholder={selectedProduct ? `Ask about ${selectedProduct.name}...` : "Select a context to start asking..."}
                    className="w-full bg-transparent border-0 px-4 py-3 text-sm focus:ring-0 resize-none min-h-[44px] max-h-[200px] outline-none text-zinc-900 dark:text-zinc-100"
                    rows={1}
                    disabled={!selectedProduct || isThinking}
                  />

                  <div className="flex justify-end px-2 pb-2">
                    <button onClick={handleSendMessage} disabled={!inputValue.trim() || !selectedProduct || isThinking}
                      className={`p-2 rounded-lg transition-all ${inputValue.trim() && selectedProduct && !isThinking ? 'bg-gradient-to-tr from-blue-500 to-purple-500 text-white shadow-md' : 'bg-zinc-200 text-zinc-400 dark:bg-zinc-800'}`}
                    >
                      <ArrowUp className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </main>

          {/* CONTEXT WARNING */}
          {showContextWarning && (
            <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
              <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowContextWarning(false)} />
              <div className="bg-white dark:bg-zinc-900 w-full max-w-sm rounded-2xl shadow-xl p-6 text-center relative z-10 animate-in zoom-in-95">
                <AlertTriangle className="w-12 h-12 text-orange-500 mx-auto mb-4" />
                <h3 className="text-lg font-bold mb-2 dark:text-white">Switch Context?</h3>
                <p className="text-sm text-zinc-500 mb-6">Changing context starts a new session.</p>
                <div className="flex gap-3">
                  <Button variant="secondary" onClick={() => setShowContextWarning(false)} className="flex-1">Cancel</Button>
                  <Button onClick={confirmContextSwitch} className="flex-1">Confirm</Button>
                </div>
              </div>
            </div>
          )}

          {/* SETTINGS */}
          {showSettings && (
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
              <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowSettings(false)} />
              <div className="bg-white dark:bg-zinc-900 w-full max-w-md rounded-2xl shadow-xl p-6 relative z-10 animate-in zoom-in-95">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="font-bold text-lg dark:text-white">Settings</h3>
                  <button onClick={() => setShowSettings(false)}><X className="w-5 h-5 text-zinc-500" /></button>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg">{isDarkMode ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}</div>
                    <div><div className="font-medium dark:text-white">Theme</div><div className="text-sm text-zinc-500">Switch mode</div></div>
                  </div>
                  <button onClick={() => setIsDarkMode(!isDarkMode)} className={`w-14 h-7 rounded-full relative transition-colors ${isDarkMode ? 'bg-blue-600' : 'bg-zinc-300'}`}>
                    <span className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform ${isDarkMode ? 'translate-x-7' : 'translate-x-0'}`} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}