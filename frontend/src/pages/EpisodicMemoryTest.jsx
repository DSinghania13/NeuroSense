import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ROUTES } from '../constants/routes';
import PageHeader from '../components/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import AudioRecorder from '../components/AudioRecorder';
import { useNotification } from '../context/NotificationContext';

export default function EpisodicMemoryTest() {
  const location = useLocation();
  const navigate = useNavigate();
  const { notify } = useNotification();

  const { patientData = {}, pendingTasks = [], sessionId } = location.state || {};

  // -- SMART STATE TRACKING --
  const currentPhase = localStorage.getItem(`memory_${sessionId}_phase`) || 'immediate';
  const savedStoryId = localStorage.getItem(`memory_${sessionId}_story_id`);
  const savedStoryText = localStorage.getItem(`memory_${sessionId}_story_text`);

  const [phase, setPhase] = useState(currentPhase);
  const [currentStory, setCurrentStory] = useState({
    id: savedStoryId || null,
    text: savedStoryText || ''
  });

  // -- LOCKOUT TIMER STATE --
  const [isLocked, setIsLocked] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [isStoryFinished, setIsStoryFinished] = useState(false);

  // -- AUDIO STATE --
  const [ttsAudioUrl, setTtsAudioUrl] = useState(null);
  const [isLoadingTts, setIsLoadingTts] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLockedOut, setIsLockedOut] = useState(false); // <--- CLINICAL LOCK

  useEffect(() => {
    if (phase === 'immediate' && !currentStory.id) {
      fetch('/api/memory/random_story')
        .then(async (res) => {
          if (!res.ok) {
            const errText = await res.text();
            throw new Error(`Backend Error: ${errText}`);
          }
          return res.json();
        })
        .then(data => {
          if (data.story_id) {
            setCurrentStory({ id: data.story_id, text: data.text });
            localStorage.setItem(`memory_${sessionId}_story_id`, data.story_id);
            localStorage.setItem(`memory_${sessionId}_story_text`, data.text);
          }
        })
        .catch(err => {
          console.error("Failed to fetch random story:", err);
          setCurrentStory({
            id: null,
            text: "⚠️ Failed to load story from server. Please check your Flask terminal for FileNotFoundError."
          });
        });
    }
  }, [phase, sessionId, currentStory.id]);

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

  const handleSubmitPhase = () => {
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

    if (phase === 'immediate') {
      fetch('/api/memory/immediate', { method: 'POST', body: formData })
        .then(() => {
          localStorage.setItem(`memory_${sessionId}_phase`, 'delayed');

          if (pendingTasks.length > 0) {
            const nextQueue = [...pendingTasks, 'memory-qna'];
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
            setPhase('delayed');
            const randomLockTime = Math.floor(Math.random() * (360 - 300 + 1)) + 300;
            setTimeLeft(randomLockTime);
            setIsLocked(true);
            setRecordedAudio(null);
            setIsProcessing(false);
          }
        }).catch(err => console.error(err));
    }
    else {
      fetch('/api/memory/delayed', { method: 'POST', body: formData })
        .then(() => {
          localStorage.removeItem(`memory_${sessionId}_phase`);
          localStorage.removeItem(`memory_${sessionId}_story_id`);
          localStorage.removeItem(`memory_${sessionId}_story_text`);
          navigate(ROUTES.DIAGNOSIS_RESULT, { state: { patientData, sessionId } });
        }).catch(err => console.error(err));
    }
  };

  useEffect(() => {
    let timer;
    if (isLocked && timeLeft > 0) {
      timer = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
    } else if (timeLeft === 0) {
      setIsLocked(false);
    }
    return () => clearInterval(timer);
  }, [isLocked, timeLeft]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <PageHeader
        title="Episodic Memory"
        description={`Patient: ${patientData.name || 'Unknown'} | Phase: ${phase === 'immediate' ? 'Encoding (Immediate)' : 'Retention (Delayed)'}`}
      />

      <main className="flex-1 overflow-y-auto py-10 px-4 sm:px-6">
        <div className="flex w-full max-w-4xl flex-col mx-auto gap-8">

          {phase === 'immediate' && (
            <>
              {!isStoryFinished ? (
                <Card className="bg-primary/5 border-primary/20">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h2 className="text-xl font-bold text-text-primary">Phase 1: Story Narration</h2>
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
                    <h2 className="text-xl font-bold text-text-primary">Immediate Recall</h2>
                    <p className="text-text-secondary">Say: <span className="italic">"Tell me everything you can remember about that story."</span></p>
                  </div>

                  {/* THE FIX: Intercept clicks to permanently disable the back button */}
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
            </>
          )}

          {phase === 'delayed' && (
            <Card className={isLocked ? "bg-gray-100 opacity-80" : ""}>
              {isLocked ? (
                <div className="text-center py-10">
                  <span className="material-symbols-outlined text-6xl text-orange-500 mb-4 animate-bounce">lock_clock</span>
                  <h2 className="text-2xl font-bold text-text-primary mb-2">Cognitive Delay Required</h2>
                  <p className="text-text-secondary mb-6 max-w-md mx-auto">
                    To accurately test retention, the patient must wait before recalling the story. Please perform other checks or wait for the timer.
                  </p>
                  <div className="text-5xl font-mono font-black text-primary">{formatTime(timeLeft)}</div>
                </div>
              ) : (
                <>
                  <div className="mb-6">
                    <h2 className="text-xl font-bold text-text-primary">Phase 2: Delayed Recall</h2>
                    <p className="text-text-secondary">Say: <span className="italic">"Tell me everything you remember about the story I played earlier."</span></p>
                  </div>
                  <AudioRecorder onAudioReady={setRecordedAudio} />
                </>
              )}
            </Card>
          )}

          <Card className="mt-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-text-primary">Queue Status</h3>
                <p className="text-sm text-text-secondary">
                  {phase === 'immediate' && pendingTasks.length > 0
                    ? `Moving to next test. Delayed recall added to end of queue.`
                    : `${pendingTasks.length} test(s) remaining`}
                </p>
              </div>
              <Button
                onClick={handleSubmitPhase}
                disabled={!recordedAudio || isProcessing || isLocked}
                className="h-14 px-8 text-lg"
                icon={phase === 'immediate' && pendingTasks.length > 0 ? 'move_item' : 'analytics'}
              >
                {isProcessing ? 'Saving...' : (phase === 'immediate' && pendingTasks.length > 0 ? 'Queue Interruption' : 'Submit Audio')}
              </Button>
            </div>
          </Card>

        </div>
      </main>
    </div>
  );
}