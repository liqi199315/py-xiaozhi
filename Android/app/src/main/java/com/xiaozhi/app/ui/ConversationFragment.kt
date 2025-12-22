package com.xiaozhi.app.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.animation.AlphaAnimation
import android.view.animation.Animation
import android.view.animation.ScaleAnimation
import android.view.animation.AnimationSet
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import com.xiaozhi.app.databinding.FragmentConversationBinding
import com.xiaozhi.app.viewmodel.BootstrapViewModel

class ConversationFragment : Fragment() {
    private var _binding: FragmentConversationBinding? = null
    private val binding get() = _binding!!
    private val viewModel: BootstrapViewModel by activityViewModels()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentConversationBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // 必须先初始化 Live2D，否则后续 observer 访问 lipSyncController 会因 Activity 为空而失败
        binding.live2dView.initSDK(requireActivity())

        // 自动开始引导流程
        if (viewModel.isReady.value != true) {
            viewModel.bootstrap()
        }

        viewModel.currentSentence.observe(viewLifecycleOwner) { sentence ->
            if (sentence.isNotEmpty()) {
                binding.txtChatResponse.text = sentence
                binding.commArea.visibility = View.VISIBLE
            } else {
                binding.commArea.visibility = View.INVISIBLE
            }
        }

        viewModel.isListening.observe(viewLifecycleOwner) { isListening ->
            binding.btnChatVoice.text = if (isListening) "正在聆聽... (點擊停止)" else "按住說話"
            if (isListening) {
                startAuraAnimation(com.xiaozhi.app.R.drawable.bg_aura_listening)
                binding.txtCommLabel.text = "LISTENING..."
            } else if (viewModel.isSpeaking.value != true) {
                stopAuraAnimation()
            }
        }

        binding.live2dView.onReady = {
            viewModel.isSpeaking.observe(viewLifecycleOwner) { isSpeaking ->
                binding.live2dView.setSpeaking(isSpeaking)
                if (isSpeaking) {
                    startAuraAnimation(com.xiaozhi.app.R.drawable.bg_aura_speaking)
                    binding.txtCommLabel.text = "INCOMING TRANSMISSION"
                } else if (viewModel.isListening.value != true) {
                    stopAuraAnimation()
                }
            }
        }

        viewModel.isReady.observe(viewLifecycleOwner) { isReady ->
            if (isReady) {
                binding.loadingOverlay.visibility = View.GONE
            } else {
                binding.loadingOverlay.visibility = View.VISIBLE
            }
        }

        viewModel.isBootstrapping.observe(viewLifecycleOwner) { isBootstrapping ->
            if (isBootstrapping) {
                binding.pbLoading.visibility = View.VISIBLE
            } else {
                binding.pbLoading.visibility = View.GONE
            }
        }

        viewModel.activationCode.observe(viewLifecycleOwner) { code ->
            if (code != null) {
                binding.layoutActivation.visibility = View.VISIBLE
                binding.txtActivationCode.text = code
                binding.txtLoadingStatus.text = "等待激活..."
            } else {
                binding.layoutActivation.visibility = View.GONE
            }
        }

        viewModel.uiState.observe(viewLifecycleOwner) { state ->
            if (viewModel.activationCode.value == null) {
                binding.txtLoadingStatus.text = state
            }
        }

        binding.btnChatSend.setOnClickListener {
            val text = binding.edtChatInput.text.toString()
            if (text.isNotBlank()) {
                viewModel.sendText(text)
                binding.edtChatInput.text.clear()
            }
        }

        binding.btnChatVoice.setOnClickListener {
            viewModel.toggleListen()
        }

        binding.btnBackFromChat.setOnClickListener {
            parentFragmentManager.popBackStack()
        }
    }

    override fun onResume() {
        super.onResume()
        binding.live2dView.onResume()
    }

    override fun onPause() {
        super.onPause()
        binding.live2dView.onPause()
    }

    private var auraAnimation: Animation? = null

    private fun startAuraAnimation(drawableRes: Int) {
        binding.viewAura.setBackgroundResource(drawableRes)
        binding.viewAura.alpha = 1f
        
        if (auraAnimation != null) return

        val scaleAnim = ScaleAnimation(
            0.8f, 1.2f, 0.8f, 1.2f,
            Animation.RELATIVE_TO_SELF, 0.5f,
            Animation.RELATIVE_TO_SELF, 0.5f
        ).apply {
            duration = 2000
            repeatCount = Animation.INFINITE
            repeatMode = Animation.REVERSE
        }

        val alphaAnim = AlphaAnimation(0.3f, 0.7f).apply {
            duration = 2000
            repeatCount = Animation.INFINITE
            repeatMode = Animation.REVERSE
        }

        auraAnimation = AnimationSet(true).apply {
            addAnimation(scaleAnim)
            addAnimation(alphaAnim)
        }
        binding.viewAura.startAnimation(auraAnimation)
    }

    private fun stopAuraAnimation() {
        binding.viewAura.clearAnimation()
        binding.viewAura.alpha = 0f
        auraAnimation = null
    }

    override fun onDestroyView() {
        binding.live2dView.release()
        super.onDestroyView()
        _binding = null
    }
}
