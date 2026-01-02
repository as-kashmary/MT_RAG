import React, { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { 
  MessageSquare, 
  Plus, 
  Search, 
  Settings, 
  LogOut, 
  User, 
  Moon, 
  Sun, 
  Send, 
  Menu, 
  X, 
  ChevronDown, 
  Box, 
  Cpu, 
  Database, 
  FileText, 
  Bot, 
  Check,
  ArrowUp,
  AlertTriangle,
  Eye,
  EyeOff,
  Sparkles,
  Server,
  Cloud,
  Shield,
  Code,
  Loader
} from 'lucide-react';
import { authAPI, sessionManager } from './services/api';

/**
 * Mock Data & Constants
 */
const PRODUCTS = [
  { id: 'p1', name: 'General Assistant', icon: Bot, color: 'text-blue-500', bg: 'bg-blue-50', activeBg: 'bg-blue-500' },
  { id: 'p2', name: 'Finance API Docs', icon: Database, color: 'text-emerald-500', bg: 'bg-emerald-50', activeBg: 'bg-emerald-500' },
  { id: 'p3', name: 'HR Policy RAG', icon: FileText, color: 'text-orange-500', bg: 'bg-orange-50', activeBg: 'bg-orange-500' },
  { id: 'p4', name: 'Engineering Specs', icon: Cpu, color: 'text-purple-500', bg: 'bg-purple-50', activeBg: 'bg-purple-500' },
  { id: 'p5', name: 'Cloud Infrastructure', icon: Cloud, color: 'text-sky-500', bg: 'bg-sky-50', activeBg: 'bg-sky-500' },
  { id: 'p6', name: 'Security Protocols', icon: Shield, color: 'text-red-500', bg: 'bg-red-50', activeBg: 'bg-red-500' },
  { id: 'p7', name: 'Legacy Systems', icon: Server, color: 'text-slate-500', bg: 'bg-slate-50', activeBg: 'bg-slate-500' },
  { id: 'p8', name: 'Frontend Guidelines', icon: Code, color: 'text-pink-500', bg: 'bg-pink-50', activeBg: 'bg-pink-500' },
  { id: 'p9', name: 'Backend Architecture', icon:  Box, color: 'text-indigo-500', bg: 'bg-indigo-50', activeBg: 'bg-indigo-500' },
  { id: 'p10', name: 'Mobile App Docs', icon: Sparkles, color: 'text-yellow-500', bg: 'bg-yellow-50', activeBg: 'bg-yellow-500' },
];

const NOW = Date.now();
const ONE_DAY = 24 * 60 * 60 * 1000;

const INITIAL_MOCK_HISTORY = [
  { id: 1, title: 'API Integration Help', timestamp: NOW, product: 'Finance API Docs' },
  { id: 2, title: 'Leave Policy Inquiry', timestamp: NOW - ONE_DAY, product: 'HR Policy RAG' },
  { id: 3, title: 'React Component Structure', timestamp: NOW - (3 * ONE_DAY), product: 'Engineering Specs' },
  { id: 4, title: 'Q4 Revenue Analysis', timestamp: NOW - (5 * ONE_DAY), product: 'General Assistant' },
  { id: 5, title: 'Onboarding Process', timestamp: NOW - (15 * ONE_DAY), product: 'HR Policy RAG' },
];

const INITIAL_MESSAGES = [
  { id: 1, role: 'system', content: 'Welcome! Please select a product context to begin your query.' },
];

const INITIAL_SESSIONS = {
  1: [
    { id: 1, role: 'system', content: 'Context: Finance API Docs' },
    { id: 2, role: 'user', content: 'How do I authenticate with the API?' },
    { id: 3, role: 'assistant', content: 'You can authenticate using a Bearer token in the header.' }
  ],
  2: [
    { id: 1, role: 'system', content: 'Context: HR Policy RAG' },
    { id: 2, role: 'user', content: 'What is the leave policy?' },
    { id: 3, role: 'assistant', content: 'Employees are entitled to 20 days of annual leave.' }
  ]
};

/**
 * Helper Functions
 */
const getInitials = (name) => {
  if (!name) return 'U';
  const parts = name.trim().split(' ');
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

const getDateLabel = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const sevenDaysAgo = new Date(today);
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  const thirtyDaysAgo = new Date(today);
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  if (date >= today) return 'Today';
  if (date >= yesterday) return 'Yesterday';
  if (date >= sevenDaysAgo) return 'Previous 7 Days';
  if (date >= thirtyDaysAgo) return 'Previous 30 Days';
  return 'Older';
};

const TIME_CATEGORIES = ['Today', 'Yesterday', 'Previous 7 Days', 'Previous 30 Days', 'Older'];

/**
 * Helper Components
 */
const Button = ({ children, onClick, variant = 'primary', className = '', ...props }) => {
  const baseStyle = "px-4 py-2.5 rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed";
  
  const variants = {
    primary: "bg-gradient-to-tr from-blue-500 to-purple-500 text-white hover:from-blue-600 hover:to-purple-600 shadow-md shadow-blue-500/20",
    secondary: "bg-zinc-100 text-zinc-900 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-100 dark:hover:bg-zinc-700",
    ghost: "bg-transparent hover:bg-zinc-100 text-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800",
    outline: "border border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
  };

  return (
    <button onClick={onClick} className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
};

const Input = ({ label, type = "text", placeholder, className = "", ...props }) => {
  const [currentType, setCurrentType] = useState(type);
  const isPassword = type === 'password';

  const showPassword = () => setCurrentType('text');
  const hidePassword = () => setCurrentType('password');

  return (
    <div className="flex flex-col gap-2 w-full">
      {label && <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">{label}</label>}
      <div className="relative">
        <input 
          type={currentType} 
          placeholder={placeholder}
          className={`w-full px-3 py-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 focus:border-blue-500 dark:focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all placeholder:text-zinc-400 text-zinc-900 dark:text-zinc-100 ${className} ${isPassword ? 'pr-10' : ''}`}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onMouseDown={showPassword}
            onMouseUp={hidePassword}
            onMouseLeave={hidePassword}
            onTouchStart={showPassword}
            onTouchEnd={hidePassword}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition-colors focus:outline-none p-1 rounded-md"
            tabIndex={-1}
            title="Hold to view password"
          >
            {currentType === 'text' ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * Main Application Component
 */
export default function App() {
  const [currentPage, setCurrentPage] = useState('login');
  const [isAuthenticated, setIsAuthenticated] = useState(() => sessionManager.isAuthenticated());
  const [authError, setAuthError] = useState('');
  const [isAuthLoading, setIsAuthLoading] = useState(false);
  
  const [user, setUser] = useState(() => {
    const session = sessionManager.getSession();
    return session ? {
      name: session.name,
      email: session.email,
      userId: session.userId,
      initials: getInitials(session.name)
    } : {
      name: 'User',
      email: '',
      userId: null,
      initials: 'U'
    };
  });
  
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('rag_dark_mode');
    return saved ? JSON.parse(saved) : false;
  });
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem('rag_history');
    return saved ? JSON.parse(saved) : INITIAL_MOCK_HISTORY;
  });
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem('rag_sessions');
    return saved ? JSON.parse(saved) : INITIAL_SESSIONS;
  });

  const [inputValue, setInputValue] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeChatId, setActiveChatId] = useState(null);
  const [isThinking, setIsThinking] = useState(false);
  
  const [showProductMenu, setShowProductMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showContextWarning, setShowContextWarning] = useState(false);
  const [pendingProduct, setPendingProduct] = useState(null);
  const [productSearchQuery, setProductSearchQuery] = useState('');

  const messagesEndRef = useRef(null);
  const userMenuRef = useRef(null);
  const productMenuRef = useRef(null);
  const inputRef = useRef(null);

  // Persistence (only when authenticated)
  useEffect(() => { 
    if (isAuthenticated) {
      localStorage.setItem('rag_history', JSON.stringify(history)); 
    }
  }, [history, isAuthenticated]);
  
  useEffect(() => { 
    if (isAuthenticated) {
      localStorage.setItem('rag_sessions', JSON.stringify(sessions)); 
    }
  }, [sessions, isAuthenticated]);
  
  // Sync dark mode with DOM and localStorage synchronously
  useLayoutEffect(() => {
    const html = document.documentElement;
    console.log('isDarkMode changed to:', isDarkMode);
    console.log('HTML element before:', html.className);
    
    if (isDarkMode) {
      html.classList.add('dark');
      html.style.colorScheme = 'dark';
    } else {
      html.classList.remove('dark');
      html.style.colorScheme = 'light';
    }
    
    console.log('HTML element after:', html.className);
    console.log('Has dark class:', html.classList.contains('dark'));
  }, [isDarkMode]);

  // Save dark mode preference to localStorage (can be async)
  useEffect(() => {
    localStorage.setItem('rag_dark_mode', JSON.stringify(isDarkMode));
  }, [isDarkMode]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isThinking]);

  // Click Outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showUserMenu && userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
      if (showProductMenu && productMenuRef.current && !productMenuRef.current.contains(event.target)) {
        setShowProductMenu(false);
        setProductSearchQuery('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showUserMenu, showProductMenu]);

  // Handlers
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    setIsAuthLoading(true);
    
    const formData = new FormData(e.currentTarget);
    const email = formData.get('email');
    const password = formData.get('password');

    try {
      if (currentPage === 'register') {
        // Handle Signup
        const fullName = formData.get('fullName');
        const confirmPassword = formData.get('confirmPassword');

        if (password !== confirmPassword) {
          setAuthError('Passwords do not match. Please try again.');
          setIsAuthLoading(false);
          return;
        }

        if (!fullName || !email || !password) {
          setAuthError('All fields are required.');
          setIsAuthLoading(false);
          return;
        }

        // Call signup API
        const signupResult = await authAPI.signup({
          name: fullName,
          email,
          password
        });

        if (!signupResult.success) {
          setAuthError(signupResult.message || 'Signup failed. Please try again.');
          setIsAuthLoading(false);
          return;
        }

        // After successful signup, switch to login
        setAuthError('');
        setCurrentPage('login');
        setIsAuthLoading(false);
        // Show success message
        alert('Signup successful! Please log in with your credentials.');
        return;
      } else {
        // Handle Login
        if (!email || !password) {
          setAuthError('Email and password are required.');
          setIsAuthLoading(false);
          return;
        }

        const loginResult = await authAPI.login(email, password);

        if (!loginResult.success) {
          setAuthError(loginResult.message || 'Login failed. Please check your credentials.');
          setIsAuthLoading(false);
          return;
        }

        // Save session
        const userData = {
          userId: loginResult.userId,
          email,
          name: email.split('@')[0], // Use email prefix as name if not available
        };

        sessionManager.saveSession(userData);

        // Update user state
        setUser({
          name: userData.name,
          email: userData.email,
          userId: userData.userId,
          initials: getInitials(userData.name)
        });

        setIsAuthenticated(true);
        setCurrentPage('dashboard');
        setAuthError('');
      }
    } catch (error) {
      console.error('Auth error:', error);
      setAuthError('An error occurred. Please try again.');
    } finally {
      setIsAuthLoading(false);
    }
  };

  const handleLogout = () => {
    sessionManager.clearSession();
    setCurrentPage('login');
    setIsAuthenticated(false);
    setMessages(INITIAL_MESSAGES);
    setHistory(INITIAL_MOCK_HISTORY);
    setSessions(INITIAL_SESSIONS);
    setSelectedProduct(null);
    setActiveChatId(null);
    setInputValue('');
    setIsThinking(false);
    setShowUserMenu(false);
    setShowSettings(false);
    setShowProductMenu(false);
    setShowContextWarning(false);
    setPendingProduct(null);
    setProductSearchQuery('');
    setAuthError('');
    setUser({
      name: 'User',
      email: '',
      userId: null,
      initials: 'U'
    });
  };

  const handleToggleDarkMode = () => {
    console.log('Toggle button clicked, current isDarkMode:', isDarkMode);
    setIsDarkMode(prev => {
      console.log('Setting isDarkMode from', prev, 'to', !prev);
      return !prev;
    });
  };

  const handleStartNewChat = () => {
    setMessages(INITIAL_MESSAGES);
    setSelectedProduct(null);
    setActiveChatId(null);
    setInputValue('');
    setIsThinking(false);
    if (window.innerWidth < 768) setIsSidebarOpen(false);
  };

  const handleLoadChat = (chat) => {
    setActiveChatId(chat.id);
    const productContext = PRODUCTS.find(p => p.name === chat.product);
    setSelectedProduct(productContext || null);
    const savedMessages = sessions[chat.id];
    setMessages(savedMessages || [
      { id: 1, role: 'system', content: `Restored Context: ${chat.product}` },
      { id: 2, role: 'user', content: chat.title },
      { id: 3, role: 'assistant', content: 'This is a mock history item.' }
    ]);
    // Clear search query when chat is selected
    setSearchQuery('');
    // Close sidebar on mobile
    if (window.innerWidth < 768) setIsSidebarOpen(false);
    // Scroll selected chat into view with a small delay to ensure render
    setTimeout(() => {
      const chatElement = document.querySelector(`[data-chat-id="${chat.id}"]`);
      if (chatElement) {
        chatElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      // Auto-focus on input after chat is loaded
      inputRef.current?.focus();
    }, 0);
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const newMsg = { id: Date.now(), role: 'user', content: inputValue };
    let currentChatId = activeChatId;
    
    if (!currentChatId) {
      currentChatId = Date.now();
      setActiveChatId(currentChatId);
      const newHistoryItem = {
        id: currentChatId,
        title: inputValue,
        timestamp: Date.now(),
        product: selectedProduct ? selectedProduct.name : 'General Assistant'
      };
      setHistory(prev => [newHistoryItem, ...prev]);
    }

    const updatedMessages = [...messages, newMsg];
    setMessages(updatedMessages);
    setInputValue('');
    setIsThinking(true);
    setSessions(prev => ({ ...prev, [currentChatId]: updatedMessages }));
    
    setTimeout(() => {
      const botMsg = { 
        id: Date.now() + 1, 
        role: 'assistant', 
        content: `I'm analyzing your request regarding "${selectedProduct ? selectedProduct.name : 'General Context'}". Here is a simulated response based on the retrieved documents.` 
      };
      setMessages(prev => [...prev, botMsg]);
      setIsThinking(false);
      setSessions(prev => ({
        ...prev,
        [currentChatId]: [...(prev[currentChatId] || updatedMessages), botMsg]
      }));
    }, 2000);
  };

  const handleProductSelect = (product) => {
    const isChatActive = activeChatId || messages.length > 1;
    if (isChatActive && selectedProduct?.id !== product.id) {
       setPendingProduct(product);
       setShowContextWarning(true);
       setShowProductMenu(false);
       setProductSearchQuery('');
    } else {
       setSelectedProduct(product);
       setShowProductMenu(false);
       setProductSearchQuery('');
       // Auto-focus on input after context is selected
       setTimeout(() => inputRef.current?.focus(), 0);
    }
  };

  const confirmContextSwitch = () => {
    setMessages(INITIAL_MESSAGES);
    setActiveChatId(null);
    setIsThinking(false);
    setSelectedProduct(pendingProduct);
    setPendingProduct(null);
    setShowContextWarning(false);
    // Auto-focus on input after context switch is confirmed
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleDeleteHistory = () => {
    if (window.confirm("Are you sure you want to delete all chat history?")) {
      setHistory([]);
      setSessions({});
      localStorage.setItem('rag_history', JSON.stringify([]));
      localStorage.setItem('rag_sessions', JSON.stringify({}));
      handleStartNewChat();
      setShowSettings(false); 
    }
  };

  const filteredProducts = PRODUCTS.filter(product => 
    product.name.toLowerCase().includes(productSearchQuery.toLowerCase())
  );

  return (
    <>
      {/* Login / Register */}
      {(currentPage === 'login' || currentPage === 'register') && (
        <div className="min-h-screen flex items-center justify-center bg-zinc-50 dark:bg-zinc-950 px-4 transition-colors duration-300">
          <div className="w-full max-w-md bg-white dark:bg-zinc-900 rounded-2xl shadow-xl border border-zinc-100 dark:border-zinc-800 overflow-hidden">
            <div className="p-8">
              <div className="flex justify-center mb-8">
                <div className="w-12 h-12 bg-gradient-to-tr from-blue-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                  <Bot className="w-6 h-6 text-white" />
                </div>
              </div>
              
              <h2 className="text-2xl font-bold text-center text-zinc-900 dark:text-white mb-2">
                {currentPage === 'login' ? 'Welcome Back' : 'Create Account'}
              </h2>
              <p className="text-center text-zinc-500 dark:text-zinc-400 mb-8">
                {currentPage === 'login' ? 'Enter your credentials to access the workspace.' : 'Get started with your AI-powered assistant.'}
              </p>

              <form key={currentPage} onSubmit={handleLogin} className="space-y-4">
                {currentPage === 'register' && (
                  <Input name="fullName" label="Full Name" placeholder="John Doe" required autoFocus disabled={isAuthLoading} />
                )}
                <Input name="email" label="Email" type="email" placeholder="name@company.com" required disabled={isAuthLoading} />
                <Input name="password" label="Password" type="password" placeholder="••••••••" required disabled={isAuthLoading} />
                
                {currentPage === 'register' && (
                  <Input name="confirmPassword" label="Confirm Password" type="password" placeholder="••••••••" required disabled={isAuthLoading} />
                )}
                
                {authError && (
                  <div className="p-3 text-sm text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg flex items-center gap-2 border border-red-100 dark:border-red-900/30 animate-in fade-in slide-in-from-top-1">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    {authError}
                  </div>
                )}

                <Button 
                  type="submit" 
                  variant="primary" 
                  className="w-full mt-6 py-3"
                  disabled={isAuthLoading}
                >
                  {isAuthLoading ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      {currentPage === 'login' ? 'Signing in...' : 'Creating account...'}
                    </>
                  ) : (
                    currentPage === 'login' ? 'Sign In' : 'Sign Up'
                  )}
                </Button>
              </form>

              <div className="mt-6 text-center text-sm">
                <span className="text-zinc-500 dark:text-zinc-400">
                  {currentPage === 'login' ? "Don't have an account? " : "Already have an account? "}
                </span>
                <button 
                  onClick={() => {
                    setCurrentPage(currentPage === 'login' ? 'register' : 'login');
                    setAuthError('');
                  }}
                  className="font-medium text-blue-600 dark:text-blue-400 hover:underline"
                >
                  {currentPage === 'login' ? 'Sign up' : 'Log in'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard */}
      {currentPage === 'dashboard' && (
        <div className="flex h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 overflow-hidden transition-colors duration-300">
          {/* Mobile Overlay */}
          {isSidebarOpen && <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={() => setIsSidebarOpen(false)} />}

          {/* Sidebar */}
          <aside className={`fixed md:relative inset-y-0 left-0 z-50 w-72 bg-zinc-50 dark:bg-zinc-950 flex flex-col border-r border-zinc-200 dark:border-zinc-800 transition-transform duration-300 ease-in-out ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
            <div className="p-4">
              <Button onClick={handleStartNewChat} variant="outline" className="w-full justify-between group hover:border-zinc-300 dark:hover:border-zinc-600">
                <span className="flex items-center gap-2"><Plus className="w-4 h-4" /> New Chat</span>
                <MessageSquare className="w-4 h-4 opacity-0 group-hover:opacity-50 transition-opacity" />
              </Button>
            </div>

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

            <div className="flex-1 overflow-y-auto px-2 py-2 space-y-6 scrollbar-thin scrollbar-thumb-zinc-200 dark:scrollbar-thumb-zinc-800">
              {TIME_CATEGORIES.map(category => {
                const groupChats = history.filter(c => {
                  const label = getDateLabel(c.timestamp);
                  return label === category && c.title.toLowerCase().includes(searchQuery.toLowerCase());
                });
                
                if (groupChats.length === 0) return null;

                return (
                  <div key={category}>
                    <h3 className="px-3 text-xs font-semibold text-zinc-400 mb-2">{category}</h3>
                    <div className="space-y-0.5">
                      {groupChats.map(chat => (
                        <button
                          key={chat.id}
                          data-chat-id={chat.id}
                          onClick={() => handleLoadChat(chat)}
                          className={`w-full text-left px-3 py-2 text-sm rounded-lg flex items-center justify-between group transition-colors ${activeChatId === chat.id ? 'bg-zinc-200 dark:bg-zinc-800 font-medium' : 'hover:bg-zinc-100 dark:hover:bg-zinc-900'}`}
                        >
                          <span className="truncate flex-1">{chat.title}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            <div ref={userMenuRef} className="p-4 border-t border-zinc-200 dark:border-zinc-800 relative">
              <button 
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-900 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-white text-sm font-bold">
                  {user.initials}
                </div>
                <div className="flex-1 text-left">
                  <div className="text-sm font-medium">{user.name}</div>
                  <div className="text-xs text-zinc-500">Pro Plan</div>
                </div>
                <Settings className="w-4 h-4 text-zinc-400" />
              </button>

              {showUserMenu && (
                <div className="absolute bottom-full left-4 right-4 mb-2 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-bottom-2 z-50">
                  <button onClick={() => { setShowSettings(true); setShowUserMenu(false); }} className="w-full px-4 py-3 text-left text-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-2">
                    <Settings className="w-4 h-4" /> Settings
                  </button>
                  <div className="h-px bg-zinc-100 dark:bg-zinc-800" />
                  <button onClick={handleLogout} className="w-full px-4 py-3 text-left text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2">
                    <LogOut className="w-4 h-4" /> Log out
                  </button>
                </div>
              )}
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 flex flex-col h-full relative w-full">
            <header className="md:hidden h-14 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between px-4 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md sticky top-0 z-30">
              <button onClick={() => setIsSidebarOpen(true)} className="p-2 -ml-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg">
                <Menu className="w-5 h-5" />
              </button>
              <span className="font-semibold text-sm">RAG Chat</span>
              <div className="w-8" />
            </header>

            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-thin scrollbar-thumb-zinc-200 dark:scrollbar-thumb-zinc-800">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center opacity-50">
                  <div className="bg-zinc-100 dark:bg-zinc-900 p-4 rounded-2xl mb-4">
                    <Bot className="w-8 h-8 text-zinc-400" />
                  </div>
                  <p className="text-zinc-500 font-medium">Start a new conversation</p>
                </div>
              ) : (
                <>
                  {messages.map((msg) => (
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
                      {msg.role === 'user' && (
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0 mt-1 text-white text-xs font-bold">
                          {user.initials}
                        </div>
                      )}
                    </div>
                  ))}
                  {isThinking && (
                    <div className="flex gap-4 max-w-3xl mx-auto justify-start">
                      <div className="w-8 h-8 rounded-full bg-zinc-900 dark:bg-white flex items-center justify-center flex-shrink-0 mt-1">
                        <Bot className="w-4 h-4 text-white dark:text-zinc-900 animate-pulse" />
                      </div>
                      <div className="flex flex-col gap-1 items-start">
                        <div className="text-xs text-zinc-400 ml-1">AI Assistant</div>
                        <div className="px-4 py-3 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl rounded-tl-sm text-sm leading-relaxed shadow-sm">
                          <div className="flex items-center gap-1 h-5">
                            <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                            <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                            <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce"></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="p-4 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md border-t border-zinc-200 dark:border-zinc-800">
              <div className="max-w-3xl mx-auto relative">
                <div className={`relative flex flex-col bg-zinc-50 dark:bg-zinc-900 rounded-2xl border transition-all duration-200 ${showProductMenu ? 'border-zinc-400 dark:border-zinc-600 ring-1 ring-zinc-400/20' : 'border-zinc-200 dark:border-zinc-800 focus-within:border-zinc-400 dark:focus-within:border-zinc-600 focus-within:ring-1 focus-within:ring-zinc-400/20'} shadow-sm`}>
                  <div className="flex items-center gap-2 px-3 pt-3">
                    <div ref={productMenuRef} className="relative">
                      <button 
                        onClick={() => setShowProductMenu(!showProductMenu)}
                        className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${selectedProduct ? `${selectedProduct.activeBg} text-white shadow-sm` : 'bg-white dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-700'}`}
                      >
                        {selectedProduct ? <><selectedProduct.icon className="w-3.5 h-3.5" />{selectedProduct.name}</> : <><Box className="w-3.5 h-3.5" />Select Context</>}
                        <ChevronDown className="w-3 h-3 opacity-60" />
                      </button>

                      {showProductMenu && (
                        <div className="absolute bottom-full left-0 mb-2 w-64 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-xl overflow-hidden z-20 animate-in fade-in zoom-in-95 origin-bottom-left flex flex-col">
                          <div className="p-2 border-b border-zinc-100 dark:border-zinc-800/50 bg-zinc-50 dark:bg-zinc-950/50">
                            <div className="relative">
                              <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-zinc-400" />
                              <input type="text" value={productSearchQuery} onChange={(e) => setProductSearchQuery(e.target.value)} placeholder="Search contexts..." className="w-full pl-8 pr-3 py-1.5 text-xs bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-md focus:outline-none focus:border-zinc-400 dark:focus:border-zinc-600" autoFocus />
                            </div>
                          </div>
                          <div className="max-h-60 overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-200 dark:scrollbar-thumb-zinc-800">
                            {filteredProducts.length > 0 ? (
                              filteredProducts.map(product => (
                                <button key={product.id} onClick={() => handleProductSelect(product)} className="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors group border-b border-zinc-100 dark:border-zinc-800/50 last:border-0">
                                  <div className={`p-1.5 rounded-md ${product.bg} ${product.color} flex-shrink-0`}><product.icon className="w-4 h-4" /></div>
                                  <span className="text-sm text-zinc-700 dark:text-zinc-200 font-medium truncate">{product.name}</span>
                                  {selectedProduct?.id === product.id && <Check className="w-4 h-4 ml-auto text-zinc-900 dark:text-white flex-shrink-0" />}
                                </button>
                              ))
                            ) : <div className="p-4 text-center text-xs text-zinc-400">No contexts found.</div>}
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
                    className="w-full bg-transparent border-0 px-4 py-3 text-sm focus:ring-0 resize-none min-h-[44px] max-h-[200px] outline-none text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400"
                    rows={1}
                    style={{ height: 'auto', minHeight: '50px' }}
                    disabled={!selectedProduct || isThinking}
                  />

                  <div className="flex justify-end items-center px-2 pb-2">
                    <button 
                      onClick={handleSendMessage}
                      disabled={!inputValue.trim() || !selectedProduct || isThinking}
                      className={`p-2 rounded-lg transition-all duration-200 ${inputValue.trim() && selectedProduct && !isThinking ? 'bg-gradient-to-tr from-blue-500 to-purple-500 text-white shadow-md hover:shadow-lg hover:-translate-y-0.5' : 'bg-zinc-200 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-600 cursor-not-allowed'}`}
                    >
                      <ArrowUp className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-center text-xs text-zinc-400 mt-2">AI can make mistakes. Please verify important information.</p>
              </div>
            </div>
          </main>

          {/* Context Warning Modal */}
          {showContextWarning && (
            <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
              <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowContextWarning(false)} />
              <div className="bg-white dark:bg-zinc-900 w-full max-w-sm rounded-2xl shadow-2xl overflow-hidden relative z-10 animate-in zoom-in-95 duration-200 border border-zinc-200 dark:border-zinc-800">
                <div className="p-6 text-center">
                  <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <AlertTriangle className="w-6 h-6 text-orange-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">Switch Context?</h3>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6">Changing the product context will start a new chat session to ensure accuracy. Your current conversation will be saved in history.</p>
                  <div className="flex gap-3">
                    <Button variant="secondary" onClick={() => setShowContextWarning(false)} className="flex-1">Cancel</Button>
                    <Button onClick={confirmContextSwitch} className="flex-1">Start New Chat</Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Settings Modal */}
          {showSettings && (
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
              <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowSettings(false)} />
              <div className="bg-white dark:bg-zinc-900 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden relative z-10 animate-in zoom-in-95 duration-200">
                <div className="p-4 border-b border-zinc-100 dark:border-zinc-800 flex justify-between items-center">
                  <h3 className="font-semibold text-lg">Settings</h3>
                  <button onClick={() => setShowSettings(false)} className="p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-full"><X className="w-5 h-5" /></button>
                </div>
                <div className="p-6 space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg">{isDarkMode ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}</div>
                      <div>
                        <div className="font-medium">Theme Preference</div>
                        <div className="text-sm text-zinc-500">Switch between light and dark mode</div>
                      </div>
                    </div>
                    <button onClick={handleToggleDarkMode} className={`relative w-14 h-7 rounded-full transition-all duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${isDarkMode ? 'bg-blue-600' : 'bg-gray-300'}`}>
                      <span className={`absolute top-0.5 left-0.5 inline-block w-6 h-6 transform bg-white rounded-full shadow-md transition-all duration-300 ease-in-out ${isDarkMode ? 'translate-x-7' : 'translate-x-0'}`} />
                    </button>
                  </div>
                  <div className="pt-4 border-t border-zinc-100 dark:border-zinc-800">
                    <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Account Data</div>
                    <Button variant="outline" onClick={handleDeleteHistory} className="w-full justify-center text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10 border-red-200 dark:border-red-900/30">Delete All Chat History</Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}