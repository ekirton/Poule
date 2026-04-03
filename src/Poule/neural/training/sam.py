"""Sharpness-Aware Minimization (SAM) optimizer wrapper.

SAM seeks parameters in flat loss neighborhoods rather than sharp minima,
improving generalization on class-imbalanced data (Shwartz-Ziv et al., 2023).

Each training step performs two forward-backward passes:
1. Compute gradient, perturb parameters by rho * grad / ||grad||.
2. Compute gradient at perturbed point, apply base optimizer step, restore.
"""

from __future__ import annotations

import torch


class SAM:
    """SAM wrapper around any base optimizer.

    Args:
        params: Model parameters (iterable).
        base_optimizer: Instantiated optimizer (e.g., AdamW).
        rho: Perturbation radius. When 0.0, no perturbation (plain optimizer).
    """

    def __init__(self, params, base_optimizer: torch.optim.Optimizer, rho: float = 0.05):
        self.base_optimizer = base_optimizer
        self.rho = rho
        self.param_groups = base_optimizer.param_groups
        self._params = list(params)
        self._old_params: dict[int, torch.Tensor] = {}

    def first_step(self) -> None:
        """Perturb parameters in the gradient ascent direction."""
        if self.rho == 0.0:
            return

        grad_norm = self._grad_norm()
        scale = self.rho / (grad_norm + 1e-12)

        for p in self._params:
            if p.grad is None:
                continue
            self._old_params[id(p)] = p.data.clone()
            p.data.add_(p.grad, alpha=scale)

    def second_step(self) -> None:
        """Apply base optimizer step using gradient at perturbed point, then restore."""
        if self.rho == 0.0:
            self.base_optimizer.step()
            return

        # Restore original parameters before applying optimizer step
        for p in self._params:
            if id(p) in self._old_params:
                p.data.copy_(self._old_params[id(p)])
        self._old_params.clear()

        self.base_optimizer.step()

    def zero_grad(self) -> None:
        """Zero gradients on the base optimizer."""
        self.base_optimizer.zero_grad()

    def _grad_norm(self) -> torch.Tensor:
        """Compute the L2 norm of all gradients."""
        shared_device = None
        norms = []
        for p in self._params:
            if p.grad is not None:
                shared_device = shared_device or p.grad.device
                norms.append(p.grad.detach().norm(2).to(shared_device))
        if not norms:
            return torch.tensor(0.0)
        return torch.stack(norms).norm(2)
