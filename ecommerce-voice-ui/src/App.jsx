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
    <div className="relative min-h-screen flex items-center justify-center p-6
  bg-gradient-to-br from-rose-100 via-red-100 to-orange-100 overflow-hidden">
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
               bg-gradient-to-r from-red-600 via-rose-600 to-orange-500">

                <h1 className="text-2xl md:text-2xl font-extrabold tracking-tight text-white">
                  Ecommerce AI Assistant
                </h1>

                <p className="text-sm text-red-100 mt-1 font-medium">
                  Voice & Text Customer Support
                </p>

               <div className="mt-3 h-[1px] w-full bg-gradient-to-r from-transparent via-white/40 to-transparent" />
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
