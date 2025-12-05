// Mock Data per Product
const productData = {
    'hr': { name: 'Product A', docs: '1,240', chats: '342', topics: [40, 30, 30] },
    'sales': { name: 'Product B', docs: '850', chats: '1,102', topics: [10, 80, 10] },
    'tech': { name: 'Product C', docs: '5,000+', chats: '89', topics: [60, 20, 20] }
};

let chartInstance = null;
let currentCompany = '';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Handle Admin Login
    const loginForm = document.getElementById('admin-login-form');
    if(loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const companyId = document.getElementById('company-id').value;
            
            // Simple validation simulation
            if(companyId.trim() === '') {
                alert("Please enter a workspace ID");
                return;
            }

            handleLoginSuccess(companyId);
        });
    }

    // 2. Drag & Drop Visuals for Drop Zone
    const dropZone = document.getElementById('drop-zone');
    if(dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        dropZone.addEventListener('drop', handleDrop, false);
    }
});

// --- LOGIN LOGIC ---

function handleLoginSuccess(companyId) {
    currentCompany = companyId;
    
    // Hide Login Portal
    const loginPortal = document.getElementById('login-portal');
    loginPortal.classList.add('opacity-0', 'pointer-events-none', 'transition-opacity', 'duration-500');
    
    // Show Main App after small delay for transition
    setTimeout(() => {
        loginPortal.classList.add('hidden');
        const mainApp = document.getElementById('main-app');
        mainApp.classList.remove('hidden');
        mainApp.classList.add('fade-in'); // Trigger animation
        
        // Update Sidebar Branding
        document.getElementById('sidebar-company-name').innerHTML = `${companyId}<span class="text-brand-500">Panel</span>`;
        
        // Initialize Default Product
        switchProduct('hr'); 
    }, 500);
}

function logout() {
    location.reload();
}

// --- DASHBOARD LOGIC ---

function showView(view) {
    // Hide all views
    document.getElementById('view-dashboard').classList.add('hidden');
    document.getElementById('view-upload').classList.add('hidden');
    
    // Show target
    document.getElementById('view-' + view).classList.remove('hidden');
    
    // Update Nav Active State
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('bg-brand-600', 'text-white');
        el.classList.add('text-slate-400', 'hover:bg-slate-800', 'hover:text-white');
    });

    const activeNav = document.getElementById('nav-' + view);
    if(activeNav) {
        activeNav.classList.remove('text-slate-400', 'hover:bg-slate-800', 'hover:text-white');
        activeNav.classList.add('bg-brand-600', 'text-white');
    }
}

function switchProduct(productId) {
    const data = productData[productId];
    
    // Update Dashboard Text
    document.getElementById('dash-title').textContent = `${data.name} Dashboard`;
    document.getElementById('stat-docs').textContent = data.docs;
    document.getElementById('stat-chats').textContent = data.chats;
    
    const contextBadge = document.getElementById('upload-context');
    if(contextBadge) contextBadge.textContent = data.name;

    // Update Chart
    updateChart(data.topics);
}

function updateChart(dataPoints) {
    const ctx = document.getElementById('companyChart').getContext('2d');
    
    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Internal Policy', 'Technical Docs', 'General Knowledge'],
            datasets: [{ 
                data: dataPoints, 
                backgroundColor: ['#0ea5e9', '#7c3aed', '#f59e0b'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false, 
            plugins: { 
                legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } } 
            },
            cutout: '75%'
        }
    });
}

// --- FILE UPLOAD LOGIC ---

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    const dz = document.getElementById('drop-zone');
    dz.classList.add('bg-brand-50', 'border-brand-500');
}

function unhighlight(e) {
    const dz = document.getElementById('drop-zone');
    dz.classList.remove('bg-brand-50', 'border-brand-500');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFileSelect(files);
}

function handleFileSelect(files) {
    const list = document.getElementById('upload-list');
    list.classList.remove('hidden');
    
    Array.from(files).forEach(file => {
        // Random ID for progress simulation
        const id = Math.random().toString(36).substr(2, 9);
        
        const html = `
            <div class="bg-white p-3 rounded-lg border border-gray-200 flex items-center shadow-sm animate-pulse" id="file-${id}">
                <div class="w-8 h-8 rounded-lg bg-red-100 text-red-500 flex items-center justify-center mr-3">
                    <i class="fa-solid fa-file-pdf"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">${file.name}</p>
                    <p class="text-xs text-gray-500">${(file.size/1024).toFixed(1)} KB • Queued</p>
                </div>
                <span class="ml-2 text-xs font-bold text-brand-600 bg-brand-50 px-2 py-1 rounded border border-brand-100 whitespace-nowrap">
                   ${document.getElementById('product-switcher').options[document.getElementById('product-switcher').selectedIndex].text}
                </span>
                <div class="ml-4 w-6 h-6 rounded-full border-2 border-brand-200 border-t-brand-600 animate-spin" id="spinner-${id}"></div>
                <i class="fa-solid fa-circle-check text-green-500 text-lg ml-4 hidden" id="check-${id}"></i>
            </div>`;
        list.insertAdjacentHTML('beforeend', html);

        // Simulate upload process
        setTimeout(() => {
            const row = document.getElementById(`file-${id}`);
            const spinner = document.getElementById(`spinner-${id}`);
            const check = document.getElementById(`check-${id}`);
            
            row.classList.remove('animate-pulse');
            spinner.classList.add('hidden');
            check.classList.remove('hidden');
        }, 1500 + Math.random() * 1000);
    });
}