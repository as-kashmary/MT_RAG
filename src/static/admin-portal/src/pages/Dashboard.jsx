/**
 * Dashboard Page
 * Main dashboard layout with sidebar and content area.
 */

import { Routes, Route } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import DashboardHome from '../components/DashboardHome';
import DocumentList from '../components/DocumentList';
import ProductsPage from '../components/ProductsPage';
import AdminAnalytics from '../components/AdminAnalytics';
import Settings from './Settings';

function Dashboard() {
    return (
        <div className="min-h-screen bg-dark-950">
            <Sidebar />

            {/* Main Content Area */}
            <main className="lg:ml-72 min-h-screen">
                <div className="p-4 md:p-8 pt-16 lg:pt-8">
                    <Routes>
                        <Route index element={<DashboardHome />} />
                        <Route path="documents" element={<DocumentList />} />
                        <Route path="products" element={<ProductsPage />} />
                        <Route path="analytics" element={<AdminAnalytics />} />
                        <Route path="settings" element={<Settings />} />
                    </Routes>
                </div>
            </main>
        </div>
    );
}

export default Dashboard;
