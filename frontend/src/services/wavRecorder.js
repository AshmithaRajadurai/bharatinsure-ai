/**
 * High-Fidelity Browser WAV Audio Recorder with Real-Time Audio Level Metering.
 * Encodes microphone stream to standard 16-bit PCM WAV blob.
 * Automatically handles browser audio context suspensions, variable hardware
 * sample rates (44.1kHz / 48kHz / 16kHz), downsampling, and acoustic feedback isolation.
 */

export class WavRecorder {
  constructor() {
    this.audioContext = null;
    this.mediaStream = null;
    this.processor = null;
    this.analyser = null;
    this.silentGain = null;
    this.dataArray = null;
    this.samples = [];
    this.sampleRate = 16000;
    this.isRecording = false;
  }

  async start() {
    this.samples = [];
    this.isRecording = true;

    // 1. Request microphone stream with voice-optimized constraints
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    // 2. Initialize AudioContext compatible with hardware
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    try {
      this.audioContext = new AudioContextClass();
    } catch {
      this.audioContext = new AudioContextClass({ sampleRate: 16000 });
    }

    // Modern browsers require explicit resume on user-initiated gesture
    if (this.audioContext.state === "suspended") {
      await this.audioContext.resume();
    }

    this.sampleRate = this.audioContext.sampleRate || 44100;

    // 3. Setup Analyser for real-time voice volume metering
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 256;
    this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);

    const source = this.audioContext.createMediaStreamSource(this.mediaStream);
    source.connect(this.analyser);

    // 4. Setup Audio Processing Node
    // Using 4096 buffer size for smooth streaming
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
    this.processor.onaudioprocess = (e) => {
      if (!this.isRecording) return;
      const channelData = e.inputBuffer.getChannelData(0);
      this.samples.push(new Float32Array(channelData));
    };

    source.connect(this.processor);

    // Connect via muted gain node to prevent speaker feedback loop
    this.silentGain = this.audioContext.createGain();
    this.silentGain.gain.value = 0;
    this.processor.connect(this.silentGain);
    this.silentGain.connect(this.audioContext.destination);
  }

  /**
   * Returns current real-time microphone volume level (0 to 100).
   * Useful for dynamic live voice visualizers.
   */
  getVolume() {
    if (!this.analyser || !this.dataArray || !this.isRecording) {
      return 0;
    }
    this.analyser.getByteFrequencyData(this.dataArray);
    let sum = 0;
    for (let i = 0; i < this.dataArray.length; i++) {
      sum += this.dataArray[i];
    }
    const avg = sum / this.dataArray.length;
    // Scale to a natural 0-100 range with sensitivity boost
    return Math.min(100, Math.round((avg / 255) * 100 * 2.2));
  }

  async stop() {
    this.isRecording = false;

    // Release microphone hardware
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
    }
    if (this.processor) {
      try {
        this.processor.disconnect();
      } catch {}
    }
    if (this.silentGain) {
      try {
        this.silentGain.disconnect();
      } catch {}
    }
    if (this.analyser) {
      try {
        this.analyser.disconnect();
      } catch {}
    }
    if (this.audioContext && this.audioContext.state !== "closed") {
      try {
        await this.audioContext.close();
      } catch {}
    }

    // Merge recorded sample buffers
    let totalLength = 0;
    for (const chunk of this.samples) {
      totalLength += chunk.length;
    }

    if (totalLength === 0) {
      return null;
    }

    const mergedSamples = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of this.samples) {
      mergedSamples.set(chunk, offset);
      offset += chunk.length;
    }

    // Downsample to 16,000 Hz for optimal STT accuracy & compact payload
    const TARGET_SAMPLE_RATE = 16000;
    const downsampled = this.downsampleBuffer(mergedSamples, this.sampleRate, TARGET_SAMPLE_RATE);

    return this.encodeWav(downsampled, TARGET_SAMPLE_RATE);
  }

  downsampleBuffer(buffer, inputSampleRate, outputSampleRate) {
    if (inputSampleRate === outputSampleRate || !inputSampleRate) {
      return buffer;
    }
    const sampleRateRatio = inputSampleRate / outputSampleRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    let offsetResult = 0;
    let offsetBuffer = 0;

    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
      let accum = 0;
      let count = 0;
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      result[offsetResult] = count > 0 ? accum / count : buffer[offsetBuffer] || 0;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    return result;
  }

  encodeWav(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    const writeString = (view, offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    // RIFF chunk descriptor
    writeString(view, 0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, "WAVE");

    // "fmt " sub-chunk
    writeString(view, 12, "fmt ");
    view.setUint32(16, 16, true); // 16 for PCM
    view.setUint16(20, 1, true); // AudioFormat: 1 = PCM
    view.setUint16(22, 1, true); // NumChannels: 1 (mono)
    view.setUint32(24, sampleRate, true); // SampleRate
    view.setUint32(28, sampleRate * 2, true); // ByteRate = SampleRate * 1 * 16/8
    view.setUint16(32, 2, true); // BlockAlign = 1 * 16/8
    view.setUint16(34, 16, true); // BitsPerSample: 16

    // "data" sub-chunk
    writeString(view, 36, "data");
    view.setUint32(40, samples.length * 2, true);

    // Write PCM 16-bit audio samples
    let sampleOffset = 44;
    for (let i = 0; i < samples.length; i++, sampleOffset += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(sampleOffset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }

    return new Blob([view], { type: "audio/wav" });
  }
}
