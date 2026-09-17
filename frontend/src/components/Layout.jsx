import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ROUTES } from '../constants/routes';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate(ROUTES.LOGIN);
  };

  // --- DYNAMIC AVATAR GENERATOR ---
  // Strips out "Dr." and grabs the first letter of the first and last name
  const getInitials = (name) => {
    if (!name) return 'DR';
    const cleanName = name.replace(/^Dr\.?\s+/i, '').trim();
    const parts = cleanName.split(' ');
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return parts[0].substring(0, 2).toUpperCase();
  };

  return (
    <div className="flex h-screen w-screen bg-gray-50 overflow-hidden">

      {/* ========================================== */}
      {/* HOVER-EXPAND SIDEBAR */}
      {/* ========================================== */}
      {/*
        How it works:
        - Base width is w-20 (just icons).
        - 'group' class tracks the hover state of the entire sidebar.
        - On hover, width smoothly expands to w-64.
      */}
      <aside className="w-20 hover:w-64 group flex flex-col bg-white border-r border-gray-200 transition-all duration-300 ease-in-out z-50 shrink-0 shadow-sm relative">

        {/* DOCTOR PROFILE BADGE */}
        <div className="p-4 border-b border-gray-100 flex items-center gap-4 whitespace-nowrap overflow-hidden min-h-[80px]">
          {/* Dynamic Initials Avatar */}
          <div className="w-12 h-12 shrink-0 rounded-full bg-primary/10 text-primary flex items-center justify-center font-black text-lg border border-primary/20 shadow-inner">
            {getInitials(user?.name)}
          </div>

          {/* Text fades in on group-hover */}
          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-75">
            <p className="font-bold text-gray-900 truncate w-40">
              {user?.name?.includes('Dr.') ? user.name : `Dr. ${user?.name || 'Doctor'}`}
            </p>
            <p className="text-xs text-gray-500 truncate w-40 font-medium">
              {user?.specialty || 'General Practice'}
            </p>
          </div>
        </div>

        {/* NAVIGATION LINKS */}
        <nav className="flex-1 py-6 flex flex-col gap-2 px-3 overflow-y-auto overflow-x-hidden custom-scrollbar">
          <NavItem to={ROUTES.DASHBOARD} icon="dashboard" label="Dashboard" />
          <NavItem to={ROUTES.PATIENTS} icon="groups" label="Patient Roster" />
          <NavItem to={ROUTES.NEW_DIAGNOSIS} icon="assignment_add" label="New Diagnosis" />
          <NavItem to={ROUTES.REPORTS} icon="folder_open" label="Reports & History" />
        </nav>

        {/* BOTTOM ACTIONS (SETTINGS & LOGOUT) */}
        <div className="p-3 border-t border-gray-100 flex flex-col gap-2 bg-white">
          <NavItem to={ROUTES.SETTINGS} icon="settings" label="Settings" />
          <button
            onClick={handleLogout}
            className="flex items-center gap-4 px-3 py-3 rounded-lg text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors whitespace-nowrap overflow-hidden"
          >
            <span className="material-symbols-outlined shrink-0">logout</span>
            <span className="font-bold opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-75">Logout</span>
          </button>
        </div>
      </aside>

      {/* ========================================== */}
      {/* MAIN CONTENT AREA */}
      {/* ========================================== */}
      <main className="flex-1 relative h-full overflow-hidden flex flex-col">
        <Outlet />
      </main>

    </div>
  );
}

// --- REUSABLE NAV ITEM COMPONENT ---
function NavItem({ to, icon, label }) {
  // If a route hasn't been defined yet, fallback to a safe hash to prevent crashes
  const safeTo = to || '#';

  return (
    <NavLink
      to={safeTo}
      className={({ isActive }) =>
        `flex items-center gap-4 px-3 py-3 rounded-lg transition-all whitespace-nowrap overflow-hidden ${
          isActive
            ? 'bg-primary/10 text-primary font-bold shadow-sm'
            : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900 font-medium'
        }`
      }
    >
      <span className="material-symbols-outlined shrink-0 text-xl">{icon}</span>
      <span className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-75 tracking-wide">
        {label}
      </span>
    </NavLink>
  );
}