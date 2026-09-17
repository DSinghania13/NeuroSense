import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import { actionCards } from '../data/mockData';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { user } = useAuth();
  const [activities, setActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Wake up the AI models silently
  useEffect(() => {
    fetch('/api/warmup').catch(err => console.log("Warmup ping failed:", err));
  }, []);

  // Fetch the real Audit Trail
  useEffect(() => {
    if (user?.doctor_id) {
      fetch(`/api/doctors/${user.doctor_id}/activity`)
        .then(res => res.json())
        .then(data => {
          setActivities(data);
          setIsLoading(false);
        })
        .catch(err => {
          console.error("Failed to load activity", err);
          setIsLoading(false);
        });
    }
  }, [user]);

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  };

  return (
    <div className="flex-1 flex flex-col overflow-y-auto">
      <PageHeader
        title={`Welcome back, ${user?.name || 'Doctor'}!`}
        description={user?.specialty && user?.clinic_name ? `${user.specialty} @ ${user.clinic_name}` : "NeuroSense Clinical Dashboard"}
        actions={
          <div className="w-full sm:w-80">
            <Input id="dashboard-search" icon="search" placeholder="Search for patients or reports" wrapperClassName="w-full" />
          </div>
        }
      />

      <div className="flex-grow p-6 lg:p-10">
        <div className="max-w-7xl mx-auto space-y-10">

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {actionCards.map((card) => (
              <Link key={card.title} to={card.to} className="block group no-underline">
                <Card className="h-full flex flex-col gap-4 border-transparent hover:border-primary hover:shadow-lg transition-all cursor-pointer">
                  <span className="material-symbols-outlined text-primary text-3xl group-hover:scale-110 transition-transform origin-left">{card.icon}</span>
                  <div className="flex flex-col gap-1">
                    <h2 className="text-text-primary text-lg font-bold leading-tight group-hover:text-primary transition-colors">{card.title}</h2>
                    <p className="text-text-secondary text-sm font-normal leading-normal">{card.description}</p>
                  </div>
                </Card>
              </Link>
            ))}
          </div>

          <section>
            <h2 className="text-text-primary text-xl font-bold mb-4">
              {activities.length > 0 ? "Recent Activity" : "Quick Insights"}
            </h2>

            {isLoading ? (
               <div className="text-center p-8 text-gray-500"><span className="material-symbols-outlined animate-spin">autorenew</span></div>
            ) : activities.length === 0 ? (
              // NO HISTORY YET -> SHOW ONBOARDING INSIGHTS
              <Card className="bg-blue-50/50 border-blue-200 p-8 text-center">
                <span className="material-symbols-outlined text-5xl text-blue-400 mb-4">health_metrics</span>
                <h3 className="text-lg font-bold text-gray-800">Ready for Diagnosis</h3>
                <p className="text-gray-600 mt-2">
                  Use the sidebar to navigate to your <strong>Patients Directory</strong> to add new profiles, or jump straight into a <strong>New Diagnosis</strong>.
                </p>
              </Card>
            ) : (
              // HISTORY EXISTS -> SHOW THE LIVE TIMELINE
              <Card noPadding>
                <ul className="divide-y divide-border">
                  {activities.map((item, index) => (
                    <li key={index} className="p-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 hover:bg-background transition-colors first:rounded-t-lg last:rounded-b-lg">
                      <div className="flex items-center gap-4">
                        <div className="bg-primary/10 text-primary size-10 flex items-center justify-center rounded-full shrink-0">
                          <span className="material-symbols-outlined text-[20px]">{item.icon || 'info'}</span>
                        </div>
                        <div>
                          <p className="font-semibold text-text-primary text-sm sm:text-base">
                            {item.title}
                          </p>
                          <p className="text-xs sm:text-sm text-text-secondary">{item.subtitle}</p>
                        </div>
                      </div>
                      <p className="text-xs sm:text-sm text-text-secondary shrink-0 font-mono">
                        {formatTime(item.timestamp)}
                      </p>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </section>

        </div>
      </div>
    </div>
  );
}