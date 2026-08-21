/**
 * Web Audio API 기반 알림 사운드 재생 유틸리티
 * - 외부 오디오 파일 다운로드 없이 브라우저 내장 오디오 엔진으로 맑은 차임벨 합성
 * - 지연 시간 0ms, 404 에러 원천 방지, 부드러운 벨소리 연출
 */

let audioCtx: AudioContext | null = null
let lastPlayTime = 0

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
    if (AudioContextClass) {
      audioCtx = new AudioContextClass()
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume().catch(() => {})
  }
  return audioCtx
}

// 브라우저 첫 사용자 클릭/터치 시 AudioContext 활성화
if (typeof window !== 'undefined') {
  const unlockAudio = () => {
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume().catch(() => {})
    }
    window.removeEventListener('click', unlockAudio)
    window.removeEventListener('keydown', unlockAudio)
  }
  window.addEventListener('click', unlockAudio, { passive: true })
  window.addEventListener('keydown', unlockAudio, { passive: true })
}

/**
 * 맑고 경쾌한 2화음 알림 차임벨 재생 (딩-동♪)
 * @param volume 음량 (0.0 ~ 1.0, 기본값 0.25)
 */
export function playNotificationSound(volume = 0.25) {
  const now = Date.now()
  // 1초 이내 중복 재생 방지
  if (now - lastPlayTime < 800) return
  lastPlayTime = now

  try {
    const ctx = getAudioContext()
    if (!ctx) return

    const currentTime = ctx.currentTime

    // 1st Tone (880Hz - A5)
    const osc1 = ctx.createOscillator()
    const gain1 = ctx.createGain()

    osc1.type = 'sine'
    osc1.frequency.setValueAtTime(880, currentTime)
    osc1.frequency.exponentialRampToValueAtTime(870, currentTime + 0.3)

    gain1.gain.setValueAtTime(0, currentTime)
    gain1.gain.linearRampToValueAtTime(volume, currentTime + 0.02)
    gain1.gain.exponentialRampToValueAtTime(0.0001, currentTime + 0.45)

    osc1.connect(gain1)
    gain1.connect(ctx.destination)

    osc1.start(currentTime)
    osc1.stop(currentTime + 0.5)

    // 2nd Tone (1318.5Hz - E6: 맑은 고음 차임)
    const osc2 = ctx.createOscillator()
    const gain2 = ctx.createGain()

    const tone2Start = currentTime + 0.12

    osc2.type = 'sine'
    osc2.frequency.setValueAtTime(1318.5, tone2Start)
    osc2.frequency.exponentialRampToValueAtTime(1310, tone2Start + 0.5)

    gain2.gain.setValueAtTime(0, tone2Start)
    gain2.gain.linearRampToValueAtTime(volume * 0.9, tone2Start + 0.02)
    gain2.gain.exponentialRampToValueAtTime(0.0001, tone2Start + 0.65)

    osc2.connect(gain2)
    gain2.connect(ctx.destination)

    osc2.start(tone2Start)
    osc2.stop(tone2Start + 0.7)
  } catch (err) {
    console.debug('Notification sound playback error:', err)
  }
}
