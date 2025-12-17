import { useEffect, useState } from "react"
import ChatWindow from "./components/ChatWindow"
import ToolPanel from "./components/ToolPanel"
import { speak } from "./utils/tts"
import { API_BASE_URL } from "./config"

export default function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [toolInfo, setToolInfo] = useState(null)
  const [retrievedDocs, setRetrievedDocs] = useState([])

  // Initial greeting
  useEffect(() => {
    const greeting =
      "Hi 👋 I’m your ecommerce assistant. You can ask about products, orders, or returns."

    setMessages([{ role: "assistant", text: greeting }])
    speak(greeting)
  }, [])

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-6">
      {/* Chat Card */}
      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Chat */}
        <div className="md:col-span-2 bg-white rounded-xl shadow-lg flex flex-col h-[80vh]">
          <div className="px-5 py-4 border-b font-semibold text-lg">
            🛒 Ecommerce AI Assistant
          </div>

          <ChatWindow
            messages={messages}
            setMessages={setMessages}
            loading={loading}
            setLoading={setLoading}
            setToolInfo={setToolInfo}
            setRetrievedDocs={setRetrievedDocs}
            onSpeak={speak}
          />
        </div>

        {/* Tool Panel */}
        <div className="bg-white rounded-xl shadow-lg p-4 overflow-auto h-[80vh]">
          <ToolPanel
            toolInfo={toolInfo}
            retrievedDocs={retrievedDocs}
          />
        </div>
      </div>
    </div>
  )
}
