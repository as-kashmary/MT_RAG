let currentProduct = '';
let currentCompany = '';

// --- MOCK DATA ---
const mockCompanyProducts = {
    'acme-corp': [
        { id: 'hr', name: 'HR Helper', icon: 'fa-users' },
        { id: 'sales', name: 'Sales Assistant', icon: 'fa-chart-pie' },
        { id: 'tech', name: 'Tech Support', icon: 'fa-code' }
    ],
    'globex': [
        { id: 'ops', name: 'Ops Assistant', icon: 'fa-gears' },
        { id: 'legal', name: 'Legal Aide', icon: 'fa-scale-balanced' }
    ],
    'default': [
        { id: 'general', name: 'General Assistant', icon: 'fa-robot' }
    ]
};

const mockHistory = [
    { id: 1, title: "Holiday Policy Inquiry", product: "HR Helper", date: "today" },
    { id: 2, title: "Q3 Sales Projections", product: "Sales Assistant", date: "today" },
    { id: 3, title: "Server 500 Error Fix", product: "Tech Support", date: "week" },
    { id: 4, title: "Onboarding Docs", product: "HR Helper", date: "week" }
];

// --- AUTH LOGIC ---

function toggleAuth(view) {
    document.getElementById('login-view').classList.toggle('hidden', view !== 'login');
    document.getElementById('register-view').classList.toggle('hidden', view !== 'register');
}

function handleLogin(e) {
    if(e) e.preventDefault();
    const companyInput = document.getElementById('login-company').value.toLowerCase().replace(/\s/g, '-');
    proceedToApp(companyInput || 'default');
}

function handleRegister(e) {
    if(e) e.preventDefault();
    const companyInput = document.getElementById('reg-company').value.toLowerCase().replace(/\s/g, '-');
    proceedToApp(companyInput || 'default');
}

function handleGoogleAuth() {
    proceedToApp('acme-corp');
}

function proceedToApp(companyId) {
    currentCompany = companyId;
    document.getElementById('auth-overlay').classList.add('hidden');
    
    // 1. Setup Sidebar
    document.getElementById('sidebar-company-label').textContent = companyId.toUpperCase();
    renderHistory();

    // 2. Setup Dropdown
    populateProductDropdown(companyId);
}

// --- UI RENDER LOGIC ---

function renderHistory() {
    const todayList = document.getElementById('history-list-today');
    const weekList = document.getElementById('history-list-week');
    
    const createItem = (item) => `
        <button class="w-full text-left px-3 py-2 rounded-md hover:bg-slate-800 transition-colors group flex flex-col">
            <span class="text-sm text-slate-300 group-hover:text-white font-medium truncate w-full block">${item.title}</span>
            <span class="text-[10px] text-slate-500 group-hover:text-slate-400 flex items-center mt-1">
                <i class="fa-solid fa-robot mr-1"></i> ${item.product}
            </span>
        </button>
    `;

    todayList.innerHTML = mockHistory.filter(h => h.date === 'today').map(createItem).join('');
    weekList.innerHTML = mockHistory.filter(h => h.date === 'week').map(createItem).join('');
}

function populateProductDropdown(companyId) {
    const products = mockCompanyProducts[companyId] || mockCompanyProducts['default'];
    const select = document.getElementById('product-select');
    
    // Keep the default disabled option
    select.innerHTML = '<option value="" disabled selected>Select Assistant...</option>';
    
    products.forEach(p => {
        const option = document.createElement('option');
        option.value = p.name;
        option.textContent = p.name;
        select.appendChild(option);
    });
}

function toggleSidebar() {
    const sidebar = document.getElementById('history-sidebar');
    sidebar.classList.toggle('hidden');
    sidebar.classList.toggle('absolute');
    sidebar.classList.toggle('inset-y-0');
    sidebar.classList.toggle('left-0');
}

// --- CHAT LOGIC ---

function handleProductChange(productName) {
    currentProduct = productName;
    
    // Enable Inputs
    const input = document.getElementById('chat-input');
    const btn = document.getElementById('send-btn');
    input.disabled = false;
    btn.disabled = false;
    input.placeholder = "Ask a question...";
    input.classList.remove('bg-gray-100');
    input.classList.add('bg-white');

    // Clear Previous Chat / Initial State
    const container = document.getElementById('chat-messages');
    container.innerHTML = ''; 

    // Add Intro Message
    const introHtml = `
        <div class="flex items-start fade-in">
            <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-500 to-purple-500 flex-shrink-0 flex items-center justify-center text-white text-xs mt-1 shadow-md">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="ml-3 bg-white border border-gray-200 p-4 rounded-tr-xl rounded-br-xl rounded-bl-xl text-sm text-gray-800 max-w-lg shadow-sm">
                <p>Hello! I am the <b>${productName}</b> for ${currentCompany}. I'm ready to assist you.</p>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', introHtml);
}

function handleChat(e) {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if(!msg) return;

    // User Message
    const container = document.getElementById('chat-messages');
    container.insertAdjacentHTML('beforeend', `
        <div class="flex items-end justify-end fade-in">
            <div class="chat-bubble user shadow-sm"><p>${msg}</p></div>
        </div>
    `);
    input.value = '';
    container.scrollTop = container.scrollHeight;

    // Loading Animation
    const loadingId = 'loading-' + Date.now();
    container.insertAdjacentHTML('beforeend', `
        <div id="${loadingId}" class="flex items-start fade-in">
            <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-500 to-purple-500 flex-shrink-0 flex items-center justify-center text-white text-xs mt-1"><i class="fa-solid fa-robot"></i></div>
            <div class="ml-3 bg-gray-50 border border-gray-100 p-4 rounded-tr-xl rounded-br-xl rounded-bl-xl"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>
        </div>
    `);
    container.scrollTop = container.scrollHeight;

    // Mock Response
    setTimeout(() => {
        document.getElementById(loadingId).remove();
        let response = `Searching ${currentProduct} knowledge base...`;
        
        if (currentProduct.includes('HR')) response = "According to the vacation policy, you accrue 1.5 days per month.";
        if (currentProduct.includes('Sales')) response = "The Q4 pricing strategy document suggests a 10% discount for annual commitments.";
        if (currentProduct.includes('Tech')) response = "Error 500 usually indicates a server misconfiguration. Check the Nginx logs.";

        container.insertAdjacentHTML('beforeend', `
            <div class="flex items-start fade-in">
                <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-500 to-purple-500 flex-shrink-0 flex items-center justify-center text-white text-xs mt-1 shadow-md"><i class="fa-solid fa-robot"></i></div>
                <div class="ml-3 chat-bubble bot bg-white border border-gray-200 shadow-sm max-w-lg">
                    <p class="text-sm leading-relaxed">${response}</p>
                </div>
            </div>
        `);
        container.scrollTop = container.scrollHeight;
    }, 1500);
}