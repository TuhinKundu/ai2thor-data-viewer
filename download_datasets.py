"""
Pre-download script for HuggingFace datasets.

Run this script once to download all datasets to cache.
This will make the viewer load much faster on first use.
"""

from datasets import load_dataset

CACHE_DIR = "./cache"

print("=" * 80)
print("Pre-downloading HuggingFace Datasets")
print("=" * 80)
print("\nThis will download ~10-15GB of data (depends on dataset sizes).")
print("It may take several minutes depending on your internet speed.\n")

# Dataset 1: ai2thor-vsi-eval-400
print("\n[1/4] Downloading Dataset 1: ai2thor-vsi-eval-400")
print("-" * 80)
try:
    print("  Loading 'rotation' split...")
    ds1_rotation = load_dataset(
        "weikaih/ai2thor-vsi-eval-400",
        split="rotation",
        cache_dir=CACHE_DIR
    )
    print(f"  ✓ Rotation split loaded ({len(ds1_rotation)} rows)")

    print("  Loading 'multi_camera' split...")
    ds1_multi = load_dataset(
        "weikaih/ai2thor-vsi-eval-400",
        split="multi_camera",
        cache_dir=CACHE_DIR
    )
    print(f"  ✓ Multi-camera split loaded ({len(ds1_multi)} rows)")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Dataset 2: ai2thor_path_tracing (8 subsets)
print("\n[2/4] Downloading Dataset 2: ai2thor_path_tracing (8 subsets)")
print("-" * 80)

subsets = [
    "dh_midpoint",
    "td_ego_dir",
    "td_ego_dir_arrow",
    "td_ego_side",
    "td_ego_side_arrow",
    "td_midpoint",
    "td_path",
    "td_path_arrow",
]

for i, subset in enumerate(subsets, 1):
    try:
        print(f"  [{i}/8] Loading subset: {subset}...")
        ds = load_dataset(
            "linjieli222/ai2thor_path_tracing_2point_tifa_filtered_eval",
            name=subset,
            split="val",
            cache_dir=CACHE_DIR
        )
        print(f"       ✓ Loaded ({len(ds)} rows)")
    except Exception as e:
        print(f"       ✗ Error: {e}")

# Dataset 3: ai2thor-multiview-counting
print("\n[3/4] Downloading Dataset 3: ai2thor-multiview-counting-val-800-v2-400")
print("-" * 80)
try:
    print("  Loading 'train' split...")
    ds3_train = load_dataset(
        "weikaih/ai2thor-multiview-counting-val-800-v2-400",
        split="train",
        cache_dir=CACHE_DIR
    )
    print(f"  ✓ Train split loaded ({len(ds3_train)} rows)")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "=" * 80)
print("Download Complete!")
print("=" * 80)
print("\nAll datasets have been cached in ./cache/")
print("You can now run 'python viewer.py' for fast loading.\n")
