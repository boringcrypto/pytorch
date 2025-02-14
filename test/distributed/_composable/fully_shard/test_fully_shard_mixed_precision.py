# Owner(s): ["oncall: distributed"]

import sys
from typing import Dict

import torch
import torch.distributed as dist
import torch.nn as nn
from torch.distributed._composable import fully_shard
from torch.distributed.fsdp import MixedPrecision
from torch.testing._internal.common_distributed import (
    SaveForwardInputsModel,
    skip_if_lt_x_gpu,
)
from torch.testing._internal.common_fsdp import FSDPTest
from torch.testing._internal.common_utils import run_tests, TEST_WITH_DEV_DBG_ASAN


if not dist.is_available():
    print("Distributed not available, skipping tests", file=sys.stderr)
    sys.exit(0)

if TEST_WITH_DEV_DBG_ASAN:
    print(
        "Skip dev-asan as torch + multiprocessing spawn have known issues",
        file=sys.stderr,
    )
    sys.exit(0)


class TestMixedPrecision(FSDPTest):
    """Tests ``fully_shard`` with mixed precision."""

    @property
    def world_size(self):
        return 2

    @skip_if_lt_x_gpu(2)
    def test_float16_on_one_submodule(self):
        self.run_subtests(
            {
                "cast_root_forward_inputs_submodule": [True, False],
                "cast_forward_inputs_submodule": [True, False],
            },
            self._test_float16_on_one_submodule,
        )

    def _test_float16_on_one_submodule(
        self,
        cast_root_forward_inputs_submodule: bool,
        cast_forward_inputs_submodule: bool,
    ):
        forward_inputs: Dict[nn.Module, torch.Tensor] = {}
        float16 = MixedPrecision(
            param_dtype=torch.float16,
            cast_root_forward_inputs=cast_root_forward_inputs_submodule,
            cast_forward_inputs=cast_forward_inputs_submodule,
        )

        model = SaveForwardInputsModel(
            forward_inputs=forward_inputs,
            cast_forward_inputs=False,
        ).cuda()
        c1, c2 = model.c1, model.c2
        x = torch.zeros(2, 100, device="cuda")

        # float16 on one submodule and float32 on everything else
        model.c2 = fully_shard(model.c2, mixed_precision=float16)
        fsdp = fully_shard(model)

        # cast_root_forward_inputs_submodule or cast_forward_inputs_submodule should be True
        if not cast_root_forward_inputs_submodule and not cast_forward_inputs_submodule:
            with self.assertRaisesRegex(
                RuntimeError,
                "mat1 and mat2 must have the same dtype",
            ):
                fsdp(x).sum().backward()
        else:
            fsdp(x).sum().backward()

        self.assertEqual(forward_inputs[model].dtype, torch.float32)
        self.assertEqual(forward_inputs[c1].dtype, torch.float32)
        if cast_root_forward_inputs_submodule or cast_forward_inputs_submodule:
            self.assertEqual(forward_inputs[c2].dtype, torch.float16)
        else:
            self.assertEqual(forward_inputs[c2].dtype, torch.float32)


if __name__ == "__main__":
    run_tests()
