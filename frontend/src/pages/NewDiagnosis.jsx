import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '../constants/routes';
import { useAuth } from '../context/AuthContext';
import PageHeader from '../components/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import {useNotification} from "../context/NotificationContext.jsx";

const AVAILABLE_TESTS = [
  { id: 'picture-description', label: 'Picture Description' },
  { id: 'free-speech', label: 'Free Speech' },
  { id: 'episodic-memory', label: 'Episodic Memory' },
  { id: 'story-recall', label: 'Story Recall' },
];

export default function NewDiagnosis() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { notify } = useNotification();

  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [selectedTasks, setSelectedTasks] = useState(AVAILABLE_TESTS.map(t => t.id));

  // Fetch the doctor's patients to populate the dropdown
  useEffect(() => {
    if (user?.doctor_id) {
      fetch(`/api/doctors/${user.doctor_id}/patients`)
        .then(res => res.json())
        .then(data => setPatients(data));
    }
  }, [user]);

  const handleToggleTask = (taskId) => {
    if (selectedTasks.includes(taskId)) {
      setSelectedTasks(selectedTasks.filter(id => id !== taskId));
    } else {
      setSelectedTasks([...selectedTasks, taskId]);
    }
  };

  const handleProceedToTest = (e) => {
    e.preventDefault();

    if (!selectedPatientId) {
      notify("Missing Information", "Please select a patient from the list.", "error");
      return;
    }
    if (selectedTasks.length === 0) {
      notify("No Tests Selected", "Please select at least one diagnostic test to proceed.", "error");
      return;
    }

    // Grab full patient data based on the selection
    const patientData = patients.find(p => p.patient_id === selectedPatientId);

    let taskQueue = [...selectedTasks];
    taskQueue.sort((a, b) => {
      if (a === 'episodic-memory') return -1;
      if (b === 'episodic-memory') return 1;
      return 0;
    });

    const firstTask = taskQueue.shift();
    const pendingTasks = taskQueue;

    const routeMap = {
      'picture-description': ROUTES.TEST_PICTURE,
      'free-speech': ROUTES.TEST_FREE_SPEECH,
      'episodic-memory': ROUTES.TEST_MEMORY,
      'story-recall': ROUTES.TEST_STORY
    };

    const sessionId = `Session-${Date.now()}`;
    localStorage.setItem(`expected_tests_${sessionId}`, selectedTasks.length);

    // Pass the patient_id deep into the state so the audio recorders can send it to Flask!
    navigate(routeMap[firstTask], {
      state: {
        patientData,
        pendingTasks,
        sessionId,
        accumulatedResults: {}
      },
      replace: true
    });
  };

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <PageHeader title="Start Diagnosis" description="Select an existing patient and choose tests." />

      <main className="flex-1 overflow-y-auto py-10 px-4">
        <div className="flex w-full max-w-4xl flex-col mx-auto">
          <Card>
            <form className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-8">

              <div className="md:col-span-2 flex flex-col">
                <label className="text-text-primary text-sm font-bold mb-2">Select Patient</label>
                <div className="relative">
                  <select
                    value={selectedPatientId}
                    onChange={(e) => setSelectedPatientId(e.target.value)}
                    className="w-full appearance-none rounded-lg border border-border bg-background p-3 text-text-primary focus:ring-2 focus:ring-primary h-[52px]"
                    required
                  >
                    <option value="" disabled>-- Select a registered patient --</option>
                    {patients.map(p => (
                      <option key={p.patient_id} value={p.patient_id}>
                        {p.name} (ID: {p.patient_id})
                      </option>
                    ))}
                  </select>

                  {/* ---> ADD THIS SPAN RIGHT HERE <--- */}
                  <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary pointer-events-none">
                    expand_more
                  </span>

                </div>
              </div>

              <div className="md:col-span-2 mt-2">
                <p className="text-text-primary text-base font-bold mb-4">Select Speech Tasks</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {AVAILABLE_TESTS.map((task) => (
                    <label key={task.id} className={`flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer ${selectedTasks.includes(task.id) ? 'border-primary bg-primary/5' : 'border-border'}`}>
                      <input type="checkbox" className="w-5 h-5" checked={selectedTasks.includes(task.id)} onChange={() => handleToggleTask(task.id)} />
                      <span className="font-semibold">{task.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="md:col-span-2 border-t border-border mt-2" />
              <div className="md:col-span-2 flex justify-end">
                <Button onClick={handleProceedToTest} className="h-14 px-8 text-lg" icon="arrow_forward">
                  Begin Diagnostic
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </main>
    </div>
  );
}