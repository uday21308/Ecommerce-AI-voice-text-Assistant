import { useRef, useState } from "react"
import { API_BASE_URL } from "../config"
import botAvatar from "../assets/bot_avatar.png"
import SpeakingWaveform from "./SpeakingWaveform"

export default function ChatWindow({
  messages,
  setMessages,
  loading,
  setLoading,
  setToolInfo,
  setRetrievedDocs,
  onSpeak
}) {
  const inputRef = useRef(null)
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)

  // 🎤 Browser Speech-to-Text
  const startVoice = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel()
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      alert("Speech recognition not supported in this browser")
      return
    }

    if (listening) return

    const recognition = new SpeechRecognition()
    recognition.lang = "en-US"
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onstart = () => setListening(true)
    recognition.onend = () => setListening(false)

    recognition.onerror = () => setListening(false)

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript
      sendMessage(transcript)
    }

    recognition.start()
  }

  // 💬 Send Message
  const sendMessage = async (textOverride) => {
    const text = textOverride ?? inputRef.current.value.trim()
    if (!text) return

    setMessages(prev => [...prev, { role: "user", text }])
    inputRef.current.value = ""
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      })

      const data = await res.json()

      setMessages(prev => [...prev, { role: "assistant", text: data.reply }])
      setToolInfo(data.last_tool || null)
      setRetrievedDocs(data.retrieved_docs || [])

      setSpeaking(true)
      onSpeak?.(data.reply)

      setTimeout(() => {
        setSpeaking(false)
      }, Math.min(4000, data.reply.length * 40))
    } catch {
      setMessages(prev => [
        ...prev,
        { role: "assistant", text: "Sorry, something went wrong." }
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex items-end gap-2 animate-fadeInUp ${
              m.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {m.role === "assistant" && (
              <div className="flex items-center gap-2">
                <img
                  src={botAvatar}
                  alt="bot"
                  className={`w-8 h-8 rounded-full ${
                    speaking ? "ring-2 ring-blue-400" : ""
                  }`}
                />
                {speaking && <SpeakingWaveform />}
              </div>
            )}

            <div
              className={`max-w-[75%] px-4 py-2 rounded-2xl text-sm shadow-sm ${
                m.role === "user"
                  ? "bg-blue-600 text-white rounded-br-sm"
                  : "bg-gray-100 text-gray-800 rounded-bl-sm"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150"></span>
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-300"></span>
            Assistant is thinking…
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t p-3 flex items-center gap-2 bg-white">
        <button
          onClick={startVoice}
          className={`p-3 rounded-full transition-all duration-200 ${
            listening
              ? "bg-red-500 text-white animate-pulse scale-110"
              : "bg-gray-200 hover:bg-gray-300"
          }`}
          title="Speak"
        >
          🎤
        </button>

        <input
          ref={inputRef}
          type="text"
          placeholder="Type a message…"
          className="flex-1 border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-blue-400"
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />

        <button
          onClick={() => sendMessage()}
          className="bg-blue-600 hover:bg-blue-700 transition text-white px-4 py-2 rounded-lg"
        >
          Send
        </button>
      </div>
    </>
  )
}
