import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ROUTES } from '../constants/routes';
import PageHeader from '../components/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import AudioRecorder from '../components/AudioRecorder';
import { useNotification } from '../context/NotificationContext';

export default function StoryRecallTest() {
  const location = useLocation();
  const navigate = useNavigate();
  const { patientData = {}, pendingTasks = [], sessionId } = location.state || {};
  const { notify } = useNotification();

  // -- STORY & AUDIO STATE --
  const [currentStory, setCurrentStory] = useState({ id: null, text: '' });
  const [ttsAudioUrl, setTtsAudioUrl] = useState(null);
  const [isLoadingTts, setIsLoadingTts] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // -- UI LOCK STATE --
  const [isStoryFinished, setIsStoryFinished] = useState(false);
  const [isLockedOut, setIsLockedOut] = useState(false); // <--- NEW SECURITY LOCK

  useEffect(() => {
    fetch('/api/memory/random_story')
      .then(async (res) => {
        if (!res.ok) throw new Error(`Backend Error: ${await res.text()}`);
        return res.json();
      })
      .then(data => {
        if (data.story_id) setCurrentStory({ id: data.story_id, text: data.text });
      })
      .catch(err => {
        console.error("Failed to fetch random story:", err);
        setCurrentStory({ id: null, text: "⚠️ Failed to load story from server." });
      });
  }, []);

  const handleFetchTTS = async () => {
    if (!currentStory.id) return;
    setIsLoadingTts(true);
    try {
      const response = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ story_id: currentStory.id, session_id: sessionId })
      });
      const blob = await response.blob();
      setTtsAudioUrl(URL.createObjectURL(blob));
    } catch (error) {
      console.error("Failed to load Google TTS", error);
      notify("Narration Error", "Failed to load audio narration. Please read the story manually.", "error");
    } finally {
      setIsLoadingTts(false);
    }
  };

  const handleSubmitTest = () => {
    if (!recordedAudio) {
      notify("Audio Required", "Please record the patient's response first before submitting.", "error");
      return;
    }
    setIsProcessing(true);

    const formData = new FormData();
    formData.append('audio', recordedAudio);
    formData.append('story_id', currentStory.id);
    if (sessionId) formData.append('session_id', sessionId);
    if (patientData.patient_id) formData.append('patient_id', patientData.patient_id);

    fetch('/api/story', { method: 'POST', body: formData })
      .then(res => res.json())
      .then(data => console.log("Story Recall background save initiated:", data))
      .catch(err => console.error("Upload failed:", err));

    if (pendingTasks.length > 0) {
      const nextQueue = [...pendingTasks];
      const nextTask = nextQueue.shift();
      const routeMap = {
        'picture-description': ROUTES.TEST_PICTURE,
        'free-speech': ROUTES.TEST_FREE_SPEECH,
        'memory-qna': ROUTES.TEST_MEMORY,
        'story-recall': ROUTES.TEST_STORY
      };
      navigate(routeMap[nextTask], { state: { patientData, pendingTasks: nextQueue, sessionId } });
    } else {
      navigate(ROUTES.DIAGNOSIS_RESULT, { state: { patientData, sessionId } });
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <PageHeader
        title="Story Recall"
        description={`Patient: ${patientData.name || 'Unknown'} | Task: Immediate auditory processing and recall`}
      />

      <main className="flex-1 overflow-y-auto py-10 px-4 sm:px-6">
        <div className="flex w-full max-w-4xl flex-col mx-auto gap-8">

          {!isStoryFinished ? (
            <Card className="bg-primary/5 border-primary/20">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-bold text-text-primary">Step 1: Story Narration</h2>
                  <p className="text-text-secondary text-sm">Play the Google TTS narration for the patient.</p>
                </div>
                {!ttsAudioUrl ? (
                  <Button onClick={handleFetchTTS} disabled={isLoadingTts || !currentStory.id} icon="download">
                    {isLoadingTts ? 'Loading...' : 'Generate Narration'}
                  </Button>
                ) : (
                  <audio src={ttsAudioUrl} controls autoPlay className="h-10" />
                )}
              </div>
              <div className="bg-white p-6 rounded-lg border border-border shadow-sm text-lg font-serif">
                {currentStory.text ? `"${currentStory.text}"` : "Loading random story from server..."}
              </div>

              <div className="mt-6 flex justify-end border-t border-border pt-4">
                <Button onClick={() => setIsStoryFinished(true)} icon="visibility_off">
                  Hide Story & Proceed to Recall
                </Button>
              </div>
            </Card>
          ) : (
            <Card>
              <div className="mb-6">
                <h2 className="text-xl font-bold text-text-primary">Step 2: Record Recall</h2>
                <p className="text-text-secondary">Say: <span className="italic">"Tell me everything you can remember about that story."</span></p>
              </div>

              {/* THE FIX: Click Capture intercepts any interaction and permanently locks the UI */}
              <div onClickCapture={() => setIsLockedOut(true)}>
                <AudioRecorder onAudioReady={setRecordedAudio} />
              </div>

              <div className="mt-6 flex justify-start">
                <button
                  onClick={() => setIsStoryFinished(false)}
                  disabled={isLockedOut}
                  className={`text-sm font-bold transition-colors flex items-center gap-1 ${
                    isLockedOut ? 'text-gray-300 cursor-not-allowed' : 'text-text-secondary hover:text-primary'
                  }`}
                  title={isLockedOut ? "Story access is permanently locked once recording begins." : "Back to Story"}
                >
                  <span className="material-symbols-outlined text-sm">arrow_back</span>
                  Back to Story
                </button>
              </div>
            </Card>
          )}

          <Card className="mt-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-text-primary">Queue Status</h3>
                <p className="text-sm text-text-secondary">
                  {pendingTasks.length} test(s) remaining in queue
                </p>
              </div>
              <Button
                onClick={handleSubmitTest}
                disabled={!recordedAudio || isProcessing}
                className="h-14 px-8 text-lg"
                icon={isProcessing ? 'hourglass_empty' : (pendingTasks.length > 0 ? 'arrow_forward' : 'analytics')}
              >
                {isProcessing
                  ? 'Saving...'
                  : (pendingTasks.length > 0 ? 'Next Test' : 'Finish & View Results')}
              </Button>
            </div>
          </Card>

        </div>
      </main>
    </div>
  );
}