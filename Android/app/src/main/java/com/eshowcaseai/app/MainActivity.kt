package com.eshowcaseai.app

import android.os.Bundle
import android.view.View
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.eshowcaseai.app.databinding.ActivityMainBinding
import com.eshowcaseai.app.ui.HomeFragment
import com.eshowcaseai.app.ui.ConversationFragment
import com.eshowcaseai.app.ui.NavigationHost
import com.eshowcaseai.app.viewmodel.BootstrapViewModel

import androidx.activity.result.contract.ActivityResultContracts
import android.Manifest
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity(), NavigationHost {

    private lateinit var binding: ActivityMainBinding
    private val viewModel: BootstrapViewModel by viewModels()

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            // Permission granted
        } else {
            // Permission denied, maybe show a message
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        checkPermissions()

        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.fragmentContainer, ConversationFragment())
                .commit()
        }

        binding.btnCloseLogs.setOnClickListener {
            binding.layoutLogOverlay.visibility = View.GONE
        }

        viewModel.logText.observe(this) { logs ->
            binding.txtLog.text = logs
            binding.txtLog.post {
                val scrollY = binding.txtLog.bottom
                (binding.txtLog.parent as? android.widget.ScrollView)?.smoothScrollTo(0, scrollY)
            }
        }
    }

    override fun navigateTo(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .setCustomAnimations(
                android.R.anim.fade_in,
                android.R.anim.fade_out,
                android.R.anim.fade_in,
                android.R.anim.fade_out
            )
            .replace(R.id.fragmentContainer, fragment)
            .addToBackStack(null)
            .commit()
    }

    override fun showLogs() {
        binding.layoutLogOverlay.visibility = View.VISIBLE
    }

    private fun checkPermissions() {
        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
        }
    }
}
