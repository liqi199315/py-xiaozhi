package com.xiaozhi.app.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import com.xiaozhi.app.databinding.FragmentActivationBinding
import com.xiaozhi.app.viewmodel.BootstrapViewModel

class ActivationFragment : Fragment() {
    private var _binding: FragmentActivationBinding? = null
    private val binding get() = _binding!!
    private val viewModel: BootstrapViewModel by activityViewModels()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentActivationBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        viewModel.activationCode.observe(viewLifecycleOwner) { code ->
            binding.txtActCodeLarge.text = code ?: "----"
        }

        viewModel.uiState.observe(viewLifecycleOwner) { state ->
            binding.txtActStatus.text = state
        }

        binding.btnStartAct.setOnClickListener {
            viewModel.bootstrap()
        }

        binding.btnBackFromAct.setOnClickListener {
            parentFragmentManager.popBackStack()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
