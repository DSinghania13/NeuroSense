import { useState } from 'react';
import PageHeader from '../components/PageHeader';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';

export default function Settings() {
  const { user } = useAuth();
  const { notify, browserEnabled, setBrowserEnabled } = useNotification();

  const [activeTab, setActiveTab] = useState('profile');

  // -- PROFILE STATE --
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    specialty: user?.specialty || '',
    clinic_name: user?.clinic_name || ''
  });

  // -- SECURITY STATE --
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);
  const [passwords, setPasswords] = useState({
    current: '',
    new: '',
    confirm: ''
  });

  // ==========================================
  // HANDLERS
  // ==========================================

  const handleSaveProfile = (e) => {
    e.preventDefault();
    setIsSavingProfile(true);

    // Simulate API call for profile (Wire this to a real PUT route later if you want!)
    setTimeout(() => {
      setIsSavingProfile(false);
      // ---> FIRE SUCCESS NOTIFICATION!
      notify("Profile Saved", "Your clinical profile has been successfully updated.", "success");
    }, 800);
  };

  const handleUpdatePassword = async (e) => {
    e.preventDefault();

    if (passwords.new !== passwords.confirm) {
      notify("Password Error", "New passwords do not match. Please try again.", "error");
      return;
    }

    if (passwords.new.length < 6) {
      notify("Weak Password", "New password must be at least 6 characters long.", "error");
      return;
    }

    setIsUpdatingPassword(true);

    try {
      const res = await fetch(`/api/doctors/${user.doctor_id}/password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: passwords.current,
          new_password: passwords.new
        })
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "Failed to update password");

      // ---> FIRE SUCCESS NOTIFICATION!
      notify("Security Updated", "Your password has been successfully changed.", "success");
      setPasswords({ current: '', new: '', confirm: '' }); // Clear the form

    } catch (err) {
      notify("Update Failed", err.message, "error");
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  const handleTogglePush = async () => {
    if (!browserEnabled) {
      if (!('Notification' in window)) {
        notify("Unsupported", "This browser does not support desktop notifications.", "error");
        return;
      }
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        setBrowserEnabled(true);
        localStorage.setItem('notify_browser', 'true');
        notify("Notifications Enabled", "You will now receive alerts when diagnostic reports finish.", "success");
      } else {
        notify("Permission Denied", "You must allow notifications in your browser settings first.", "error");
      }
    } else {
      setBrowserEnabled(false);
      localStorage.setItem('notify_browser', 'false');
      // ---> FIRE DISABLE NOTIFICATION!
      notify("Notifications Paused", "Desktop alerts have been turned off.", "info");
    }
  };

  // ==========================================
  // RENDER
  // ==========================================

  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-gray-50/50">
      <PageHeader
        title="Settings & Preferences"
        description="Manage your clinical profile and account security."
      />

      <div className="flex-grow p-6 lg:p-10">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row gap-8">

          {/* SIDEBAR TABS */}
          <div className="w-full md:w-64 shrink-0">
            <Card noPadding className="overflow-hidden">
              <nav className="flex flex-col">
                <button onClick={() => setActiveTab('profile')} className={`flex items-center gap-3 p-4 text-left font-medium transition-colors ${activeTab === 'profile' ? 'bg-primary/10 text-primary border-l-4 border-primary' : 'text-text-secondary hover:bg-gray-50 border-l-4 border-transparent'}`}>
                  <span className="material-symbols-outlined">person</span> My Profile
                </button>
                <button onClick={() => setActiveTab('security')} className={`flex items-center gap-3 p-4 text-left font-medium transition-colors ${activeTab === 'security' ? 'bg-primary/10 text-primary border-l-4 border-primary' : 'text-text-secondary hover:bg-gray-50 border-l-4 border-transparent'}`}>
                  <span className="material-symbols-outlined">lock</span> Security
                </button>
                <button onClick={() => setActiveTab('notifications')} className={`flex items-center gap-3 p-4 text-left font-medium transition-colors ${activeTab === 'notifications' ? 'bg-primary/10 text-primary border-l-4 border-primary' : 'text-text-secondary hover:bg-gray-50 border-l-4 border-transparent'}`}>
                  <span className="material-symbols-outlined">notifications</span> Notifications
                </button>
              </nav>
            </Card>
          </div>

          {/* MAIN CONTENT AREA */}
          <div className="flex-1">

            {/* PROFILE TAB */}
            {activeTab === 'profile' && (
              <Card>
                <div className="mb-6">
                  <h2 className="text-xl font-bold text-text-primary">Clinical Profile</h2>
                  <p className="text-sm text-text-secondary">Update your professional details and clinic association.</p>
                </div>

                <form onSubmit={handleSaveProfile} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Input id="name" label="Full Name (Dr.)" value={profileData.name} onChange={(e) => setProfileData({...profileData, name: e.target.value})} />
                    <Input id="email" type="email" label="Email Address" value={profileData.email} onChange={(e) => setProfileData({...profileData, email: e.target.value})} />
                    <Input id="specialty" label="Medical Specialty" value={profileData.specialty} onChange={(e) => setProfileData({...profileData, specialty: e.target.value})} />
                    <Input id="clinic" label="Clinic / Hospital Name" value={profileData.clinic_name} onChange={(e) => setProfileData({...profileData, clinic_name: e.target.value})} />
                  </div>

                  <div className="border-t border-border pt-6 flex justify-end">
                    <Button type="submit" disabled={isSavingProfile} className="h-12 px-8">
                      {isSavingProfile ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </div>
                </form>
              </Card>
            )}

            {/* SECURITY TAB */}
            {activeTab === 'security' && (
              <Card>
                <div className="mb-6">
                  <h2 className="text-xl font-bold text-text-primary">Change Password</h2>
                  <p className="text-sm text-text-secondary">Ensure your account uses a strong, secure password.</p>
                </div>

                <form onSubmit={handleUpdatePassword} className="space-y-6 max-w-md">
                  <Input type="password" id="current-pass" label="Current Password" placeholder="••••••••" required value={passwords.current} onChange={e => setPasswords({...passwords, current: e.target.value})} />
                  <Input type="password" id="new-pass" label="New Password" placeholder="••••••••" required value={passwords.new} onChange={e => setPasswords({...passwords, new: e.target.value})} />
                  <Input type="password" id="confirm-pass" label="Confirm New Password" placeholder="••••••••" required value={passwords.confirm} onChange={e => setPasswords({...passwords, confirm: e.target.value})} />
                  <Button type="submit" disabled={isUpdatingPassword} className="h-12 w-full">
                    {isUpdatingPassword ? 'Updating...' : 'Update Password'}
                  </Button>
                </form>
              </Card>
            )}

            {/* NOTIFICATIONS TAB */}
            {activeTab === 'notifications' && (
              <Card>
                <div className="mb-6">
                  <h2 className="text-xl font-bold text-text-primary">Notification Preferences</h2>
                  <p className="text-sm text-text-secondary">Control how NeuroSense alerts you.</p>
                </div>

                <div className="space-y-4">
                  <label className="flex items-center justify-between p-4 border border-border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                    <div>
                      <h4 className="font-bold text-text-primary text-sm">Desktop Push Notifications</h4>
                      <p className="text-xs text-text-secondary">Get an OS-level alert when background AI processing completes.</p>
                    </div>
                    <input type="checkbox" checked={browserEnabled} onChange={handleTogglePush} className="w-5 h-5 text-primary focus:ring-primary rounded cursor-pointer" />
                  </label>

                  <label className="flex items-center justify-between p-4 border border-border rounded-lg cursor-pointer hover:bg-gray-50 opacity-60">
                    <div>
                      <h4 className="font-bold text-text-primary text-sm">System Updates (Coming Soon)</h4>
                      <p className="text-xs text-text-secondary">Receive email alerts about NeuroSense platform updates.</p>
                    </div>
                    <input type="checkbox" disabled className="w-5 h-5 rounded cursor-not-allowed" />
                  </label>
                </div>
              </Card>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}