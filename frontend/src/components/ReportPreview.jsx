import { useNavigate } from 'react-router-dom';
import { ROUTES } from '../constants/routes';

export default function ReportPreview({ report, onClose }) {
  const navigate = useNavigate();

  if (!report) return null;

  const getRiskColor = (risk) => {
    if (risk === 'Invalid') return 'text-gray-500';
    if (risk?.includes('High')) return 'text-red-600';
    if (risk?.includes('Elevated') || risk?.includes('MCI')) return 'text-orange-500';
    return 'text-green-600';
  };

  const handleOpenFullReport = () => {
    navigate(ROUTES.DIAGNOSIS_RESULT, {
      state: {
        sessionId: report.id,
        patientData: { name: report.name, patient_id: report.patient_id, gender: report.gender, dob: report.age }
      }
    });
  };

  return (
    <div className="w-full lg:w-[380px] bg-white border-l border-gray-200 flex flex-col h-full shrink-0 shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)] z-10 overflow-y-auto">

      {/* Header with Close Button */}
      <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gray-50/50 sticky top-0 z-20">
        <h2 className="text-xl font-bold text-gray-900">Report Overview</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-red-500 transition-colors p-1 rounded-full hover:bg-red-50 flex items-center justify-center"
          title="Close Preview"
        >
          <span className="material-symbols-outlined">close</span>
        </button>
      </div>

      <div className="p-6 flex flex-col gap-6 flex-grow">

        {/* Identity Details */}
        <div className="bg-gray-50 p-4 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Patient Name</p>
            <p className="text-gray-900 font-bold text-lg">{report.name}</p>
          </div>
          <div>
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Patient ID</p>
            <p className="text-gray-700 font-mono text-sm">{report.patient_id || 'N/A'}</p>
          </div>
          <div>
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Date of Assessment</p>
            <p className="text-gray-700 text-sm">{report.date}</p>
          </div>
        </div>

        {/* Clinical Result */}
        <div>
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Diagnostic Result</p>
          <p className={`text-xl font-black ${getRiskColor(report.result)}`}>
            {report.result?.toUpperCase() || 'UNKNOWN'}
          </p>
        </div>

        {/* Confidence Bar */}
        <div>
          <div className="flex justify-between items-end mb-2">
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">AI Confidence Matrix</p>
            <span className="text-sm font-bold text-primary">{report.confidence || 0}%</span>
          </div>
          <div className="w-full h-2.5 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-primary transition-all duration-1000" style={{ width: `${report.confidence || 0}%` }}></div>
          </div>
        </div>

        {/* Notes */}
        <div>
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Clinical Notes</p>
          <div className="bg-blue-50/50 p-4 rounded-lg border border-blue-100 text-sm text-gray-600 leading-relaxed">
            {report.notes}
          </div>
        </div>
      </div>

      {/* Footer Action */}
      <div className="p-6 border-t border-gray-100 bg-white sticky bottom-0 z-20">
        <button
          onClick={handleOpenFullReport}
          className="w-full py-3.5 bg-primary/10 hover:bg-primary text-primary hover:text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2 shadow-sm"
        >
          <span className="material-symbols-outlined text-lg">description</span>
          Open Full Clinical Report
        </button>
      </div>
    </div>
  );
}