package com.xiaozhi.app.ui.widget

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View

class GridBackgroundView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private val paint = Paint().apply {
        color = android.graphics.Color.parseColor("#0D00F3FF") // Cyan with very low alpha (approx 5%)
        strokeWidth = 2f
        style = Paint.Style.STROKE
    }

    private val gridSize = 120f // Approx 40dp

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        
        val width = width.toFloat()
        val height = height.toFloat()

        // Draw vertical lines
        var x = 0f
        while (x <= width) {
            canvas.drawLine(x, 0f, x, height, paint)
            x += gridSize
        }

        // Draw horizontal lines
        var y = 0f
        while (y <= height) {
            canvas.drawLine(0f, y, width, y, paint)
            y += gridSize
        }
    }
}
