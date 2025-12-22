package com.xiaozhi.app.core.live2d

import android.app.Activity
import android.content.Context
import android.opengl.GLSurfaceView
import android.util.AttributeSet
import android.view.MotionEvent
import com.live2d.demo.full.LAppDelegate
import com.live2d.demo.full.LAppLive2DManager
import com.live2d.demo.full.GLRenderer

/**
 * Custom View for Live2D rendering using GLSurfaceView.
 */
class Live2DView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : GLSurfaceView(context, attrs) {

    private val renderer: GLRenderer
    private var lipSyncController: LipSyncController? = null
    private var isSpeaking = false

    /**
     * Callback for when Live2D is fully initialized and ready to use.
     */
    var onReady: (() -> Unit)? = null

    /**
     * Set the speaking state to control lip sync animation.
     * This safely communicates with the GL thread.
     */
    fun setSpeaking(speaking: Boolean) {
        this.isSpeaking = speaking
        queueEvent {
            updateLipSyncState()
        }
    }

    private fun updateLipSyncState() {
        // Safety check: Ensure framework is initialized before accessing manager or model
        if (!com.live2d.sdk.cubism.framework.CubismFramework.isInitialized()) {
            return
        }

        if (lipSyncController == null) {
            val model = LAppLive2DManager.getInstance().getModel(0)
            if (model != null) {
                lipSyncController = LipSyncController(model)
            }
        }
        
        if (isSpeaking) {
            lipSyncController?.start()
        } else {
            lipSyncController?.stop()
        }
    }

    init {
        // Setup OpenGL ES 2.0 context
        setEGLContextClientVersion(2)
        
        // Setup for transparency
        setEGLConfigChooser(8, 8, 8, 8, 16, 0)
        holder.setFormat(android.graphics.PixelFormat.TRANSLUCENT)
        setZOrderMediaOverlay(true)

        renderer = GLRenderer()
        renderer.setOnSurfaceCreatedListener {
            // Framework is initialized in onSurfaceCreated, so we can now update state
            queueEvent {
                updateLipSyncState()
            }
            post {
                onReady?.invoke()
            }
        }
        setRenderer(renderer)
        renderMode = RENDERMODE_CONTINUOUSLY
        preserveEGLContextOnPause = true
    }

    /**
     * Initialize the Live2D SDK with an activity.
     */
    fun initSDK(activity: Activity) {
        LAppDelegate.getInstance().onStart(activity)
    }

    override fun onResume() {
        super.onResume()
    }

    override fun onPause() {
        super.onPause()
        LAppDelegate.getInstance().onPause()
    }

    fun release() {
        val appInstance = LAppDelegate.getInstance()
        LAppDelegate.releaseInstance() // Clear the singleton immediately on UI thread
        
        queueEvent {
            appInstance.release()
        }
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        val x = event.x
        val y = event.y

        queueEvent {
            when (event.action) {
                MotionEvent.ACTION_DOWN -> LAppDelegate.getInstance().onTouchBegan(x, y)
                MotionEvent.ACTION_UP -> LAppDelegate.getInstance().onTouchEnd(x, y)
                MotionEvent.ACTION_MOVE -> LAppDelegate.getInstance().onTouchMoved(x, y)
            }
        }
        return true
    }
}
