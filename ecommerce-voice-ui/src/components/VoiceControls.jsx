import { useState, useRef } from "react"

export default function VoiceControls({ onVoiceText }) {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef(null)

  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      alert("Speech recognition not supported in this browser")
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = "en-US"
    recognition.interimResults = false
    recognition.continuous = false

    recognition.onstart = () => {
      setListening(true)
    }

    recognition.onend = () => {
      setListening(false)
    }

    recognition.onerror = (e) => {
      console.error("STT error:", e)
      setListening(false)
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      onVoiceText(transcript)
    }

    recognitionRef.current = recognition
    recognition.start()
  }

  const stopListening = () => {
    recognitionRef.current?.stop()
  }

  return (
    <div className="flex flex-col items-center justify-center h-full gap-4">
      <button
        onClick={listening ? stopListening : startListening}
        className={`px-6 py-3 rounded-full text-white text-lg font-semibold ${
          listening ? "bg-red-500 animate-pulse" : "bg-blue-600"
        }`}
      >
        {listening ? "Listening…" : "Hold to Speak"}
      </button>

      <p className="text-gray-500 text-sm">
        Speak clearly after clicking the button
      </p>
    </div>
  )
}
