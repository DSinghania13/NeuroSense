import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ROUTES } from './constants/routes';

import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Patients from './pages/Patients';
import NewDiagnosis from './pages/NewDiagnosis';
import DiagnosisResult from './pages/DiagnosisResult';
import Reports from './pages/Reports';
import NotFound from './pages/NotFound';
import SystemGuard from './components/SystemGuard';

import PictureDescriptionTest from './pages/PictureDescriptionTest';
import FreeSpeechTest from "./pages/FreeSpeechTest.jsx";
import EpisodicMemoryTest from "./pages/EpisodicMemoryTest.jsx";
import StoryRecallTest from "./pages/StoryRecallTest.jsx";
import Settings from "./pages/Settings.jsx";
import {NotificationProvider} from "./context/NotificationContext.jsx";
import ErrorBoundary from "./components/ErrorBoundary.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NotificationProvider>
          <ErrorBoundary>
            <Routes>
              <Route path={ROUTES.LOGIN} element={<Login />} />

              <Route element={<ProtectedRoute />}>
                <Route element={<Layout />}>
                  <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
                  <Route path={ROUTES.PATIENTS} element={<Patients />} />
                  <Route path={ROUTES.NEW_DIAGNOSIS} element={<NewDiagnosis />} />
                  <Route path={ROUTES.DIAGNOSIS_RESULT} element={<DiagnosisResult />} />
                  <Route path={ROUTES.REPORTS} element={<Reports />} />
                  <Route path={ROUTES.SETTINGS} element={<Settings />} />
                  <Route path={ROUTES.TEST_PICTURE} element={
                    <SystemGuard>
                      <PictureDescriptionTest />
                    </SystemGuard>
                  } />
                  <Route path={ROUTES.TEST_FREE_SPEECH} element={
                    <SystemGuard>
                      <FreeSpeechTest />
                    </SystemGuard>
                  } />
                  <Route path={ROUTES.TEST_MEMORY} element={
                    <SystemGuard>
                      <EpisodicMemoryTest />
                    </SystemGuard>
                  } />
                  <Route path={ROUTES.TEST_STORY} element={
                    <SystemGuard>
                      <StoryRecallTest />
                    </SystemGuard>
                  } />
                </Route>
              </Route>

              <Route path="*" element={<NotFound />} />
            </Routes>
          </ErrorBoundary>
        </NotificationProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
