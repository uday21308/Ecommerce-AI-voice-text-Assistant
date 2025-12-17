export function speak(text) {
  if (!("speechSynthesis" in window)) return

  window.speechSynthesis.cancel()

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = "en-US"
  utterance.rate = 1
  utterance.pitch = 1

  window.speechSynthesis.speak(utterance)
}
