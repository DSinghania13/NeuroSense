import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { ROUTES } from '../constants/routes';
import { useAuth } from '../context/AuthContext';
import { LuClipboardCheck } from "react-icons/lu";

const navItems = [
  { to: ROUTES.DASHBOARD, icon: 'dashboard', label: 'Dashboard' },
  { to: ROUTES.PATIENTS, icon: 'group', label: 'Patients' },
  { to: ROUTES.NEW_DIAGNOSIS, icon: <LuClipboardCheck />, label: 'New Diagnosis' },
  { to: ROUTES.REPORTS, icon: 'folder_open', label: 'Reports & History' },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate(ROUTES.LOGIN);
  };

  return (
    <aside className="flex w-64 flex-col bg-card border-r border-border p-4 flex-shrink-0 relative z-20">
      <div className="flex flex-col gap-4 flex-grow">
        {/* Profile Section */}
        <div className="flex items-center gap-3 px-3 py-2">
          <div
            className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 shadow-sm border border-border"
            style={{
              backgroundImage:
                'url("https://lh3.googleusercontent.com/aida-public/AB6AXuCrSBR4vofJmKfekvexTlVyrX4Nhyo8m0cgJ9Q5iRpT5cvsEAvf-emp3b9WbPTIBXhwHzw6gLnqxyHhGpC4ay9vIOBInnsIsir5uA5FTEdcjaTqKlzhiiAou-c53DO7mENjQPgBsNv9f_qWixSygGJMUnzNgucY_w-LVEUCh4InEj-BnaET21pvLxaj8oHMDlZcAlqewu88gL7gHO2Hh8CauOeTm-4rI9gucyMm4RWf_qDyDXtp14vWLJgQbvK3dvgeJI2w7kKZy_4")',
            }}
            aria-label={`Profile picture of ${user?.name || 'Doctor'}`}
          />
          <div className="flex flex-col">
            <h1 className="text-text-primary text-base font-bold leading-normal truncate max-w-[130px]">
              {user?.name || 'Dr. Evelyn Reed'}
            </h1>
            <p className="text-text-secondary text-sm font-normal leading-normal truncate max-w-[130px]">
              {user?.role || 'Neurologist'}
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-2 mt-4">
          {navItems.map((item) => {
            const isActive =
              item.to === ROUTES.DASHBOARD
                ? location.pathname === ROUTES.DASHBOARD
                : location.pathname.startsWith(item.to);

            return (
              <NavLink
                key={item.label}
                to={item.to}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-sidebar-active-bg text-primary font-bold shadow-sm'
                    : 'text-text-secondary hover:bg-sidebar-hover hover:text-primary font-medium'
                }`}
              >
                <span className={`material-symbols-outlined text-xl ${isActive ? 'filled' : ''}`}>
                  {item.icon}
                </span>
                <p className="text-sm leading-normal">{item.label}</p>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Bottom Links */}
      <div className="flex flex-col gap-2 mt-auto pt-4 border-t border-border">
        <NavLink
          to={ROUTES.SETTINGS}
          className={({ isActive }) => `flex items-center gap-3 p-3 rounded-lg ${isActive ? 'bg-primary/10 text-primary' : 'hover:bg-gray-100 text-text-secondary'}`}
        >

          <span className="material-symbols-outlined text-xl">settings</span>
          <p className="text-sm font-medium leading-normal">Settings</p>
        </NavLink>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 text-risk-high hover:bg-red-50 hover:text-red-700 rounded-lg transition-colors w-full text-left font-medium group"
        >
          <span className="material-symbols-outlined text-xl group-hover:scale-110 transition-transform">
            logout
          </span>
          <p className="text-sm leading-normal">Logout</p>
        </button>
      </div>
    </aside>
  );
}
