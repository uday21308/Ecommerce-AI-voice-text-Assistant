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
    <div className="min-h-screen flex items-center justify-center p-6
  bg-gradient-to-br from-indigo-50 via-blue-50 to-purple-50">
    <div className="absolute inset-0 overflow-hidden -z-10">
        <div className="absolute top-20 left-10 w-72 h-72 bg-purple-300 rounded-full blur-3xl opacity-30"></div>
        <div className="absolute bottom-20 right-10 w-72 h-72 bg-blue-300 rounded-full blur-3xl opacity-30"></div>
        <div className="absolute top-1/2 right-1/3 w-60 h-60 bg-indigo-300 rounded-full blur-3xl opacity-20"></div>
      </div>
      {/* Chat Card */}
      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Chat */}
        <div className="md:col-span-2 rounded-2xl shadow-[0_20px_50px_rgba(8,_112,_184,_0.15)] flex flex-col h-[80vh]
                        bg-white/70 backdrop-blur-lg border border-white/40">
          <div className="relative px-6 py-5 text-center rounded-t-2xl
                          bg-gradient-to-r from-indigo-600 via-blue-600 to-purple-600">
  
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white">
                 Ecommerce AI Assistant
              </h1>

               <p className="text-sm text-blue-100 mt-1 font-medium">
                Voice & Text Customer Support
              </p>
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
