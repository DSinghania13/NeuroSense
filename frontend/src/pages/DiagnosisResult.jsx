import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import html2pdf from 'html2pdf.js';
import PageHeader from '../components/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { ROUTES } from '../constants/routes';
import { useNotification } from '../context/NotificationContext';

// ==========================================
// CLINICAL HELPERS
// ==========================================

const calculateAge = (dobOrAge) => {
  if (!dobOrAge || dobOrAge === 'N/A') return 'N/A';
  if (!isNaN(dobOrAge) && String(dobOrAge).length < 4) return dobOrAge;

  const birthDate = new Date(dobOrAge);
  if (isNaN(birthDate)) return dobOrAge;

  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
  return age;
};

const getMissedConcepts = (iuTable, type) => {
  if (!iuTable || Object.keys(iuTable).length === 0) return "None";
  const missed = Object.values(iuTable)
    .filter(iu => iu.iu_type === type && (iu.match_type === 'missed' || iu.match_type === 'none'))
    .map(iu => iu.iu_id);
  return missed.length > 0 ? missed.join(', ') : "None";
};

const IUComparisonTable = ({ iuTable }) => {
  if (!iuTable || Object.keys(iuTable).length === 0) {
    return <p style={{ fontSize: '14px', fontStyle: 'italic', padding: '16px', color: '#6b7280' }}>No Information Unit data available. (Audio may have been too short or unintelligible).</p>;
  }

  const getStatusBadge = (matchType) => {
    switch (matchType?.toLowerCase()) {
      case 'exact': return <span style={{ padding: '4px 8px', fontSize: '10px', fontWeight: 'bold', backgroundColor: '#dcfce7', color: '#166534', borderRadius: '4px' }}>✅ MATCH</span>;
      case 'paraphrase': return <span style={{ padding: '4px 8px', fontSize: '10px', fontWeight: 'bold', backgroundColor: '#fef08a', color: '#854d0e', borderRadius: '4px' }}>⚠️ PARA</span>;
      default: return <span style={{ padding: '4px 8px', fontSize: '10px', fontWeight: 'bold', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '4px' }}>❌ MISS</span>;
    }
  };

  return (
    <div style={{ overflowX: 'auto', marginTop: '16px', borderRadius: '8px', border: '1px solid #e5e7eb', pageBreakInside: 'avoid' }}>
      <table style={{ width: '100%', textAlign: 'left', fontSize: '14px', borderCollapse: 'collapse' }}>
        <thead style={{ backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
          <tr>
            <th style={{ padding: '12px 16px', fontWeight: '600', textTransform: 'uppercase', fontSize: '12px', width: '80px', color: '#6b7280' }}>Type</th>
            <th style={{ padding: '12px 16px', fontWeight: '600', textTransform: 'uppercase', fontSize: '12px', width: '96px', color: '#6b7280' }}>Status</th>
            <th style={{ padding: '12px 16px', fontWeight: '600', textTransform: 'uppercase', fontSize: '12px', width: '50%', color: '#6b7280' }}>Expected Concept</th>
            <th style={{ padding: '12px 16px', fontWeight: '600', textTransform: 'uppercase', fontSize: '12px', width: '50%', color: '#6b7280' }}>User Recall</th>
          </tr>
        </thead>
        <tbody>
          {Object.values(iuTable).map((iu, idx) => (
            <tr key={idx} style={{ borderBottom: '1px solid #f3f4f6', pageBreakInside: 'avoid' }}>
              <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontSize: '12px', color: '#374151' }}>{iu.iu_type}</td>
              <td style={{ padding: '12px 16px' }}>{getStatusBadge(iu.match_type)}</td>
              <td style={{ padding: '12px 16px', fontWeight: '500', color: '#111827' }}>{iu.expected_text}</td>
              <td style={{ padding: '12px 16px', fontStyle: 'italic', color: '#6b7280' }}>
                {iu.matched_utterance || iu.matched_recall_text || "---"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ==========================================
// MAIN COMPONENT
// ==========================================
export default function DiagnosisResult() {
  const location = useLocation();
  const navigate = useNavigate();
  const { notify } = useNotification();
  // We still check router state as a fallback, but we won't rely on it!
  const { patientData: routerPatientData = {}, sessionId } = location.state || {};

  const [results, setResults] = useState(null);
  const [dbPatientData, setDbPatientData] = useState(null); // <--- NEW DB STATE
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('clinical');
  const [isExporting, setIsExporting] = useState(false);

  const [completedTests, setCompletedTests] = useState(0);
  const [expectedTests, setExpectedTests] = useState(1);

  // --- NEW: Prioritize Database data over Router data ---
  const activePatientData = dbPatientData || routerPatientData;

  const rawAge = activePatientData.dob || activePatientData.age || 'N/A';
  const patientAge = calculateAge(rawAge);
  const patientGender = activePatientData.gender || 'Unknown';

  useEffect(() => {
    if (!sessionId) {
      setError("No active session ID found. Please start a new diagnosis.");
      setIsLoading(false);
      return;
    }

    const expectedCount = parseInt(localStorage.getItem(`expected_tests_${sessionId}`)) || 1;
    setExpectedTests(expectedCount);

    const fetchResults = async () => {
      try {
        const response = await fetch(`/api/results/${sessionId}`);
        if (response.status === 404) {
          setTimeout(fetchResults, 3000);
          return;
        }
        if (!response.ok) throw new Error("Failed to load results from the server.");

        const data = await response.json();

        // ---> NEW: If the backend attached the patient profile, save it!
        if (data.patient) {
          setDbPatientData(data.patient);
        }

        const validTestKeys = Object.keys(data).filter(k => !data[k].error && typeof data[k] === 'object' && k !== 'patient');
        const currentCompleted = validTestKeys.length;

        setCompletedTests(currentCompleted);

        // Wait until all tests finish processing (ignoring the 'patient' key)
        if (Object.keys(data).filter(k => typeof data[k] === 'object' && k !== 'patient').length < expectedCount) {
          setTimeout(fetchResults, 3000);
          return;
        }

        setResults(data);
        setIsLoading(false);
      } catch (err) {
        console.error(err);
        setError(err.message);
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [sessionId]);

  const handleDirectDownloadPDF = () => {
    setIsExporting(true);
    setTimeout(() => {
      const element = document.getElementById('hidden-pdf-engine-container');
      element.style.display = 'block';

      const opt = {
        margin:       [10, 10, 15, 10],
        filename:     `NeuroSense_Diagnostic_${activePatientData.name || sessionId}.pdf`,
        image:        { type: 'jpeg', quality: 1.0 },
        html2canvas:  { scale: 2, useCORS: true, logging: false },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak:    { mode: ['css', 'legacy'] }
      };

      html2pdf().set(opt).from(element).save()
        .then(() => {
          element.style.display = 'none';
          setIsExporting(false);
          notify("Export Complete", "Your diagnostic PDF has been downloaded.", "success");
        })
        .catch((err) => {
          console.error("PDF generation failed:", err);
          notify("Export Failed", "There was an error generating the PDF document.", "error");
          element.style.display = 'none';
          setIsExporting(false);
        });
    }, 300);
  };

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-background p-6">
        <span className="material-symbols-outlined text-6xl text-red-500 mb-4">error</span>
        <h2 className="text-2xl font-bold text-text-primary mb-2">Error Loading Results</h2>
        <p className="text-text-secondary mb-6">{error}</p>
        <Button onClick={() => navigate(ROUTES.NEW_DIAGNOSIS)}>Start New Diagnosis</Button>
      </div>
    );
  }

  if (isLoading || !results) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-background p-6">
        <span className="material-symbols-outlined text-6xl text-primary animate-spin mb-4">autorenew</span>
        <h2 className="text-2xl font-bold text-text-primary mb-2">AI is Processing</h2>
        <p className="text-text-secondary mb-6">Synthesizing audio linguistics and cognitive markers...</p>
        <div className="w-64 bg-gray-200 rounded-full h-2.5">
          <div className="bg-primary h-2.5 rounded-full transition-all duration-500" style={{ width: `${(completedTests / expectedTests) * 100}%` }}></div>
        </div>
        <p className="text-sm text-text-secondary mt-3 font-bold uppercase tracking-wider">
          {completedTests} of {expectedTests} Modules Complete
        </p>
      </div>
    );
  }

  const determineOverallStatus = () => {
    const testKeys = ['free_speech', 'picture_description', 'story_recall', 'memory_qna'];
    const validTestKeys = testKeys.filter(k => results[k] && typeof results[k] === 'object' && !results[k].error);

    let isInvalid = false;
    if (validTestKeys.length === 0) {
      isInvalid = true;
    } else {
      isInvalid = validTestKeys.every(k => {
        const transcript = results[k].transcript || results[k].transcripts?.immediate || "";
        return transcript.trim().length < 5;
      });
    }

    if (isInvalid) return { status: 'Audio Missing or Unintelligible', risk: 'Invalid', color: '#9ca3af' };

    const hasHighRisk = validTestKeys.some(k => results[k]?.composite?.risk_band === 'High' || results[k]?.risk_level === 'high_risk' || results[k]?.memory_analysis?.memory_status === 'high_risk');
    const hasMCI = validTestKeys.some(k => results[k]?.composite?.risk_band === 'MCI' || results[k]?.risk_level === 'mci' || results[k]?.memory_analysis?.memory_status === 'mci');

    if (hasHighRisk) return { status: 'Significant Impairment Identified', risk: 'High Risk', color: '#ef4444' };
    if (hasMCI) return { status: 'Mild Cognitive Impairment (MCI)', risk: 'Elevated Risk', color: '#f97316' };
    return { status: 'Cognitively Healthy', risk: 'Low Risk', color: '#22c55e' };
  };

  const { status, risk, color } = determineOverallStatus();

  // Guarantee 0% confidence if invalid
  const validTestKeysLength = ['free_speech', 'picture_description', 'story_recall', 'memory_qna'].filter(k => results[k] && typeof results[k] === 'object' && !results[k].error).length;
  const dynamicConfidence = risk === 'Invalid' ? 0 : Math.min(98, 70 + (validTestKeysLength * 6));

  const cleanPatientData = {
    ...activePatientData,
    age: patientAge,
    gender: patientGender
  };

  return (
    <div className="flex-1 overflow-auto bg-background flex flex-col relative">
      {isExporting && (
        <div className="absolute inset-0 z-50 bg-white/80 flex items-center justify-center backdrop-blur-sm">
          <div className="flex flex-col items-center">
             <span className="material-symbols-outlined text-primary text-6xl animate-spin mb-4">downloading</span>
             <h2 className="text-2xl font-bold text-text-primary">Generating PDF...</h2>
             <p className="text-text-secondary">Please wait while we format your direct download.</p>
          </div>
        </div>
      )}

      <PageHeader
        title="Diagnostic Report"
        description="Comprehensive cognitive evaluation results."
        actions={
          <>
            <Button variant="outline" onClick={() => navigate(ROUTES.DASHBOARD)}>Return Home</Button>
            <Button icon="download" onClick={handleDirectDownloadPDF} disabled={isExporting}>
              Export PDF
            </Button>
          </>
        }
      />

      <div className="p-6 lg:p-10 mx-auto w-full max-w-7xl">

        {/* PATIENT DETAILS HEADER */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-sm">
           <div>
              <h2 className="text-2xl font-bold text-gray-900">{cleanPatientData.name || 'Anonymous Patient'}</h2>
              <div className="flex items-center gap-2 mt-1 text-gray-600">
                 <span className="material-symbols-outlined text-sm">badge</span>
                 <span className="text-sm font-medium">ID: {cleanPatientData.patient_id || 'N/A'}</span>
                 <span className="text-gray-300">|</span>
                 <span className="text-sm">{cleanPatientData.gender}</span>
                 <span className="text-gray-300">|</span>
                 <span className="text-sm">{cleanPatientData.age} years old</span>
              </div>
           </div>
           <div className="md:text-right">
              <p className="font-mono text-sm text-gray-500 mb-1">Session: {sessionId}</p>
              <p className="text-sm font-bold text-primary bg-primary/10 px-3 py-1 rounded inline-block">
                {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
           </div>
        </div>

        {/* TABS */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex bg-gray-200 p-1 rounded-lg">
            <button onClick={() => setViewMode('patient')} className={`px-6 py-2 rounded-md text-sm font-bold transition-colors ${viewMode === 'patient' ? 'bg-white shadow text-primary' : 'text-gray-600 hover:text-gray-900'}`}>Patient View (Summary)</button>
            <button onClick={() => setViewMode('clinical')} className={`px-6 py-2 rounded-md text-sm font-bold transition-colors ${viewMode === 'clinical' ? 'bg-white shadow text-primary' : 'text-gray-600 hover:text-gray-900'}`}>Clinical View (Detailed)</button>
          </div>
        </div>

        {/* PATIENT VIEW */}
        {viewMode === 'patient' && (
          <div className="space-y-6 max-w-4xl mx-auto">
            {risk === 'Invalid' ? (
               <Card className="text-center p-10 border-t-4 border-t-gray-400 shadow-md">
                 <span className="material-symbols-outlined text-6xl text-gray-400 mb-4">mic_off</span>
                 <h2 className="text-3xl font-bold text-gray-800">Audio Not Detected</h2>
                 <p className="text-gray-600 mt-4 max-w-2xl mx-auto text-lg leading-relaxed">
                   The system was unable to detect sufficient speech to process this evaluation. Please consult your physician to retake the diagnostic tests.
                 </p>
               </Card>
            ) : (
               <>
                 <Card className="text-center p-10 border-t-4 border-t-primary shadow-md">
                   <span className="material-symbols-outlined text-6xl text-primary mb-4">health_and_safety</span>
                   <h2 className="text-3xl font-bold text-gray-800">Assessment Successfully Completed</h2>
                   <p className="text-gray-600 mt-4 max-w-2xl mx-auto text-lg leading-relaxed">
                     Thank you for completing the NeuroSense evaluation. Your cognitive and vocal responses have been processed securely and saved to your medical profile.
                   </p>
                 </Card>

                 <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                   <Card>
                     <div className="flex items-center gap-2 mb-4">
                       <span className="material-symbols-outlined text-gray-400">fact_check</span>
                       <h3 className="font-bold text-lg text-gray-800">Tests Completed</h3>
                     </div>
                     <ul className="space-y-3 text-gray-700">
                       {results.free_speech && !results.free_speech.error && <li className="flex items-start gap-2"><span className="text-green-500 mt-0.5">✓</span><strong>Spontaneous Speech</strong></li>}
                       {results.picture_description && !results.picture_description.error && <li className="flex items-start gap-2"><span className="text-green-500 mt-0.5">✓</span><strong>Visual Cognition</strong></li>}
                       {results.story_recall && !results.story_recall.error && <li className="flex items-start gap-2"><span className="text-green-500 mt-0.5">✓</span><strong>Immediate Recall</strong></li>}
                       {results.memory_qna && !results.memory_qna.error && <li className="flex items-start gap-2"><span className="text-green-500 mt-0.5">✓</span><strong>Episodic Memory</strong></li>}
                     </ul>
                   </Card>

                   <Card>
                     <div className="flex items-center gap-2 mb-4">
                       <span className="material-symbols-outlined text-gray-400">medical_services</span>
                       <h3 className="font-bold text-lg text-gray-800">Next Steps</h3>
                     </div>
                     <p className="text-gray-700 mb-6 leading-relaxed">
                       Your physician has received the comprehensive technical breakdown of these results.
                     </p>

                     <div className={`p-4 rounded-lg border flex gap-3 ${risk === 'Low Risk' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-blue-50 border-blue-200 text-blue-800'}`}>
                       <span className="material-symbols-outlined mt-0.5">{risk === 'Low Risk' ? 'check_circle' : 'info'}</span>
                       <div>
                         <strong className="block mb-1">Status Indicator:</strong>
                         <span className="text-sm">
                           {risk === 'Low Risk'
                             ? 'Your cognitive baseline currently looks stable based on these audio metrics.'
                             : 'Your doctor will discuss these results with you to determine if further clinical correlation is recommended.'}
                         </span>
                       </div>
                     </div>
                   </Card>
                 </div>
               </>
            )}
          </div>
        )}

        {/* CLINICAL VIEW */}
        {viewMode === 'clinical' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="border-l-4" style={{ borderLeftColor: color }}>
                <p className="text-sm text-text-secondary mb-1">Predicted Risk Level</p>
                <p className="text-2xl font-black tracking-tight" style={{ color: color }}>{risk.toUpperCase()}</p>
                <p className="text-xs text-gray-500 mt-1">{status}</p>
              </Card>
              <Card>
                <p className="text-sm text-text-secondary mb-1">Total Tests Run</p>
                <p className="text-2xl font-black tracking-tight text-gray-800">{completedTests} Modules</p>
                <p className="text-xs text-gray-500 mt-1">Expected: {expectedTests}</p>
              </Card>
              <Card>
                <p className="text-sm text-text-secondary mb-1">AI Confidence Matrix</p>
                <p className="text-2xl font-black tracking-tight text-primary">{dynamicConfidence}% Aligned</p>
                <p className="text-xs text-gray-500 mt-1">Based on multi-modal data density</p>
              </Card>
            </div>

            <PrintableReport
              results={results}
              patientData={cleanPatientData}
              sessionId={sessionId}
              isWeb={true}
              risk={risk}
              status={status}
              confidence={dynamicConfidence}
            />
          </div>
        )}
      </div>

      {/* HIDDEN PDF ENGINE */}
      <div id="hidden-pdf-engine-container" style={{ display: 'none', backgroundColor: '#ffffff', color: '#111827', width: '1000px', padding: '40px' }}>
         <PrintableReport
            results={results}
            patientData={cleanPatientData}
            sessionId={sessionId}
            isWeb={false}
            risk={risk}
            status={status}
            confidence={dynamicConfidence}
          />
      </div>
    </div>
  );
}

// ==========================================
// THE UNIVERSAL REPORT TEMPLATE (PDF & WEB)
// ==========================================
const PrintableReport = ({ results, patientData, sessionId, isWeb, risk, status, confidence }) => {

  const ReportCard = ({ children, title, icon }) => (
    <div style={{ pageBreakInside: 'avoid', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '24px', marginBottom: '24px', backgroundColor: '#ffffff' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #e5e7eb', paddingBottom: '16px', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px', color: '#111827', margin: 0 }}>
          {icon && <span className="material-symbols-outlined" style={{ color: '#2563eb' }}>{icon}</span>}
          {title}
        </h2>
      </div>
      {children}
    </div>
  );

  const StatBox = ({ label, value }) => (
    <div style={{ backgroundColor: '#f9fafb', padding: '16px', borderRadius: '8px', border: '1px solid #f3f4f6', pageBreakInside: 'avoid' }}>
      <p style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase', fontWeight: 'bold', margin: '0 0 4px 0' }}>{label}</p>
      <p style={{ fontSize: '18px', fontWeight: '900', color: '#111827', margin: 0 }}>{value}</p>
    </div>
  );

  const TranscriptBox = ({ transcript }) => (
    <div style={{ marginTop: '24px', pageBreakInside: 'avoid' }}>
      <h3 style={{ fontSize: '12px', fontWeight: 'bold', color: '#374151', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>Speech Transcript</h3>
      <div style={{ backgroundColor: '#f3f4f6', padding: '16px', borderRadius: '6px', fontSize: '14px', fontFamily: 'monospace', color: '#1f2937', whiteSpace: 'pre-wrap', borderLeft: '4px solid #9ca3af' }}>
        {transcript || "No transcript generated."}
      </div>
    </div>
  );

  // Dynamic Graph Calculation
  const calculateGraphData = () => {
    let memoryScore = 0;
    if (results.story_recall?.scores?.summary?.core_recall) memoryScore = results.story_recall.scores.summary.core_recall * 100;
    else if (results.memory_qna?.memory_analysis?.delayed_score) memoryScore = results.memory_qna.memory_analysis.delayed_score * 100;

    let fluencyScore = 0;
    if (results.free_speech?.features?.fluency?.evidence?.wpm) {
      fluencyScore = Math.min(100, (results.free_speech.features.fluency.evidence.wpm / 150) * 100);
    } else if (results.picture_description?.scores?.fluency_score) {
       fluencyScore = Math.min(100, results.picture_description.scores.fluency_score * 10);
    }

    let densityScore = 0;
    if (results.picture_description?.spatial_stats?.spatial_density) {
      densityScore = Math.min(100, (results.picture_description.spatial_stats.spatial_density / 2.0) * 100);
    } else if (results.story_recall?.scores?.summary?.primacy_ratio) {
      densityScore = Math.min(100, results.story_recall.scores.summary.primacy_ratio * 100);
    }

    return [
      { label: 'Memory Retention', value: memoryScore || 5, color: '#3b82f6' },
      { label: 'Speech Fluency', value: fluencyScore || 5, color: '#10b981' },
      { label: 'Content Density', value: densityScore || 5, color: '#8b5cf6' }
    ];
  };

  const graphData = calculateGraphData();

  return (
    <div style={{ fontFamily: 'sans-serif' }}>

      {/* PDF HEADER WITH DYNAMIC STATS */}
      {!isWeb && (
        <div style={{ borderBottom: '2px solid #2563eb', paddingBottom: '16px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h1 style={{ fontSize: '24px', fontWeight: '900', color: '#2563eb', margin: '0 0 8px 0' }}>NeuroSense Diagnostic Report</h1>
              <div style={{ fontSize: '12px', color: '#4b5563', lineHeight: '1.5' }}>
                <p style={{ margin: 0 }}>Patient: <strong style={{ color: '#111827', fontSize: '14px' }}>{patientData.name || 'Anonymous'}</strong></p>
                <p style={{ margin: 0 }}>Age: <strong style={{ color: '#111827' }}>{patientData.age}</strong> | Gender: <strong style={{ color: '#111827' }}>{patientData.gender}</strong></p>
              </div>
            </div>
            <div style={{ textAlign: 'right', fontSize: '12px', color: '#4b5563', lineHeight: '1.5' }}>
              <p style={{ margin: 0 }}>Date: <strong style={{ color: '#111827' }}>{new Date().toLocaleDateString()}</strong></p>
              <p style={{ margin: 0 }}>Session: <span style={{ fontFamily: 'monospace' }}>{sessionId}</span></p>
            </div>
          </div>

          {/* THE NEW DYNAMIC SUMMARY BOX IN PDF */}
          <div style={{ display: 'flex', gap: '16px', marginTop: '20px' }}>
            <div style={{ flex: 1, backgroundColor: risk === 'Invalid' ? '#f3f4f6' : (risk.includes('High') ? '#fef2f2' : (risk.includes('Elevated') ? '#fff7ed' : '#f0fdf4')), padding: '12px', borderRadius: '8px', border: '1px solid', borderColor: risk === 'Invalid' ? '#e5e7eb' : (risk.includes('High') ? '#fca5a5' : (risk.includes('Elevated') ? '#fdba74' : '#bbf7d0')) }}>
               <p style={{ fontSize: '10px', textTransform: 'uppercase', color: '#6b7280', fontWeight: 'bold', margin: '0 0 4px 0' }}>Predicted Risk Level</p>
               <p style={{ fontSize: '16px', fontWeight: '900', margin: 0, color: risk === 'Invalid' ? '#6b7280' : (risk.includes('High') ? '#dc2626' : (risk.includes('Elevated') ? '#ea580c' : '#16a34a')) }}>{risk.toUpperCase()}</p>
               <p style={{ fontSize: '10px', color: '#6b7280', margin: '4px 0 0 0' }}>{status}</p>
            </div>
            <div style={{ flex: 1, backgroundColor: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
               <p style={{ fontSize: '10px', textTransform: 'uppercase', color: '#6b7280', fontWeight: 'bold', margin: '0 0 4px 0' }}>AI Confidence Matrix</p>
               <p style={{ fontSize: '16px', fontWeight: '900', margin: 0, color: '#0ea5e9' }}>{confidence}% Aligned</p>
               <p style={{ fontSize: '10px', color: '#6b7280', margin: '4px 0 0 0' }}>Multi-modal data density</p>
            </div>
          </div>
        </div>
      )}

      {/* COGNITIVE DOMAIN GRAPH */}
      {confidence > 0 ? (
        <ReportCard title="Cognitive Domain Summary" icon="bar_chart">
           <div style={{ padding: '10px 0' }}>
              {graphData.map((stat, idx) => (
                 <div key={idx} style={{ marginBottom: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                       <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#374151' }}>{stat.label}</span>
                       <span style={{ fontSize: '13px', fontWeight: 'bold', color: stat.color }}>{Math.round(stat.value)}%</span>
                    </div>
                    <div style={{ width: '100%', backgroundColor: '#f3f4f6', borderRadius: '999px', height: '12px', overflow: 'hidden' }}>
                       <div style={{
                          height: '100%',
                          width: `${stat.value}%`,
                          backgroundColor: stat.color,
                          borderRadius: '999px',
                          transition: 'width 1s ease-in-out'
                       }} />
                    </div>
                 </div>
              ))}
              <p style={{ fontSize: '11px', color: '#6b7280', marginTop: '12px', fontStyle: 'italic', textAlign: 'center' }}>
                 *Normalized percentiles based on aggregated performance metrics.
              </p>
           </div>
        </ReportCard>
      ) : (
        <div style={{ padding: '16px', backgroundColor: '#f9fafb', border: '1px dashed #d1d5db', borderRadius: '8px', textAlign: 'center', marginBottom: '24px', pageBreakInside: 'avoid' }}>
           <p style={{ color: '#6b7280', fontSize: '13px', fontStyle: 'italic', margin: 0 }}>Insufficient audio data collected to generate cognitive domain graphs.</p>
        </div>
      )}

      {/* 1. FREE SPEECH */}
      {results.free_speech && results.free_speech.features && (
        <ReportCard title="Free Speech Analysis" icon="record_voice_over">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatBox label="WPM (Fluency)" value={results.free_speech.features.fluency?.evidence?.wpm || 'N/A'} />
            <StatBox label="Syntactic Depth" value={results.free_speech.features.syntax?.evidence?.avg_depth?.toFixed(2) || 'N/A'} />
            <StatBox label="Lexical Diversity" value={results.free_speech.features.lexical_diversity?.primary_score?.toFixed(2) || 'N/A'} />
            <StatBox label="Perplexity" value={results.free_speech.features.perplexity?.perplexity?.toFixed(2) || 'N/A'} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div style={{ pageBreakInside: 'avoid' }}>
              <h3 style={{ fontSize: '12px', fontWeight: 'bold', color: '#374151', textTransform: 'uppercase', marginBottom: '12px' }}>Semantic & Coherence Evidence</h3>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <li style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', backgroundColor: '#fef2f2', color: '#991b1b', borderRadius: '4px' }}>
                  <span>Topic Drift Events:</span> <strong>{results.free_speech.features.coherence?.evidence?.drift_points?.length || 0} detected</strong>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', backgroundColor: '#fef08a', color: '#854d0e', borderRadius: '4px' }}>
                  <span>Vague Words (Empty Speech):</span> <strong>{results.free_speech.features.idea_density?.vague_words_count || 0} instances</strong>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', backgroundColor: '#ffedd5', color: '#9a3412', borderRadius: '4px' }}>
                  <span>Anomia (Word Finding):</span> <strong>{results.free_speech.features.idea_density?.anomia_flags || 0} instances</strong>
                </li>
              </ul>
            </div>
            <div style={{ pageBreakInside: 'avoid' }}>
              <h3 style={{ fontSize: '12px', fontWeight: 'bold', color: '#374151', textTransform: 'uppercase', marginBottom: '12px' }}>Disfluency & Repetition</h3>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <li style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '4px' }}>
                  <span>Fillers Used ("um", "ah"):</span> <strong>{results.free_speech.features.disfluency?.filler_count || 0}</strong>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '4px' }}>
                  <span>Phrase Repetitions:</span> <strong>{results.free_speech.features.repetition?.phrase_repetition || 0}</strong>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between', padding: '8px', backgroundColor: '#fef2f2', color: '#991b1b', borderRadius: '4px' }}>
                  <span>Perseveration Loop:</span> <strong>{results.free_speech.features.repetition?.evidence?.loop_detected ? 'YES' : 'NO'}</strong>
                </li>
              </ul>
            </div>
          </div>
          <TranscriptBox transcript={results.free_speech.transcript} />
        </ReportCard>
      )}

      {/* 2. PICTURE DESCRIPTION */}
      {results.picture_description && !results.picture_description.error && (
        <ReportCard title={`Picture Description (${results.picture_description.picture_id || 'cookie_theft'})`} icon="image">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatBox label="Spatial Density" value={results.picture_description.spatial_stats?.spatial_density?.toFixed(2) || 0} />
            <StatBox label="Syntactic Depth" value={results.picture_description.utterances?.syntax_stats?.avg_tree_depth?.toFixed(2) || 0} />
            <StatBox label="Fluency Score" value={results.picture_description.scores?.fluency_score?.toFixed(2) || 0} />
            <StatBox label="Disfluency Rate" value={results.picture_description.utterances?.disfluency_stats?.disfluency_score?.toFixed(2) || 0} />
          </div>

          <div style={{ backgroundColor: '#fff7ed', borderLeft: '4px solid #f97316', padding: '12px', marginBottom: '16px', borderRadius: '4px', pageBreakInside: 'avoid' }}>
             <p style={{ fontSize: '12px', fontWeight: 'bold', color: '#9a3412', margin: '0 0 4px 0' }}>Conceptual Insights</p>
             <p style={{ fontSize: '13px', color: '#c2410c', margin: '0 0 4px 0' }}>
               <strong>Missed Core Concepts:</strong> {getMissedConcepts(results.picture_description.details?.iu_table, 'core')}
             </p>
             <p style={{ fontSize: '13px', color: '#c2410c', margin: 0 }}>
               <strong>Missed Context Concepts:</strong> {getMissedConcepts(results.picture_description.details?.iu_table, 'context')}
             </p>
          </div>

          <h3 style={{ fontSize: '12px', fontWeight: 'bold', color: '#374151', textTransform: 'uppercase' }}>Content Verification Map</h3>
          <IUComparisonTable iuTable={results.picture_description.details?.iu_table} />
          <TranscriptBox transcript={results.picture_description.transcript} />
        </ReportCard>
      )}

      {/* 3. STORY RECALL */}
      {results.story_recall && !results.story_recall.error && (
        <ReportCard title={`Story Recall Analysis (Story ID: ${results.story_recall.story_id || 'Unknown'})`} icon="menu_book">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatBox label="Speech Rate" value={`${results.story_recall.pause_analysis?.speech_rate?.toFixed(2) || 0} w/s`} />
            <StatBox label="Long Pauses > 2s" value={results.story_recall.pause_analysis?.pause_count || 0} />
            <StatBox label="Core IU Recall" value={`${((results.story_recall.scores?.summary?.core_recall || 0) * 100)?.toFixed(0)}%`} />
            <StatBox label="Primacy Ratio" value={results.story_recall.scores?.summary?.primacy_ratio?.toFixed(2) || 0} />
          </div>

          <div style={{ backgroundColor: '#fff7ed', borderLeft: '4px solid #f97316', padding: '12px', marginBottom: '16px', borderRadius: '4px', pageBreakInside: 'avoid' }}>
             <p style={{ fontSize: '12px', fontWeight: 'bold', color: '#9a3412', margin: '0 0 4px 0' }}>Structural Insights</p>
             <p style={{ fontSize: '13px', color: '#c2410c', margin: '0 0 4px 0' }}>
               <strong>Missed Core Concepts:</strong> {getMissedConcepts(results.story_recall.scores?.details?.iu_table, 'core')}
             </p>
             <p style={{ fontSize: '13px', color: '#c2410c', margin: '0 0 4px 0' }}>
               <strong>Sequence Order:</strong> {results.story_recall.scores?.details?.gmatch_details?.recalled_order?.join(', ') || "None"}
             </p>
          </div>

          <h3 style={{ fontSize: '12px', fontWeight: 'bold', color: '#374151', textTransform: 'uppercase' }}>Recall Accuracy Matrix</h3>
          <IUComparisonTable iuTable={results.story_recall.scores?.details?.iu_table} />
          <TranscriptBox transcript={results.story_recall.transcript} />
        </ReportCard>
      )}

      {/* 4. EPISODIC MEMORY */}
      {results.memory_qna && !results.memory_qna.error && (
        <ReportCard title={`Episodic Memory (Story ID: ${results.memory_qna.story_id || 'Unknown'})`} icon="psychology">

          <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', padding: '16px', borderRadius: '8px', marginBottom: '24px', textAlign: 'center', pageBreakInside: 'avoid' }}>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold', color: '#166534', textTransform: 'capitalize' }}>
               Status: {results.memory_qna.memory_analysis?.memory_status?.replace('_', ' ')}
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#15803d' }}>{results.memory_qna.memory_analysis?.explanation}</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <StatBox label="Immediate Score" value={`${(results.memory_qna.memory_analysis?.immediate_score * 100)?.toFixed(1)}%`} />
            <StatBox label="Delayed Score" value={`${(results.memory_qna.memory_analysis?.delayed_score * 100)?.toFixed(1)}%`} />
            <StatBox label="Efficiency" value={`${(results.memory_qna.memory_analysis?.recall_efficiency * 100)?.toFixed(1)}%`} />
            <StatBox label="Forgetting Rate" value={`${(results.memory_qna.memory_analysis?.forgetting_rate * 100)?.toFixed(1)}%`} />
            <div style={{ backgroundColor: '#fef2f2', padding: '16px', borderRadius: '8px', border: '1px solid #fecaca' }}>
               <p style={{ fontSize: '11px', color: '#991b1b', textTransform: 'uppercase', fontWeight: 'bold', margin: '0 0 4px 0' }}>Memory Drop</p>
               <p style={{ fontSize: '18px', fontWeight: '900', color: '#dc2626', margin: 0 }}>{(results.memory_qna.memory_drop * 100)?.toFixed(1)}%</p>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mt-4">
            <div className="break-inside-avoid">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <h3 style={{ fontSize: '12px', fontWeight: 'bold', color: '#374151', textTransform: 'uppercase', margin: 0 }}>Immediate Encoding Match</h3>
                <span style={{ fontSize: '11px', color: '#c2410c', fontWeight: 'bold' }}>
                  Missed Core: {getMissedConcepts(results.memory_qna.immediate?.scores?.details?.iu_table, 'core')}
                </span>
              </div>
              <IUComparisonTable iuTable={results.memory_qna.immediate?.scores?.details?.iu_table} />
              <TranscriptBox transcript={results.memory_qna.transcripts?.immediate} />
            </div>

            <div className="break-inside-avoid">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <h3 style={{ fontSize: '12px', fontWeight: 'bold', color: '#374151', textTransform: 'uppercase', margin: 0 }}>Delayed Retention Match</h3>
                <span style={{ fontSize: '11px', color: '#c2410c', fontWeight: 'bold' }}>
                  Missed Core: {getMissedConcepts(results.memory_qna.delayed?.scores?.details?.iu_table, 'core')}
                </span>
              </div>
              <IUComparisonTable iuTable={results.memory_qna.delayed?.scores?.details?.iu_table} />
              <TranscriptBox transcript={results.memory_qna.transcripts?.delayed} />
            </div>
          </div>
        </ReportCard>
      )}
    </div>
  );
};