def define_targets(rules):
    rules.cc_test(
        name = "test",
        srcs = [
            "impl/CUDATest.cpp",
            "impl/CUDAAssertionsTest_1_var_test.cu",
            "impl/CUDAAssertionsTest_catches_stream.cu",
            "impl/CUDAAssertionsTest_catches_thread_and_block_and_device.cu",
            "impl/CUDAAssertionsTest_from_2_processes.cu",
            "impl/CUDAAssertionsTest_multiple_writes_from_blocks_and_threads.cu",
            "impl/CUDAAssertionsTest_multiple_writes_from_multiple_blocks.cu",
            "impl/CUDAAssertionsTest_multiple_writes_from_same_block.cu",
        ],
        deps = [
            "@com_google_googletest//:gtest_main",
            "//c10/cuda",
        ],
        target_compatible_with = rules.requires_cuda_enabled(),
    )
