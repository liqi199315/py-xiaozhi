package com.xiaozhi.app.core.live2d

import com.live2d.demo.full.LAppModel
import java.util.Timer
import java.util.TimerTask
import java.util.Random

/**
 * Controller for Live2D lip sync (mouth movement).
 * Simulates mouth movement by setting random values to the model's lip sync parameter.
 */
class LipSyncController(private val model: LAppModel) {
    private var timer: Timer? = null
    private val random = Random()

    /**
     * Start the lip sync animation.
     */
    fun start() {
        if (timer != null) return
        
        timer = Timer().apply {
            scheduleAtFixedRate(object : TimerTask() {
                override fun run() {
                    // Generate a random value between 0.2 and 1.0 to simulate speech
                    val mouthOpenY = random.nextFloat() * 0.8f + 0.2f
                    model.setLipSyncValue(mouthOpenY)
                }
            }, 0, 100) // Update every 100ms
        }
    }

    /**
     * Stop the lip sync animation and reset mouth to closed.
     */
    fun stop() {
        timer?.cancel()
        timer = null
        model.setLipSyncValue(0f)
    }
}
