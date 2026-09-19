// Shared by the TTS workspace and the standalone Audio Studio.
// No DOM or application state: encoding can also be tested directly in Node.
globalThis.AIVoiceAudio = (() => {
  function encodeWav(channels, sampleRate) {
    const frameCount = channels[0]?.length
    if (!channels.length || channels.some(channel => channel.length !== frameCount)) {
      throw new Error('Audio channels must have matching lengths.')
    }
    if (!Number.isInteger(sampleRate) || sampleRate <= 0) {
      throw new Error('Sample rate must be a positive integer.')
    }

    const bytesPerSample = 2
    const blockAlign = channels.length * bytesPerSample
    const dataSize = frameCount * blockAlign
    const buffer = new ArrayBuffer(44 + dataSize)
    const view = new DataView(buffer)
    const writeText = (offset, text) => {
      for (let index = 0; index < text.length; index++) {
        view.setUint8(offset + index, text.charCodeAt(index))
      }
    }

    writeText(0, 'RIFF')
    view.setUint32(4, 36 + dataSize, true)
    writeText(8, 'WAVE')
    writeText(12, 'fmt ')
    view.setUint32(16, 16, true) // PCM format chunk size
    view.setUint16(20, 1, true) // Linear PCM
    view.setUint16(22, channels.length, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * blockAlign, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, 16, true) // Bits per sample
    writeText(36, 'data')
    view.setUint32(40, dataSize, true)

    let offset = 44
    for (let frame = 0; frame < frameCount; frame++) {
      for (const channel of channels) {
        const sample = Math.max(-1, Math.min(1, channel[frame]))
        view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
        offset += bytesPerSample
      }
    }
    return new Blob([buffer], {type: 'audio/wav'})
  }

  return {encodeWav}
})()
