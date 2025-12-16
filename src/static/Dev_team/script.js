// Mock Data for Tenants and their Products
const tenants = [
    { name: 'Acme Corp', admin: 'John Doe', products: ['HR Helper', 'Sales Bot'], status: 'Active', color: 'bg-orange-100 text-orange-600' },
    { name: 'Globex Inc', admin: 'Sarah Smith', products: ['Tech Support'], status: 'Pending', color: 'bg-blue-100 text-blue-600' },
    { name: 'Soylent Corp', admin: 'Harry P.', products: ['Internal Wiki', 'Legal Aide', 'Ops Bot'], status: 'Active', color: 'bg-purple-100 text-purple-600' }
];

document.addEventListener('DOMContentLoaded', () => {
    // Handle Login
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            document.getElementById('login-overlay').classList.add('hidden');
            initDashboard();
        });
    }
});

function initDashboard() {
    initChart();
    renderTenants();
}

function renderTenants() {
    const container = document.getElementById('tenant-list');
    container.innerHTML = tenants.map(t => `
        <div class="flex items-center p-3 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer border border-gray-50 hover:border-gray-200">
            <div class="w-10 h-10 rounded-full ${t.color} flex items-center justify-center font-bold text-sm">
                ${t.name.charAt(0)}
            </div>
            <div class="ml-3 flex-1">
                <p class="text-sm font-medium text-gray-800">${t.name}</p>
                <p class="text-xs text-gray-500">${t.products.length} Products: ${t.products.join(', ')}</p>
            </div>
            <span class="text-xs px-2 py-1 ${t.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'} rounded-full">${t.status}</span>
        </div>
    `).join('');
}

function initChart() {
    const ctx = document.getElementById('platformChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Global API Requests',
                data: [12000, 19000, 3000, 5000, 20000, 30000, 45000],
                borderColor: '#0ea5e9',
                tension: 0.4,
                fill: false
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });
}