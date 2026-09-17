import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ROUTES } from '../constants/routes';
import PageHeader from '../components/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import AudioRecorder from '../components/AudioRecorder';
import { useNotification } from '../context/NotificationContext';

const TARGET_WORD_COUNT = 50;

export default function FreeSpeechTest() {
  const location = useLocation();
  const navigate = useNavigate();
  const { notify } = useNotification();

  const {
    patientData = {},
    pendingTasks = [],
    sessionId
  } = location.state || {};

  const [audioFile, setAudioFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // --- REAL-TIME WORD TRACKING STATE ---
  const [isListening, setIsListening] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const recognitionRef = useRef(null);

  // Initialize the Browser's Native Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event) => {
        // Combine all chunks of speech
        const currentTranscript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join(' ');

        // Count words (split by spaces, filter out empty strings)
        const words = currentTranscript.trim().split(/\s+/).filter(w => w !== '');
        setWordCount(words.length);
      };

      recognition.onerror = (event) => {
        console.warn("Speech recognition error", event.error);
      };

      recognitionRef.current = recognition;
    } else {
      console.warn("Browser does not support real-time speech recognition.");
    }

    // Cleanup on unmount
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  // Sync the Word Counter with your AudioRecorder component
  // (You may need to pass these functions into your AudioRecorder component as props if it has its own start/stop buttons)
  const handleStartRecording = () => {
    setWordCount(0);
    setIsListening(true);
    if (recognitionRef.current) {
      try {
        recognitionRef.current.start();
      } catch (e) {
        console.error("Recognition already started", e);
      }
    }
  };

  const handleStopRecording = () => {
    setIsListening(false);
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  };

  const handleSubmitTest = () => {
    if (!audioFile) {
      notify("Audio Required", "Please record the patient's response before proceeding.", "error");
      return;
    }

    setIsProcessing(true);

    const formData = new FormData();
    formData.append('audio', audioFile);
    if (sessionId) formData.append('session_id', sessionId);

    // ---> THE FIX: Send the MongoDB patient_id to Flask!
    if (patientData.patient_id) formData.append('patient_id', patientData.patient_id);

    // FIRE AND FORGET
    fetch('/api/freespeech', {
      method: 'POST',
      body: formData,
    })
    .then(res => res.json())
    .then(data => console.log("Background save initiated:", data))
    .catch(err => console.error("Upload failed:", err));

    // INSTANT NAVIGATION
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

  // Calculate Progress UI
  const progressPercent = Math.min((wordCount / TARGET_WORD_COUNT) * 100, 100);
  const isTargetMet = wordCount >= TARGET_WORD_COUNT;

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <PageHeader
        title="Free Speech"
        description={`Patient: ${patientData.name || 'Unknown'} | Task: Spontaneous speech and cognitive fluency`}
      />

      <main className="flex-1 overflow-y-auto py-10 px-4 sm:px-6">
        <div className="flex w-full max-w-4xl flex-col mx-auto gap-8">

          {/* Instructions Section */}
          <Card className="bg-primary/5 border-primary/20">
            <h2 className="text-xl font-bold text-text-primary mb-2">Clinical Instructions</h2>
            <p className="text-text-secondary mb-4">
              Ask the patient an open-ended question to elicit spontaneous speech. <span className="font-bold text-primary">Aim for at least {TARGET_WORD_COUNT} words.</span>
            </p>
            <div className="bg-white p-4 rounded-lg border border-border shadow-sm">
              <h3 className="font-semibold text-text-primary text-sm uppercase tracking-wide mb-2">Suggested Prompts:</h3>
              <ul className="list-disc list-inside text-text-secondary space-y-2">
                <li>"Tell me about a memorable vacation you took."</li>
                <li>"Walk me through your typical morning routine."</li>
                <li>"Describe the house you grew up in."</li>
              </ul>
            </div>
          </Card>

          {/* Recording & Progress Section */}
          <Card>
            <div className="w-full text-left mb-6">
              <h2 className="text-xl font-bold text-text-primary">Record Response</h2>
              <p className="text-text-secondary text-sm">
                Ensure the environment is quiet. Press record when the patient begins speaking.
              </p>
            </div>

            {/* REAL-TIME PROGRESS BAR */}
            <div className="mb-8 p-6 bg-background rounded-xl border border-border">
              <div className="flex justify-between items-end mb-2">
                <div>
                  <p className="text-sm font-bold text-text-secondary uppercase tracking-wider">Live Word Count</p>
                  <p className={`text-3xl font-black ${isTargetMet ? 'text-green-600' : 'text-primary'}`}>
                    {wordCount} <span className="text-lg font-medium text-text-secondary">/ {TARGET_WORD_COUNT}</span>
                  </p>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-bold ${isTargetMet ? 'text-green-600' : 'text-orange-500'}`}>
                    {isTargetMet ? 'Target Reached! ✅' : (wordCount > 0 ? 'Keep prompting the patient...' : 'Waiting for speech...')}
                  </p>
                </div>
              </div>

              {/* The Bar */}
              <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ease-out ${isTargetMet ? 'bg-green-500' : 'bg-orange-400'}`}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>

            {/* Note: You may need to wire these handlers into your AudioRecorder component */}
            <div
              onClick={() => {
                // Quick hack to sync state if we don't have access to AudioRecorder's internals
                if (!isListening) handleStartRecording();
                else handleStopRecording();
            }}>
              <AudioRecorder onAudioReady={(file) => {
                setAudioFile(file);
                handleStopRecording();
              }} />
            </div>

            <div className="border-t border-border mt-8 pt-6 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-text-primary">Test Progress</h3>
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
      </main>
    </div>
  );
}