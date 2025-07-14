import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, 
  Ticket, 
  Plus, 
  Search, 
  Settings, 
  User, 
  LogOut, 
  Menu, 
  X,
  Bell
} from 'lucide-react';
import { useAuth } from '../context/AuthContext.tsx';
import { getInitials } from '../utils/index.ts';

const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const navigationItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/tickets', icon: Ticket, label: 'Tickets' },
    { path: '/create-ticket', icon: Plus, label: 'Create Ticket' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
    setSidebarOpen(false);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed inset-0 bg-gray-800 text-white md:relative md:translate-x-0 z-50 transform"
          >
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between p-4 border-b border-gray-700">
                <div className="font-bold text-xl text-blue-400">IT Support</div>
                <button onClick={() => setSidebarOpen(false)} className="md:hidden focus:outline-none p-2 rounded-full hover:bg-gray-700">
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto">
                {navigationItems.map(item => (
                  <div 
                    key={item.path}
                    onClick={() => handleNavigation(item.path)}
                    className={`flex items-center p-3 cursor-pointer hover:bg-gray-700 ${location.pathname === item.path ? 'bg-blue-800' : ''}`}
                  >
                    <item.icon size={20} className="mr-4" />
                    <span className="text-white">{item.label}</span>
                  </div>
                ))}
              </div>

              <div className="p-4 border-t border-gray-700">
                <div onClick={handleLogout} className="flex items-center p-3 cursor-pointer hover:bg-gray-700">
                  <LogOut size={20} className="mr-4" />
                  <span className="text-white">Logout</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="flex justify-between items-center p-4 border-b bg-white shadow">
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)} 
              className="md:hidden focus:outline-none p-2 rounded-full hover:bg-gray-200">
              <Menu size={20} />
            </button>
            <div className="relative">
              <Search size={16} className="absolute top-2 left-3 text-gray-500" />
              <form onSubmit={handleSearch}>
                <input
                  type="text"
                  className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg shadow-sm focus:outline-none focus:ring focus:border-blue-300"
                  placeholder="Search tickets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </form>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="relative cursor-pointer">
              <Bell size={20} className="text-gray-600" />
              <div className="absolute top-0 right-0 bg-red-600 text-white text-xs w-2 h-2 rounded-full"></div>
            </div>
            <div className="flex items-center space-x-2 cursor-pointer p-1 hover:bg-gray-200 rounded-lg">
              <div className="w-8 h-8 rounded-full bg-blue-400 flex items-center justify-center text-white font-medium">
                {user ? getInitials(user.name) : 'U'}
              </div>
              <div className="hidden md:block">
                <div className="text-gray-800 font-medium">{user?.name}</div>
                <div className="text-gray-600 text-sm">{user?.role}</div>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>

      <div
        className={`fixed inset-0 bg-black opacity-50 md:hidden z-40 ${sidebarOpen ? 'block' : 'hidden'}`}
        onClick={() => setSidebarOpen(false)}
      />
    </div>
  );
};

export default Layout;
