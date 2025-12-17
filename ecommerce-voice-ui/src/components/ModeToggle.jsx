export default function ModeToggle({ mode, setMode }) {
  return (
    <div className="flex bg-gray-200 rounded-lg p-1">
      <button
        onClick={() => setMode("chat")}
        className={`px-4 py-1 rounded-md text-sm font-medium transition ${
          mode === "chat"
            ? "bg-white shadow"
            : "text-gray-600"
        }`}
      >
        Chat
      </button>

      <button
        onClick={() => setMode("voice")}
        className={`px-4 py-1 rounded-md text-sm font-medium transition ${
          mode === "voice"
            ? "bg-white shadow"
            : "text-gray-600"
        }`}
      >
        Voice
      </button>
    </div>
  )
}
