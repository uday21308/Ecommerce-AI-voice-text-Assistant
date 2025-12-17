import { useRef, useState, useEffect } from "react"
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
  const bottomRef = useRef(null)

  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)

  // 🔽 Auto-scroll when messages or loading change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  // 🎤 Browser Speech-to-Text
  const startVoice = () => {
    window.speechSynthesis.cancel()

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      alert("Speech recognition not supported")
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

  // 🔊 Speak with REAL lifecycle tracking
  const speakWithWaveform = (text) => {
    if (!("speechSynthesis" in window)) return

    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = "en-US"

    utterance.onstart = () => setSpeaking(true)
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)

    window.speechSynthesis.speak(utterance)
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

      speakWithWaveform(data.reply)

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
      {/* 💬 Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex items-end gap-2 ${
              m.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {m.role === "assistant" && (
              <div className="flex items-center gap-2">
                <img
                  src={botAvatar}
                  alt="bot"
                  className={`w-8 h-8 rounded-full ${
                    speaking ? "ring-2 ring-blue-400 animate-pulse" : ""
                  }`}
                />
                {speaking && <SpeakingWaveform />}
              </div>
            )}

            <div
              className={`max-w-[75%] px-4 py-2 rounded-2xl text-[14px] leading-relaxed font-medium ${
                m.role === "user"
                  ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white"
                  : "bg-white/80 text-gray-800 backdrop-blur border border-gray-200"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-gray-500 text-sm animate-pulse">
            <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
            <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
            <span className="w-2 h-2 bg-purple-400 rounded-full"></span>
            Assistant is thinking…
          </div>
        )}

        {/* ⬇️ Scroll Anchor */}
        <div ref={bottomRef} />
      </div>

      {/* ⌨️ Input */}
      <div className="border-t p-3 flex items-center gap-2 bg-white">
        <button
          onClick={startVoice}
          className={`p-3 rounded-full transition-all duration-300 ${
            listening
              ? "bg-red-500 text-white animate-pulse scale-110"
              : "bg-white shadow hover:shadow-md"
          }`}
        >
          🎤
        </button>

        <input
          ref={inputRef}
          type="text"
          placeholder="Type a message…"
          className="flex-1 border rounded-xl px-4 py-2.5 text-sm font-medium
placeholder:text-gray-400 focus:ring-2 focus:ring-blue-400 outline-none"
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />

        <button
          onClick={() => sendMessage()}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
        >
          Send
        </button>
      </div>
    </>
  )
}
