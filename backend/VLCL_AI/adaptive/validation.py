# validation.py
import numpy as np
from typing import Dict, List, Any
from VLCL_AI.adaptive.resource_mask import ResourceMask, SubcarrierLockType
from VLCL_AI.communication.exceptions import VLCLCommunicationError

class AllocationValidator:
    """
    Validates structural and mathematical invariants of allocation decisions.
    """

    @staticmethod
    def validate_allocation_decision(
        rho: np.ndarray,
        resource_mask: ResourceMask,
        device_ids: List[int],
        strict: bool = True
    ) -> bool:
        """
        Enforces:
        1. rho elements are binary in {0, 1}.
        2. sum_k rho[k, n] <= 1 for all subcarriers n (no carrier collision).
        3. rho[k, n] == 0 for all locked subcarriers (localization, guard, DC, pilots).
        4. Matrix dimensions match len(device_ids) x resource_mask.fft_size.
        """
        rho = np.asarray(rho, dtype=int)
        K, N = rho.shape

        if K != len(device_ids):
            raise VLCLCommunicationError(
                f"Allocation matrix row count K={K} does not match device count {len(device_ids)}."
            )

        if N != resource_mask.fft_size:
            raise VLCLCommunicationError(
                f"Allocation matrix column count N={N} does not match FFT size {resource_mask.fft_size}."
            )

        # 1. Binary check
        if not np.all(np.isin(rho, [0, 1])):
            raise VLCLCommunicationError("Allocation matrix contains non-binary entries.")

        # 2. Exclusive allocation check (sum_k rho[k, n] <= 1)
        col_sums = np.sum(rho, axis=0)
        if np.any(col_sums > 1):
            bad_sc = np.where(col_sums > 1)[0].tolist()
            raise VLCLCommunicationError(
                f"Subcarrier collision detected! Subcarriers {bad_sc} allocated to multiple devices."
            )

        # 3. Locked resource protection check
        for k in range(K):
            for n in range(N):
                if rho[k, n] == 1:
                    lock_type = resource_mask.get_lock_type(n)
                    if lock_type != SubcarrierLockType.AVAILABLE_COMM:
                        raise VLCLCommunicationError(
                            f"Illegal allocation! Subcarrier {n} with lock type {lock_type.value} "
                            f"allocated to device {device_ids[k]}."
                        )

        return True
