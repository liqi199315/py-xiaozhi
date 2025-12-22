package com.xiaozhi.app.core.audio

import android.annotation.SuppressLint
import android.media.*
import android.util.Log
import java.util.concurrent.LinkedBlockingQueue
import kotlin.concurrent.thread

class AudioPipeline(
    private val onAudioCaptured: (ByteArray) -> Unit,
    private val onPlaybackStateChanged: (Boolean) -> Unit = {}
) {
    private var isSpeaking = false
    private var lastPlayTime = 0L
    private val speakingTimeoutMs = 500L
    private var speakingCheckThread: Thread? = null
    private var isReleased = false
    private var audioRecord: AudioRecord? = null
    private var audioTrack: AudioTrack? = null
    private var isRecording = false
    private var recordingThread: Thread? = null
    private var encoder: MediaCodec? = null
    private var ampLogCount = 0

    private val sampleRate = AudioConfig.SAMPLE_RATE
    private val channels = AudioConfig.CHANNELS
    private val channelConfigIn = AudioFormat.CHANNEL_IN_MONO
    private val channelConfigOut = AudioFormat.CHANNEL_OUT_MONO
    private val audioFormat = AudioFormat.ENCODING_PCM_16BIT
    private val bufferSizeIn = AudioRecord.getMinBufferSize(sampleRate, channelConfigIn, audioFormat) * 4
    private val bufferSizeOut = AudioTrack.getMinBufferSize(sampleRate, channelConfigOut, audioFormat)

    private var decoder: MediaCodec? = null
    private val decoderFormat = MediaFormat.createAudioFormat(MediaFormat.MIMETYPE_AUDIO_OPUS, sampleRate, channels).apply {
        // Opus 具体的 CSD-0 (Identification Header) 和 CSD-1 (Pre-skip) 
        // 对于流式播放，MediaCodec 通常能自动处理或需要特定的配置
    }

    @SuppressLint("MissingPermission")
    fun startCapture() {
        if (isRecording) return
        isRecording = true

        if (speakingCheckThread == null) {
            startSpeakingCheck()
        }

        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            initEncoder()
        } else {
            Log.w("AudioPipeline", "当前 Android 版本低于 10 (API 29)，MediaCodec 可能不支持 Opus 编码")
            initEncoder() // 尝试初始化，某些设备可能提前支持
        }

        audioRecord = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            sampleRate,
            channelConfigIn,
            audioFormat,
            bufferSizeIn
        )

        if (audioRecord?.state != AudioRecord.STATE_INITIALIZED) {
            Log.e("AudioPipeline", "AudioRecord 初始化失败！请检查权限或设备是否支持采样率 $sampleRate")
            audioRecord?.release()
            audioRecord = null
            isRecording = false
            return
        }

        audioRecord?.startRecording()
        if (audioRecord?.recordingState != AudioRecord.RECORDSTATE_RECORDING) {
            Log.e("AudioPipeline", "AudioRecord 启动录音失败！")
            isRecording = false
            return
        }
        recordingThread = thread(start = true, name = "AudioCaptureThread") {
            val bufferSize = sampleRate * 2 * AudioConfig.FRAME_DURATION_MS / 1000
            val buffer = ByteArray(bufferSize)
            var framesCount = 0
            
            while (isRecording) {
                val read = audioRecord?.read(buffer, 0, buffer.size) ?: -1
                if (read > 0) {
                    // 1. 前 5 帧（约 100ms）丢弃，用于清空硬件缓冲区积压
                    if (framesCount < 5) {
                        framesCount++
                        continue
                    }

                    // 2. 数字增益：放大 4 倍 (左移 2 位)
                    applyGain(buffer, read, 4.0f)

                    if (encoder != null) {
                        val maxAmp = calculateMaxAmplitude(buffer, read)
                        ampLogCount++
                        if (ampLogCount % 100 == 0) {
                            Log.d("AudioPipeline", "录音中, Max Amp: $maxAmp, Read: $read")
                        }
                        
                        queueInputToEncoder(buffer, read)
                        drainEncoder { encoded ->
                            onAudioCaptured(encoded)
                        }
                    } else {
                        onAudioCaptured(buffer.copyOf(read))
                    }
                } else if (read < 0) {
                    Log.e("AudioPipeline", "AudioRecord 读取错误: $read")
                    break
                }
            }
        }
        Log.i("AudioPipeline", "开始采集音频 (MIC)")
    }

    private fun applyGain(data: ByteArray, size: Int, gain: Float) {
        for (i in 0 until size - 1 step 2) {
            var sample = (data[i + 1].toInt() shl 8) or (data[i].toInt() and 0xFF)
            sample = (sample * gain).toInt()
            // 钳位防止溢出
            if (sample > 32767) sample = 32767
            else if (sample < -32768) sample = -32768
            
            data[i] = (sample and 0xFF).toByte()
            data[i + 1] = ((sample shr 8) and 0xFF).toByte()
        }
    }

    private fun calculateMaxAmplitude(data: ByteArray, size: Int): Int {
        var max = 0
        for (i in 0 until size - 1 step 2) {
            val sample = (data[i + 1].toInt() shl 8) or (data[i].toInt() and 0xFF)
            val absSample = Math.abs(sample)
            if (absSample > max) max = absSample
        }
        return max
    }

    private fun queueInputToEncoder(data: ByteArray, size: Int) {
        val currentEncoder = encoder ?: return
        try {
            val inputIndex = currentEncoder.dequeueInputBuffer(10000)
            if (inputIndex >= 0) {
                val inputBuffer = currentEncoder.getInputBuffer(inputIndex)
                inputBuffer?.clear()
                inputBuffer?.put(data, 0, size)
                currentEncoder.queueInputBuffer(inputIndex, 0, size, System.nanoTime() / 1000, 0)
            }
        } catch (e: Exception) {
            Log.e("AudioPipeline", "入队编码器失败: ${e.message}")
        }
    }

    private fun drainEncoder(onEncoded: (ByteArray) -> Unit) {
        val currentEncoder = encoder ?: return
        val info = MediaCodec.BufferInfo()
        try {
            while (true) {
                val outputIndex = currentEncoder.dequeueOutputBuffer(info, 0)
                if (outputIndex == MediaCodec.INFO_TRY_AGAIN_LATER) break
                if (outputIndex == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) continue
                if (outputIndex < 0) break

                if ((info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG) != 0) {
                    // 跳过配置帧
                } else if (info.size > 0) {
                    val outputBuffer = currentEncoder.getOutputBuffer(outputIndex)
                    if (outputBuffer != null) {
                        val encodedData = ByteArray(info.size)
                        outputBuffer.get(encodedData)
                        onEncoded(encodedData)
                    }
                }
                currentEncoder.releaseOutputBuffer(outputIndex, false)
            }
        } catch (e: Exception) {
            Log.e("AudioPipeline", "出队编码器失败: ${e.message}")
        }
    }

    fun stopCapture() {
        isRecording = false
        recordingThread?.join(500)
        recordingThread = null
        
        audioRecord?.stop()
        audioRecord?.release()
        audioRecord = null
        
        releaseEncoder()
        Log.i("AudioPipeline", "停止采集音频")
    }

    private fun initEncoder() {
        try {
            encoder = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_AUDIO_OPUS)
            val format = MediaFormat.createAudioFormat(MediaFormat.MIMETYPE_AUDIO_OPUS, sampleRate, channels)
            format.setInteger(MediaFormat.KEY_BIT_RATE, 32000)
            format.setInteger(MediaFormat.KEY_COMPLEXITY, 5)
            // Opus 编码不需要像解码那样设置 CSD，MediaCodec 会处理
            encoder?.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            encoder?.start()
            Log.i("AudioPipeline", "Opus 编码器初始化成功")
        } catch (e: Exception) {
            Log.e("AudioPipeline", "Opus 编码器初始化失败: ${e.message}")
            encoder = null
        }
    }

    private fun releaseEncoder() {
        try {
            encoder?.stop()
            encoder?.release()
        } catch (e: Exception) {}
        encoder = null
    }

    private val playbackSampleRate = 48000 // Opus 内部标准采样率

    @Synchronized
    fun play(data: ByteArray) {
        lastPlayTime = System.currentTimeMillis()
        if (!isSpeaking) {
            isSpeaking = true
            onPlaybackStateChanged(true)
        }
        
        if (speakingCheckThread == null) {
            startSpeakingCheck()
        }

        try {
            if (audioTrack == null) {
                audioTrack = AudioTrack(
                    AudioManager.STREAM_MUSIC,
                    playbackSampleRate,
                    channelConfigOut,
                    audioFormat,
                    AudioTrack.getMinBufferSize(playbackSampleRate, channelConfigOut, audioFormat),
                    AudioTrack.MODE_STREAM
                )
                audioTrack?.play()
            }

            // 初始化解码器
            if (decoder == null) {
                decoder = MediaCodec.createDecoderByType(MediaFormat.MIMETYPE_AUDIO_OPUS)
                val format = MediaFormat.createAudioFormat(MediaFormat.MIMETYPE_AUDIO_OPUS, playbackSampleRate, channels)
                
                // 注入 Opus CSD 数据 (Codec Specific Data)
                // CSD-0: Opus Identification Header (OpusHead)
                val csd0 = ByteArray(19)
                csd0[0] = 'O'.toByte(); csd0[1] = 'p'.toByte(); csd0[2] = 'u'.toByte(); csd0[3] = 's'.toByte()
                csd0[4] = 'H'.toByte(); csd0[5] = 'e'.toByte(); csd0[6] = 'a'.toByte(); csd0[7] = 'd'.toByte()
                csd0[8] = 1 // 版本号
                csd0[9] = channels.toByte() // 声道数
                // 10-11: Pre-skip (Little Endian), 12-15: Original Sample Rate, 16-17: Output Gain, 18: Channel Mapping Family
                val preSkip = 312 // 默认预跳过
                csd0[10] = (preSkip and 0xFF).toByte()
                csd0[11] = ((preSkip shr 8) and 0xFF).toByte()
                
                format.setByteBuffer("csd-0", java.nio.ByteBuffer.wrap(csd0))
                
                // CSD-1: Pre-skip in nanoseconds
                val csd1 = ByteArray(8) // 也可以留空，某些设备需要
                format.setByteBuffer("csd-1", java.nio.ByteBuffer.wrap(csd1))
                
                // CSD-2: Identification Header (OpusTags) - 通常不需要
                
                decoder?.configure(format, null, null, 0)
                decoder?.start()
                Log.i("AudioPipeline", "Opus 解码器初始化成功 (48kHz)")
            }

            val currentDecoder = decoder ?: return

            // 将 Opus 数据喂给解码器
            val inputIndex = currentDecoder.dequeueInputBuffer(10000)
            if (inputIndex >= 0) {
                val inputBuffer = currentDecoder.getInputBuffer(inputIndex)
                inputBuffer?.clear()
                inputBuffer?.put(data)
                currentDecoder.queueInputBuffer(inputIndex, 0, data.size, 0, 0)
            }

            // 获取解码后的 PCM
            val info = MediaCodec.BufferInfo()
            var outputIndex = currentDecoder.dequeueOutputBuffer(info, 10000)
            while (outputIndex >= 0) {
                val outputBuffer = currentDecoder.getOutputBuffer(outputIndex)
                if (outputBuffer != null) {
                    val pcmData = ByteArray(info.size)
                    outputBuffer.get(pcmData)
                    audioTrack?.write(pcmData, 0, pcmData.size)
                }
                currentDecoder.releaseOutputBuffer(outputIndex, false)
                outputIndex = currentDecoder.dequeueOutputBuffer(info, 0)
            }
        } catch (e: Exception) {
            Log.e("AudioPipeline", "解码播放失败，尝试重置: ${e.message}")
            resetDecoder()
        }
    }

    private fun resetDecoder() {
        try {
            decoder?.stop()
            decoder?.release()
        } catch (ex: Exception) {
            // ignore
        }
        decoder = null
    }

    private fun startSpeakingCheck() {
        speakingCheckThread = thread(start = true, name = "SpeakingCheckThread") {
            while (!isReleased) {
                val now = System.currentTimeMillis()
                if (isSpeaking && now - lastPlayTime > speakingTimeoutMs) {
                    isSpeaking = false
                    onPlaybackStateChanged(false)
                }
                try {
                    Thread.sleep(100)
                } catch (e: InterruptedException) {
                    break
                }
            }
        }
    }

    @Synchronized
    fun release() {
        isReleased = true
        speakingCheckThread?.interrupt()
        speakingCheckThread = null
        
        stopCapture()
        try {
            audioTrack?.stop()
            audioTrack?.release()
        } catch (e: Exception) {}
        audioTrack = null
        
        resetDecoder()
    }
}
