export default function SpeakingWaveform() {
  return (
    <div className="flex items-center gap-1 h-6">
      {[...Array(5)].map((_, i) => (
        <span
          key={i}
          className="w-1 rounded bg-blue-500 animate-wave"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  )
}
