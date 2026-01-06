/**
 * Dashboard Page
 * Main dashboard with sidebar navigation and content area.
 */

import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import DashboardHome from '../components/DashboardHome';

const Dashboard = () => {
    const location = useLocation();
    const isBaseDashboard = location.pathname === '/dashboard';

    return (
        <div className="min-h-screen bg-dark-950 flex">
            <Sidebar />

            <main className="flex-1 p-8 overflow-y-auto">
                <div className="max-w-6xl mx-auto animate-fade-in">
                    {isBaseDashboard ? <DashboardHome /> : <Outlet />}
                </div>
            </main>
        </div>
    );
};

export default Dashboard;
