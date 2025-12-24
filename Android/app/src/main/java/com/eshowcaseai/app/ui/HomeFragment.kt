package com.eshowcaseai.app.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import com.eshowcaseai.app.R
import com.eshowcaseai.app.databinding.FragmentHomeBinding
import com.eshowcaseai.app.viewmodel.BootstrapViewModel

class HomeFragment : Fragment() {
    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!
    private val viewModel: BootstrapViewModel by activityViewModels()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        viewModel.uiState.observe(viewLifecycleOwner) { state ->
            binding.txtHomeStatus.text = state
            if (state.contains("已連接")) {
                binding.viewStatusDot.setBackgroundResource(R.drawable.bg_status_dot_green)
            } else {
                binding.viewStatusDot.setBackgroundResource(R.drawable.bg_status_dot_red)
            }
        }

        viewModel.logText.observe(viewLifecycleOwner) { logs ->
            binding.txtHomeLog.text = logs
        }

        binding.btnActivation.setOnClickListener {
            (activity as? NavigationHost)?.navigateTo(ActivationFragment())
        }

        binding.btnEnterChat.setOnClickListener {
            (activity as? NavigationHost)?.navigateTo(ConversationFragment())
        }

        // 自动连接
        if (viewModel.uiState.value == "準備就緒") {
            viewModel.bootstrap()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

interface NavigationHost {
    fun navigateTo(fragment: Fragment)
    fun showLogs()
}
