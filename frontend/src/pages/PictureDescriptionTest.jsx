import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ROUTES } from '../constants/routes';
import PageHeader from '../components/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import AudioRecorder from '../components/AudioRecorder';
import { useNotification } from '../context/NotificationContext';

export default function PictureDescriptionTest() {
  const location = useLocation();
  const navigate = useNavigate();
  const { notify } = useNotification();

  // 1. Declare state variables exactly ONCE here at the top!
  const {
    patientData = {},
    pendingTasks = [],
    sessionId
  } = location.state || {};

  const [audioFile, setAudioFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSubmitTest = () => {
    if (!audioFile) {
      notify("Audio Required", "Please record the patient's response before proceeding.", "error");
      return;
    }

    setIsProcessing(true);

    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('picture_id', 'cookie_theft');
    if (sessionId) formData.append('session_id', sessionId);

    // ---> THE FIX: Send the MongoDB patient_id to Flask!
    if (patientData.patient_id) formData.append('patient_id', patientData.patient_id);

    // 2. FIRE AND FORGET: Hand it to Flask
    fetch('/api/picture', {
      method: 'POST',
      body: formData,
    })
    .then(res => res.json())
    .then(data => console.log("Background save initiated:", data))
    .catch(err => console.error("Upload failed:", err));

    // 3. INSTANT NAVIGATION: Move straight to the next page
    if (pendingTasks.length > 0) {
      // ... (rest of your navigation logic remains exactly the same)
      const nextQueue = [...pendingTasks];
      const nextTask = nextQueue.shift();

      const routeMap = {
        'picture-description': ROUTES.TEST_PICTURE,
        'free-speech': ROUTES.TEST_FREE_SPEECH,
        'memory-qna': ROUTES.TEST_MEMORY,
        'story-recall': ROUTES.TEST_STORY
      };

      navigate(routeMap[nextTask], {
        state: { patientData, pendingTasks: nextQueue, sessionId }
      });
    } else {
      navigate(ROUTES.DIAGNOSIS_RESULT, {
        state: { patientData, sessionId }
      });
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <PageHeader
        title="Picture Description"
        description={`Patient: ${patientData.name || 'Unknown'} | Task: Identifying visual elements and spatial relations`}
      />

      <main className="flex-1 overflow-y-auto py-10 px-4 sm:px-6">
        <div className="flex w-full max-w-5xl flex-col mx-auto gap-8">

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Visual Stimulus Section */}
            <Card className="flex flex-col items-center">
              <div className="w-full text-left mb-4">
                <h2 className="text-xl font-bold text-text-primary">Clinical Stimulus</h2>
                <p className="text-text-secondary text-sm">
                  Show this image to the patient and ask: "Tell me everything you see happening in this picture."
                </p>
              </div>

              <div className="w-full aspect-[4/3] bg-gray-100 rounded-xl border border-border flex items-center justify-center overflow-hidden">
                <img
                  src="/cookie_theft.png"
                  alt="Cookie Theft Clinical Image"
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
                <div className="hidden w-full h-full flex-col items-center justify-center text-gray-400">
                  <span className="material-symbols-outlined text-4xl mb-2">image</span>
                  <span>Add 'cookie_theft.png' to /public</span>
                </div>
              </div>
            </Card>

            {/* Recording & Actions Section */}
            <div className="flex flex-col gap-8">
              <Card>
                <div className="w-full text-left mb-6">
                  <h2 className="text-xl font-bold text-text-primary">Record Response</h2>
                  <p className="text-text-secondary text-sm">
                    Ensure the environment is quiet. Press record when the patient begins speaking.
                  </p>
                </div>

                <AudioRecorder onAudioReady={setAudioFile} />
              </Card>

              {/* Action Buttons */}
              <Card className="bg-primary/5 border-primary/20">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-primary">Test Progress</h3>
                    <p className="text-sm text-text-secondary">
                      {pendingTasks.length} test(s) remaining in queue
                    </p>
                  </div>
                  <Button
                    onClick={handleSubmitTest}
                    disabled={!audioFile || isProcessing}
                    className="h-14 px-8 text-lg"
                    icon={isProcessing ? 'hourglass_empty' : (pendingTasks.length > 0 ? 'arrow_forward' : 'analytics')}
                  >
                    {isProcessing
                      ? 'Moving...'
                      : (pendingTasks.length > 0 ? 'Next Test' : 'View Results')}
                  </Button>
                </div>
              </Card>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}