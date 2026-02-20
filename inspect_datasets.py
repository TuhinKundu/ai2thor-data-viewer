from datasets import load_dataset
import json

print("=" * 80)
print("DATASET 1: weikaih/ai2thor-vsi-eval-400")
print("=" * 80)

# Load dataset 1
ds1 = load_dataset("weikaih/ai2thor-vsi-eval-400", cache_dir="./cache")

# Inspect splits
print("\nSplits:", list(ds1.keys()))

for split_name in ds1.keys():
    print(f"\n--- Split: {split_name} ---")
    split = ds1[split_name]
    print(f"Number of rows: {len(split)}")
    print(f"Features: {list(split.features.keys())}")

    # Inspect first row
    if len(split) > 0:
        first_row = split[0]
        print(f"\nFirst row sample:")

        # Count frame images
        frame_images = [k for k in first_row.keys() if k.startswith('frame_')]
        print(f"  Frame images: {frame_images}")

        # Check other fields
        print(f"  Question: {first_row.get('question', 'N/A')[:100]}...")
        print(f"  Answer: {first_row.get('answer', 'N/A')}")
        print(f"  Choices: {first_row.get('choices', 'N/A')}")
        print(f"  Scene: {first_row.get('scene_name', 'N/A')}")
        print(f"  Question type: {first_row.get('question_type', 'N/A')}")
        print(f"  Movement type: {first_row.get('movement_type', 'N/A')}")
        print(f"  Total frames: {first_row.get('total_frames', 'N/A')}")
        print(f"  Has topdown_map: {'topdown_map' in first_row}")

        # Check metadata structure
        if 'metadata' in first_row:
            print(f"  Metadata keys: {list(first_row['metadata'].keys()) if isinstance(first_row['metadata'], dict) else 'Not a dict'}")

print("\n" + "=" * 80)
print("DATASET 2: linjieli222/ai2thor_path_tracing_2point_tifa_filtered_eval")
print("=" * 80)

# Load all configurations of dataset 2
configs = ["dh_midpoint", "td_ego_dir", "td_ego_dir_arrow", "td_ego_side",
           "td_ego_side_arrow", "td_midpoint", "td_path", "td_path_arrow"]

for config in configs:
    print(f"\n--- Configuration: {config} ---")
    try:
        ds2 = load_dataset("linjieli222/ai2thor_path_tracing_2point_tifa_filtered_eval",
                          name=config, cache_dir="./cache")

        # Inspect splits
        print(f"Splits: {list(ds2.keys())}")

        for split_name in ds2.keys():
            split = ds2[split_name]
            print(f"  {split_name} - Number of rows: {len(split)}")
            print(f"  Features: {list(split.features.keys())}")

            # Inspect first row
            if len(split) > 0:
                first_row = split[0]
                print(f"\n  First row sample:")

                # Check image fields
                print(f"    Has topdown_image: {'topdown_image' in first_row}")
                print(f"    Has sideview_image: {'sideview_image' in first_row}")

                # Check ego_images
                if 'ego_images' in first_row:
                    ego_imgs = first_row['ego_images']
                    if ego_imgs is not None:
                        if isinstance(ego_imgs, list):
                            print(f"    ego_images count: {len(ego_imgs)}")
                        else:
                            print(f"    ego_images type: {type(ego_imgs)}")
                    else:
                        print(f"    ego_images: None")
                else:
                    print(f"    Has ego_images: False")

                print(f"    Question: {first_row.get('question', 'N/A')[:100]}...")
                print(f"    Answer: {first_row.get('answer', 'N/A')}")
                print(f"    Choices: {first_row.get('choices', 'N/A')}")
                print(f"    Room type: {first_row.get('room_type', 'N/A')}")
                print(f"    Variant type: {first_row.get('variant_type', 'N/A')}")
                print(f"    Is egocentric: {first_row.get('is_egocentric', 'N/A')}")

    except Exception as e:
        print(f"  Error loading config {config}: {e}")

print("\n" + "=" * 80)
print("INSPECTION COMPLETE")
print("=" * 80)
