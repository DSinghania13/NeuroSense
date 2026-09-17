import { ROUTES } from '../constants/routes';

export const actionCards = [
  {
    icon: 'add_circle',
    title: 'New Diagnosis',
    description: 'Start a new diagnostic session with a patient.',
    to: ROUTES.NEW_DIAGNOSIS,
  },
  {
    icon: 'summarize',
    title: 'View Reports',
    description: 'Access historical data and diagnostic results.',
    to: ROUTES.REPORTS,
  },
];

export const recentActivity = [
  {
    icon: 'person',
    title: 'New patient registered: John Doe',
    subtitle: 'ID: P-102345',
    time: '1 hour ago',
  },
  {
    icon: 'article',
    title: 'Report generated for Jane Smith',
    subtitle: 'Result: 87% Probability of AD',
    time: '3 hours ago',
  },
  {
    icon: 'upload_file',
    title: 'Audio file uploaded for Robert Brown',
    subtitle: 'File: RB_session_03.wav',
    time: 'Yesterday',
  },
];

export const patient = {
  name: 'John Doe',
  age: 72,
  gender: 'Male',
  recordingDate: '2023-10-26',
  speechTask: 'Picture Description',
};

export const diagnosis = {
  status: "Alzheimer's",
  riskCategory: 'High Risk',
  confidence: 87.5,
};

export const metrics = [
  { label: 'Accuracy', value: '91.2%' },
  { label: 'Precision', value: '88.5%' },
  { label: 'Recall', value: '89.7%' },
  { label: 'F1-Score', value: '89.1%' },
  { label: 'ROC-AUC', value: '0.93' },
];

export const reportData = [
  {
    name: 'John Doe',
    date: '12-11-2025',
    result: "Alzheimer's",
    confidence: 87,
    patientId: 'JD-19550515',
    assessmentDate: 'December 11, 2025',
    note: 'Patient exhibited significant semantic fluency decline. Follow-up recommended in 3 months.',
    modelNote:
      "The model predicts a high probability of Alzheimer's based on vocal biomarkers and cognitive speech patterns.",
  },
  {
    name: 'Jane Smith',
    date: '12-10-2025',
    result: 'Healthy',
    confidence: 95,
    patientId: 'JS-19600322',
    assessmentDate: 'December 10, 2025',
    note: 'No cognitive decline detected. Regular check-up recommended annually.',
    modelNote: 'The model indicates healthy cognitive speech patterns with high confidence.',
  },
  {
    name: 'Robert Johnson',
    date: '12-09-2025',
    result: 'Mild Cognitive Impairment',
    confidence: 76,
    patientId: 'RJ-19480710',
    assessmentDate: 'December 9, 2025',
    note: 'Mild word-finding difficulty noted. Follow-up in 6 months.',
    modelNote:
      'The model detects early signs of mild cognitive impairment based on hesitation patterns.',
  },
  {
    name: 'Emily Williams',
    date: '12-08-2025',
    result: "Alzheimer's",
    confidence: 91,
    patientId: 'EW-19550101',
    assessmentDate: 'December 8, 2025',
    note: 'Significant decline in narrative coherence. Immediate referral recommended.',
    modelNote: "The model predicts a high probability of Alzheimer's based on vocal biomarkers.",
  },
  {
    name: 'Michael Brown',
    date: '12-07-2025',
    result: 'Healthy',
    confidence: 98,
    patientId: 'MB-19700415',
    assessmentDate: 'December 7, 2025',
    note: 'All cognitive markers within normal range.',
    modelNote: 'The model indicates healthy cognitive speech patterns with very high confidence.',
  },
];
