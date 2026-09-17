import { useState, useEffect } from 'react';
import PageHeader from '../components/PageHeader';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';

// --- DOB TO AGE CALCULATOR ---
const calculateAge = (dobString) => {
  if (!dobString) return 'N/A';
  const birthDate = new Date(dobString);
  const today = new Date();
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
  return age;
};

export default function Patients() {
  const { user } = useAuth();
  const { notify } = useNotification();
  const [patients, setPatients] = useState([]);

  // Forms State
  const [showAddForm, setShowAddForm] = useState(false);
  const [newPatient, setNewPatient] = useState({ name: '', dob: '', gender: 'Male' });

  // Edit State
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', dob: '', gender: '' });
  const [patientToDelete, setPatientToDelete] = useState(null);

  // History State
  const [expandedPatientId, setExpandedPatientId] = useState(null);
  const [patientHistory, setPatientHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  useEffect(() => {
    if (user?.doctor_id) {
      fetch(`/api/doctors/${user.doctor_id}/patients`)
        .then(res => res.json())
        .then(data => setPatients(data))
        .catch(err => console.error("Failed to load patients", err));
    }
  }, [user]);

  // --- CRUD ACTIONS ---
  const handleAddPatient = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`/api/doctors/${user.doctor_id}/patients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPatient)
      });
      const data = await res.json();
      if (data.status === 'success') {
        setPatients([data.patient, ...patients]);
        setShowAddForm(false);
        setNewPatient({ name: '', dob: '', gender: 'Male' });
        notify("Patient Registered", `${data.patient.name} has been added to your directory.`, "success");
      }
    } catch (err) {
      console.error("Failed to add patient", err);
      notify("Registration Failed", "Could not add the patient to the database.", "error");
    }
  };

  const confirmDeletePatient = async () => {
    if (!patientToDelete) return;

    try {
      await fetch(`/api/patients/${patientToDelete}`, { method: 'DELETE' });
      setPatients(patients.filter(p => p.patient_id !== patientToDelete));
      notify("Patient Deleted", "Profile and all associated reports have been permanently removed.", "info");
    } catch (err) {
      console.error("Failed to delete patient", err);
      notify("Deletion Failed", "Could not remove the patient from the database.", "error");
    } finally {
      // Close the modal whether it succeeds or fails
      setPatientToDelete(null);
    }
  };

  const handleSaveEdit = async (patientId) => {
    try {
      const res = await fetch(`/api/patients/${patientId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editForm)
      });
      if (res.ok) {
        setPatients(patients.map(p => p.patient_id === patientId ? { ...p, ...editForm } : p));
        setEditingId(null);
        notify("Profile Updated", "The patient's details have been updated.", "success");
      }
    } catch (err) {
      console.error("Failed to edit patient", err);
      notify("Update Failed", "Could not save the patient's new details.", "error");
    }
  };

  // --- MINI HISTORY ACTION ---
  const toggleHistory = async (patientId) => {
    if (expandedPatientId === patientId) {
      setExpandedPatientId(null); // Close if already open
      return;
    }

    setExpandedPatientId(patientId);
    setIsLoadingHistory(true);
    try {
      const res = await fetch(`/api/patients/${patientId}/reports`);
      const data = await res.json();
      setPatientHistory(data);
    } catch (err) {
      console.error("Failed to fetch history", err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-y-auto bg-gray-50/50">
      <PageHeader
        title="Patient Directory"
        description="Manage profiles and view quick clinical histories."
      />

      <div className="flex-grow p-6 lg:p-10">
        <div className="max-w-6xl mx-auto space-y-6">

          <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-text-primary text-lg font-bold">Total Patients: {patients.length}</h2>
            <Button onClick={() => setShowAddForm(!showAddForm)} icon={showAddForm ? "close" : "person_add"}>
              {showAddForm ? "Cancel" : "Add New Patient"}
            </Button>
          </div>

          {/* ADD PATIENT FORM */}
          {showAddForm && (
            <Card className="bg-blue-50/50 border-blue-200 shadow-inner">
              <h3 className="font-bold text-blue-900 mb-4">Register New Patient</h3>
              <form onSubmit={handleAddPatient} className="flex flex-col md:flex-row gap-4 items-end">
                <div className="w-full">
                  <Input label="Patient Name" value={newPatient.name} onChange={(e) => setNewPatient({...newPatient, name: e.target.value})} required />
                </div>
                <div className="w-48">
                  <label className="text-sm font-bold text-text-primary mb-2 block">Date of Birth</label>
                  <input type="date" value={newPatient.dob} onChange={(e) => setNewPatient({...newPatient, dob: e.target.value})} className="w-full rounded-lg border border-border p-3 h-[52px] focus:ring-2 focus:ring-primary outline-none" required />
                </div>
                <div className="w-48">
                  <label className="text-sm font-bold text-text-primary mb-2 block">Gender</label>
                  <select value={newPatient.gender} onChange={(e) => setNewPatient({...newPatient, gender: e.target.value})} className="w-full rounded-lg border border-border p-3 h-[52px] focus:ring-2 focus:ring-primary outline-none">
                    <option>Male</option><option>Female</option><option>Other</option>
                  </select>
                </div>
                <Button type="submit" className="h-[52px]">Save Patient</Button>
              </form>
            </Card>
          )}

          {/* PATIENT LIST */}
          <Card noPadding className="shadow-sm">
            {patients.length === 0 ? (
              <p className="p-10 text-center text-text-secondary">No patients found. Add one above to get started!</p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {patients.map((patient) => (
                  <li key={patient.patient_id} className="flex flex-col hover:bg-gray-50 transition-colors">

                    {/* Main Row */}
                    <div className="p-4 flex flex-col md:flex-row justify-between md:items-center gap-4">
                      {editingId === patient.patient_id ? (
                        <div className="flex-1 flex flex-col md:flex-row gap-4 items-center w-full">
                          <input type="text" value={editForm.name} onChange={e => setEditForm({...editForm, name: e.target.value})} className="border border-gray-300 p-2 rounded flex-1 min-w-[150px] focus:ring-2 focus:ring-primary outline-none" />
                          <input type="date" value={editForm.dob} onChange={e => setEditForm({...editForm, dob: e.target.value})} className="border border-gray-300 p-2 rounded w-full md:w-40 focus:ring-2 focus:ring-primary outline-none" />
                          <select value={editForm.gender} onChange={e => setEditForm({...editForm, gender: e.target.value})} className="border border-gray-300 p-2 rounded w-full md:w-32 focus:ring-2 focus:ring-primary outline-none">
                            <option>Male</option><option>Female</option><option>Other</option>
                          </select>
                          <div className="flex gap-2 shrink-0">
                            <Button onClick={() => handleSaveEdit(patient.patient_id)} className="h-10 px-4 bg-green-600 hover:bg-green-700 border-green-600">Save</Button>
                            <Button variant="outline" onClick={() => setEditingId(null)} className="h-10 px-4">Cancel</Button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center gap-4 flex-1 cursor-pointer" onClick={() => toggleHistory(patient.patient_id)}>
                            <div className="bg-primary/10 text-primary size-10 flex items-center justify-center rounded-full shrink-0">
                              <span className="material-symbols-outlined text-[20px]">person</span>
                            </div>
                            <div>
                              <p className="font-semibold text-text-primary text-lg">
                                {patient.name} <span className="text-sm text-gray-500 font-normal ml-2">({calculateAge(patient.dob)} yrs, {patient.gender})</span>
                              </p>
                              <p className="text-xs text-text-secondary font-mono">ID: {patient.patient_id}</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <button onClick={() => toggleHistory(patient.patient_id)} className="px-3 py-1.5 text-sm font-medium text-primary bg-primary/10 rounded-md hover:bg-primary/20 transition-colors">
                              {expandedPatientId === patient.patient_id ? 'Hide History' : 'View History'}
                            </button>
                            <div className="w-px h-6 bg-gray-200 mx-2"></div>
                            <button onClick={() => { setEditingId(patient.patient_id); setEditForm({ name: patient.name, dob: patient.dob, gender: patient.gender }); }} className="p-2 text-gray-400 hover:text-primary transition-colors flex items-center justify-center rounded-lg hover:bg-gray-100" title="Edit Patient">
                              <span className="material-symbols-outlined text-xl">edit</span>
                            </button>
                            <button
                              onClick={() => setPatientToDelete(patient.patient_id)}
                              className="p-2 text-gray-400 hover:text-red-600 transition-colors flex items-center justify-center rounded-lg hover:bg-red-50"
                              title="Delete Patient"
                            >
                              <span className="material-symbols-outlined text-xl">delete</span>
                            </button>
                          </div>
                        </>
                      )}
                    </div>

                    {/* EXPANDED MINI-HISTORY VIEW */}
                    {expandedPatientId === patient.patient_id && !editingId && (
                      <div className="bg-gray-100/50 p-6 border-t border-gray-200">
                        <div className="flex items-center gap-2 mb-4">
                          <span className="material-symbols-outlined text-gray-500">history</span>
                          <h4 className="font-bold text-gray-700">Clinical History Snapshot</h4>
                        </div>

                        <div className="text-sm text-gray-600 mb-4">
                          <p><strong>Registered On:</strong> {new Date(patient.created_at).toLocaleDateString()}</p>
                          <p><strong>Total Diagnostics Run:</strong> {patientHistory.length}</p>
                        </div>

                        {isLoadingHistory ? (
                          <p className="text-sm text-gray-500 italic animate-pulse">Fetching records...</p>
                        ) : patientHistory.length > 0 ? (
                          <div className="space-y-2">
                            {patientHistory.slice(0, 3).map((report, idx) => (
                              <div key={idx} className="bg-white p-3 rounded border border-gray-200 flex justify-between items-center shadow-sm">
                                <div>
                                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">{new Date(report.created_at).toLocaleDateString()}</span>
                                  <p className="text-sm font-medium text-gray-800">Diagnostic Session Completed</p>
                                </div>
                                <span className="text-xs font-mono text-gray-400">{report.session_id}</span>
                              </div>
                            ))}
                            {patientHistory.length > 3 && (
                              <p className="text-xs text-gray-500 italic mt-2 text-center">...and {patientHistory.length - 3} older records. Navigate to the Reports tab for full details.</p>
                            )}
                          </div>
                        ) : (
                          <div className="bg-white p-4 rounded border border-dashed border-gray-300 text-center text-sm text-gray-500">
                            No diagnostic history available. Start a new test to establish a baseline.
                          </div>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>

        </div>
      </div>
      {patientToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <Card className="max-w-md w-full text-center shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="mx-auto bg-red-100 text-red-600 size-16 flex items-center justify-center rounded-full mb-4">
              <span className="material-symbols-outlined text-3xl">warning</span>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Delete Patient?</h3>
            <p className="text-gray-600 mb-6">
              Are you sure? This will delete the patient and <strong>ALL</strong> their diagnostic reports permanently. This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={() => setPatientToDelete(null)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={confirmDeletePatient} className="flex-1 bg-red-600 hover:bg-red-700 border-red-600 text-white">
                Yes, Delete
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}