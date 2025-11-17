/**
 * Navigation Bar Component
 */

import { Link, useLocation } from 'react-router-dom';

const Navbar = ({ isWsConnected }) => {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path;
  };

  const navLinkClass = (path) => {
    return `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive(path)
        ? 'bg-primary-600 text-white'
        : 'text-gray-700 hover:bg-gray-100'
    }`;
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            {/* Logo */}
            <div className="flex-shrink-0 flex items-center">
              <Link to="/" className="text-xl font-bold text-primary-600">
                🎯 LAYA Calling Agent
              </Link>
            </div>

            {/* Navigation Links */}
            <div className="hidden sm:ml-8 sm:flex sm:space-x-4">
              <Link to="/" className={navLinkClass('/')}>
                לוח בקרה
              </Link>
              <Link to="/leads" className={navLinkClass('/leads')}>
                לידים
              </Link>
              <Link to="/calls" className={navLinkClass('/calls')}>
                שיחות
              </Link>
              <Link to="/analytics" className={navLinkClass('/analytics')}>
                אנליטיקה
              </Link>
            </div>
          </div>

          {/* Right side - Connection Status */}
          <div className="flex items-center">
            <div className="flex items-center space-x-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  isWsConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              ></span>
              <span className="text-sm text-gray-600">
                {isWsConnected ? 'מחובר' : 'מנותק'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
