import { useState, useRef } from 'react';

export default function AudioRecorder({ onAudioReady }) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        // Create the final audio blob
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);

        // Pass the blob up to the Test page so it can be sent to Flask!
        onAudioReady(audioBlob);

        // Stop all microphone tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);

      // Start the UI timer
      setRecordingTime(0);
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Microphone access is required to perform this test.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  };

  const clearRecording = () => {
    setAudioUrl(null);
    setRecordingTime(0);
    onAudioReady(null); // Clear the file in the parent component
  };

  // Helper to format seconds into MM:SS
  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-border rounded-xl bg-background">

      {/* If there is no recording yet, show the Record button */}
      {!audioUrl && (
        <div className="flex flex-col items-center gap-4">
          <button
            onClick={isRecording ? stopRecording : startRecording}
            type="button"
            className={`cursor-pointer flex items-center justify-center w-16 h-16 rounded-full transition-all duration-300 shadow-lg ${
              isRecording 
                ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                : 'bg-primary hover:bg-primary-light text-white'
            }`}
          >
            <span className="material-symbols-outlined text-3xl text-white">
              {isRecording ? 'stop' : 'mic'}
            </span>
          </button>

          <div className="text-center">
            <p className={`font-bold text-lg ${isRecording ? 'text-red-500' : 'text-text-primary'}`}>
              {isRecording ? 'Recording...' : 'Click to Record'}
            </p>
            {isRecording && (
              <p className="text-red-500 font-mono text-xl mt-1">{formatTime(recordingTime)}</p>
            )}
          </div>
        </div>
      )}

      {/* If the recording is finished, show the Playback and Retake options */}
      {audioUrl && (
        <div className="flex flex-col items-center gap-4 w-full max-w-md">
          <audio src={audioUrl} controls className="w-full" />

          <button
            onClick={clearRecording}
            type="button"
            className="text-sm font-bold text-red-500 hover:text-red-700 transition-colors flex items-center gap-1"
          >
            <span className="material-symbols-outlined text-sm">delete</span>
            Delete & Retake
          </button>
        </div>
      )}

    </div>
  );
}