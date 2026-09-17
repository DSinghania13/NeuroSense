import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import Button from '../components/ui/Button';
import ReportTable from '../components/ReportTable';
import ReportPreview from '../components/ReportPreview';
import { useAuth } from '../context/AuthContext';
import { ROUTES } from '../constants/routes';

export default function Reports() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null); // Defaults to null (hidden)
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAllReports = async () => {
      if (!user?.doctor_id) return;
      setIsLoading(true);

      try {
        const patRes = await fetch(`/api/doctors/${user.doctor_id}/patients`);
        const patients = await patRes.json();

        let combinedReports = [];

        for (const patient of patients) {
          const repRes = await fetch(`/api/patients/${patient.patient_id}/reports`);
          const patientReports = await repRes.json();

          const formattedReports = patientReports.map((report, index) => {
            const testKeys = ['free_speech', 'picture_description', 'story_recall', 'memory_qna'];

            const validTestKeys = testKeys.filter(k => report[k] && typeof report[k] === 'object' && !report[k].error);

            let isInvalid = false;
            if (validTestKeys.length === 0) {
              isInvalid = true;
            } else {
              isInvalid = validTestKeys.every(k => {
                const transcript = report[k].transcript || report[k].transcripts?.immediate || "";
                return transcript.trim().length < 5;
              });
            }

            let calculatedRisk = 'Low Risk';
            if (isInvalid) {
              calculatedRisk = 'Invalid';
            } else {
              const hasHighRisk = validTestKeys.some(k => report[k]?.composite?.risk_band === 'High' || report[k]?.risk_level === 'high_risk' || report[k]?.memory_analysis?.memory_status === 'high_risk');
              const hasMCI = validTestKeys.some(k => report[k]?.composite?.risk_band === 'MCI' || report[k]?.risk_level === 'mci' || report[k]?.memory_analysis?.memory_status === 'mci');

              if (hasHighRisk) calculatedRisk = 'High Risk';
              else if (hasMCI) calculatedRisk = 'Elevated Risk';
            }

            const dynamicConfidence = calculatedRisk === 'Invalid' ? 0 : Math.min(98, 70 + (validTestKeys.length * 6));

            return {
              ...report,
              id: report.session_id || `legacy-${patient.patient_id}-${index}`,
              name: patient.name || 'Anonymous',
              patient_id: patient.patient_id,
              date: report.created_at ? new Date(report.created_at).toLocaleDateString() : 'Unknown Date',
              status: report.status || 'Completed',
              risk: calculatedRisk,
              result: calculatedRisk,
              confidence: dynamicConfidence,
              notes: isInvalid ? "Assessment incomplete: No readable audio detected." : (report.notes || "No clinical anomalies explicitly noted outside of standard metrics.")
            };
          });

          combinedReports = [...combinedReports, ...formattedReports];
        }

        combinedReports.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)).reverse();

        setReports(combinedReports);

        // ---> FIX: Removed the line that was auto-setting setSelectedReport(combinedReports[0]) here! <---

      } catch (err) {
        console.error("Failed to load reports from database", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAllReports();
  }, [user]);

  const filteredReports = reports.filter((r) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      (r.name && r.name.toLowerCase().includes(q)) ||
      (r.patient_id && r.patient_id.toLowerCase().includes(q)) ||
      (r.id && r.id.toLowerCase().includes(q))
    );
  });

  useEffect(() => {
    if (searchQuery.trim() !== '') {
      if (filteredReports.length === 0) {
        setSelectedReport(null);
      } else if (!filteredReports.find(r => r.id === selectedReport?.id)) {
        setSelectedReport(filteredReports[0]);
      }
    }
  }, [searchQuery, filteredReports.length]);

  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-gray-50/50">
      <PageHeader
        title="Patient Reports"
        description="Review, manage, and generate diagnostic reports."
        actions={
          <Button icon="add_circle" onClick={() => navigate(ROUTES.NEW_DIAGNOSIS)} className="h-10 px-4">
            Generate New Report
          </Button>
        }
      />

      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        <div className="flex-1 flex flex-col p-6 lg:p-8 overflow-y-auto min-w-0">

          <div className="w-full sm:max-w-md mb-6 relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">search</span>
            <input
              type="text"
              placeholder="Search by patient name, ID, or session..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white py-3 pl-10 pr-4 text-gray-900 focus:ring-2 focus:ring-primary outline-none transition-shadow shadow-sm"
            />
          </div>

          {isLoading ? (
            <div className="flex flex-col items-center justify-center p-10 text-gray-500">
              <span className="material-symbols-outlined text-4xl animate-spin mb-4 text-primary">autorenew</span>
              <p>Loading clinical records...</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="text-center p-10 text-gray-500 bg-white rounded-xl border border-dashed border-gray-300 shadow-sm">
              <span className="material-symbols-outlined text-4xl mb-2 text-gray-400">folder_open</span>
              <p>No reports found. Complete a diagnostic test to see records here.</p>
            </div>
          ) : (
            <ReportTable
              reports={filteredReports}
              selectedReport={selectedReport}
              onSelect={setSelectedReport}
            />
          )}
        </div>

        {selectedReport && (
          <ReportPreview
            report={selectedReport}
            onClose={() => setSelectedReport(null)}
          />
        )}
      </div>
    </div>
  );
}