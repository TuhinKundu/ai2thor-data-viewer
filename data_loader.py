"""
Dataset loading logic for HuggingFace dataset viewer.

Supports two datasets:
1. weikaih/ai2thor-vsi-eval-400 (splits: rotation, multi_camera)
2. linjieli222/ai2thor_path_tracing_2point_tifa_filtered_eval (8 subsets, val split)
"""

from datasets import load_dataset
from PIL import Image
from typing import Dict, List, Optional, Any, Tuple, Union

# Cache directory for HuggingFace datasets
CACHE_DIR = "./cache"

# Dataset identifiers
DATASET_1_ID = "weikaih/ai2thor-vsi-eval-400"
DATASET_2_ID = "linjieli222/ai2thor_path_tracing_2point_tifa_filtered_eval"
DATASET_3_ID = "weikaih/ai2thor-multiview-counting-val-800-v2-400"

# Available splits/subsets
DATASET_1_SPLITS = ["rotation", "multi_camera"]
DATASET_2_SUBSETS = [
    "dh_midpoint",
    "td_ego_dir",
    "td_ego_dir_arrow",
    "td_ego_side",
    "td_ego_side_arrow",
    "td_midpoint",
    "td_path",
    "td_path_arrow",
]
DATASET_3_SPLITS = ["train"]

# Metadata fields for each dataset
DATASET_1_METADATA_FIELDS = [
    "question",
    "answer",
    "choices",
    "scene_name",
    "question_type",
    "movement_type",
    "total_frames",
]

DATASET_2_METADATA_FIELDS = [
    "question",
    "answer",
    "choices",
    "room_type",
    "variant_type",
    "is_egocentric",
]

DATASET_3_METADATA_FIELDS = [
    "question",
    "answer",
    "query_object",
    "scene_name",
    "question_type",
    "movement_type",
    "count",
]


def load_dataset_1(split_name: str):
    """
    Load the ai2thor-vsi-eval-400 dataset with a specific split.

    Args:
        split_name: Either "rotation" or "multi_camera"

    Returns:
        The dataset split as a HuggingFace Dataset object

    Raises:
        ValueError: If split_name is not valid
    """
    if split_name not in DATASET_1_SPLITS:
        raise ValueError(
            f"Invalid split '{split_name}'. Must be one of: {DATASET_1_SPLITS}"
        )

    print(f"Loading Dataset 1 - Split: {split_name}...")
    # Load only the specific split directly (faster than loading all splits)
    dataset = load_dataset(
        DATASET_1_ID,
        split=split_name,
        cache_dir=CACHE_DIR,
        keep_in_memory=False
    )
    print(f"✓ Loaded {len(dataset)} rows")
    return dataset


def load_dataset_2(subset_name: str):
    """
    Load the ai2thor_path_tracing dataset with a specific subset.
    Always accesses the "val" split.

    Args:
        subset_name: One of the 8 available subsets

    Returns:
        The validation split of the specified subset

    Raises:
        ValueError: If subset_name is not valid
    """
    if subset_name not in DATASET_2_SUBSETS:
        raise ValueError(
            f"Invalid subset '{subset_name}'. Must be one of: {DATASET_2_SUBSETS}"
        )

    print(f"Loading Dataset 2 - Subset: {subset_name}...")
    # Load only the val split directly
    dataset = load_dataset(
        DATASET_2_ID,
        name=subset_name,
        split="val",
        cache_dir=CACHE_DIR,
        keep_in_memory=False
    )
    print(f"✓ Loaded {len(dataset)} rows")
    return dataset


def load_dataset_3(split_name: str):
    """
    Load the ai2thor-multiview-counting-val-800-v2-400 dataset with a specific split.

    Args:
        split_name: Either "rotation" or "multi_camera"

    Returns:
        The dataset split as a HuggingFace Dataset object

    Raises:
        ValueError: If split_name is not valid
    """
    if split_name not in DATASET_3_SPLITS:
        raise ValueError(
            f"Invalid split '{split_name}'. Must be one of: {DATASET_3_SPLITS}"
        )

    print(f"Loading Dataset 3 - Split: {split_name}...")
    # Load only the specific split directly
    dataset = load_dataset(
        DATASET_3_ID,
        split=split_name,
        cache_dir=CACHE_DIR,
        keep_in_memory=False
    )
    print(f"✓ Loaded {len(dataset)} rows")
    return dataset


def extract_frame_images(row: Dict[str, Any]) -> List[Tuple[str, Image.Image]]:
    """
    Extract all frame_* images from a Dataset 1 row.

    Args:
        row: A single row from Dataset 1

    Returns:
        List of tuples (frame_name, PIL.Image) sorted by frame name
    """
    frame_images = []

    for key in row.keys():
        if key.startswith("frame_"):
            value = row[key]
            if value is not None:
                # Handle both PIL Image and dict format from HF datasets
                if isinstance(value, Image.Image):
                    frame_images.append((key, value))
                elif isinstance(value, dict) and "bytes" in value:
                    # Convert bytes to PIL Image
                    import io
                    img = Image.open(io.BytesIO(value["bytes"]))
                    frame_images.append((key, img))
                elif isinstance(value, dict) and "path" in value:
                    # Load from path
                    img = Image.open(value["path"])
                    frame_images.append((key, img))

    # Sort by frame name to maintain consistent order
    frame_images.sort(key=lambda x: x[0])

    return frame_images


def extract_images_dataset2(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract topdown_image, sideview_image, and ego_images from a Dataset 2 row.

    Args:
        row: A single row from Dataset 2

    Returns:
        Dictionary with:
            - "topdown_image": PIL.Image (main image)
            - "sideview_image": PIL.Image or None
            - "ego_images": List of PIL.Image or empty list
    """
    def ensure_pil_image(value) -> Optional[Image.Image]:
        """Convert various image formats to PIL Image."""
        if value is None:
            return None
        if isinstance(value, Image.Image):
            return value
        if isinstance(value, dict):
            if "bytes" in value and value["bytes"] is not None:
                import io
                return Image.open(io.BytesIO(value["bytes"]))
            elif "path" in value and value["path"] is not None:
                return Image.open(value["path"])
        return None

    result = {
        "topdown_image": ensure_pil_image(row.get("topdown_image")),
        "sideview_image": ensure_pil_image(row.get("sideview_image")),
        "ego_images": [],
    }

    # Handle ego_images - can be a list or None
    ego_images_raw = row.get("ego_images")
    if ego_images_raw is not None:
        if isinstance(ego_images_raw, list):
            for img in ego_images_raw:
                pil_img = ensure_pil_image(img)
                if pil_img is not None:
                    result["ego_images"].append(pil_img)
        else:
            # Single image case
            pil_img = ensure_pil_image(ego_images_raw)
            if pil_img is not None:
                result["ego_images"].append(pil_img)

    return result


def get_row_data(
    dataset, idx: int, dataset_type: int
) -> Dict[str, Any]:
    """
    Extract a single row with all images and metadata.

    Args:
        dataset: The loaded HuggingFace dataset (split or subset)
        idx: Row index
        dataset_type: 1 for Dataset 1, 2 for Dataset 2, 3 for Dataset 3

    Returns:
        Dictionary containing:
            - "main_image": PIL.Image (topdown_map or topdown_image)
            - "grid_images": List of (name, PIL.Image) tuples
            - "metadata": Dict of metadata fields
            - "idx": The row index
            - "total_rows": Total number of rows in dataset

    Raises:
        IndexError: If idx is out of range
        ValueError: If dataset_type is invalid
    """
    if dataset_type not in [1, 2, 3]:
        raise ValueError(f"Invalid dataset_type: {dataset_type}. Must be 1, 2, or 3.")

    total_rows = len(dataset)
    if idx < 0 or idx >= total_rows:
        raise IndexError(f"Index {idx} out of range. Dataset has {total_rows} rows.")

    row = dataset[idx]

    if dataset_type == 1:
        return _get_row_data_dataset1(row, idx, total_rows)
    elif dataset_type == 2:
        return _get_row_data_dataset2(row, idx, total_rows)
    else:  # dataset_type == 3
        return _get_row_data_dataset3(row, idx, total_rows)


def _get_row_data_dataset1(
    row: Dict[str, Any], idx: int, total_rows: int
) -> Dict[str, Any]:
    """Extract data from a Dataset 1 row."""

    def ensure_pil_image(value) -> Optional[Image.Image]:
        """Convert various image formats to PIL Image."""
        if value is None:
            return None
        if isinstance(value, Image.Image):
            return value
        if isinstance(value, dict):
            if "bytes" in value and value["bytes"] is not None:
                import io
                return Image.open(io.BytesIO(value["bytes"]))
            elif "path" in value and value["path"] is not None:
                return Image.open(value["path"])
        return None

    # Extract main image (topdown_map)
    main_image = ensure_pil_image(row.get("topdown_map"))

    # Extract frame images for the grid
    frame_images = extract_frame_images(row)

    # Extract metadata
    metadata = {}
    for field in DATASET_1_METADATA_FIELDS:
        metadata[field] = row.get(field)

    return {
        "main_image": main_image,
        "grid_images": frame_images,
        "metadata": metadata,
        "idx": idx,
        "total_rows": total_rows,
    }


def _get_row_data_dataset2(
    row: Dict[str, Any], idx: int, total_rows: int
) -> Dict[str, Any]:
    """Extract data from a Dataset 2 row."""

    # Extract images
    images = extract_images_dataset2(row)

    # Build grid images: [sideview_image] + ego_images
    grid_images = []

    if images["sideview_image"] is not None:
        grid_images.append(("sideview_image", images["sideview_image"]))

    for i, ego_img in enumerate(images["ego_images"]):
        grid_images.append((f"ego_image_{i}", ego_img))

    # Extract metadata
    metadata = {}
    for field in DATASET_2_METADATA_FIELDS:
        metadata[field] = row.get(field)

    return {
        "main_image": images["topdown_image"],
        "grid_images": grid_images,
        "metadata": metadata,
        "idx": idx,
        "total_rows": total_rows,
    }


def _get_row_data_dataset3(
    row: Dict[str, Any], idx: int, total_rows: int
) -> Dict[str, Any]:
    """Extract data from a Dataset 3 row."""
    import re

    def ensure_pil_image(value) -> Optional[Image.Image]:
        """Convert various image formats to PIL Image."""
        if value is None:
            return None
        if isinstance(value, Image.Image):
            return value
        if isinstance(value, dict):
            if "bytes" in value and value["bytes"] is not None:
                import io
                return Image.open(io.BytesIO(value["bytes"]))
            elif "path" in value and value["path"] is not None:
                return Image.open(value["path"])
        return None

    # Extract main image (topdown_map)
    main_image = ensure_pil_image(row.get("topdown_map"))

    # Extract frame images for the grid
    frame_images = extract_frame_images(row)

    # Extract metadata
    metadata = {}
    for field in DATASET_3_METADATA_FIELDS:
        metadata[field] = row.get(field)

    # Dataset 3 has choices embedded in the question text
    # Parse them out: "Question text\nA) choice1\nB) choice2..."
    question_text = row.get("question", "")
    choices = []
    original_answer = row.get("answer", "").strip().upper()

    # Split question and choices
    lines = question_text.split('\n')
    clean_question_lines = []
    for line in lines:
        # Check if line starts with A), B), C), D)
        if re.match(r'^[A-D]\)', line.strip()):
            choices.append(line.strip())
        else:
            clean_question_lines.append(line)

    metadata["question"] = '\n'.join(clean_question_lines).strip()

    # Sort choices by numeric value (ascending) and remap answer
    def extract_number(choice):
        """Extract numeric value from choice like 'A) 2' -> 2"""
        match = re.search(r'\)\s*(\d+)', choice)
        if match:
            return int(match.group(1))
        return 0

    # Parse choices into (original_letter, number, text)
    parsed_choices = []
    for choice in choices:
        letter = choice[0]  # A, B, C, D
        number = extract_number(choice)
        text = re.sub(r'^[A-D]\)\s*', '', choice)  # Remove letter prefix
        parsed_choices.append((letter, number, text))

    # Sort by numeric value (ascending)
    sorted_choices = sorted(parsed_choices, key=lambda x: x[1])

    # Create new choices with A, B, C, D labels and find new answer
    new_labels = ['A', 'B', 'C', 'D']
    new_choices = []
    new_answer = original_answer

    for i, (orig_letter, number, text) in enumerate(sorted_choices):
        if i < len(new_labels):
            new_choices.append(f"{new_labels[i]}) {text}")
            # If this was the original correct answer, update to new label
            if orig_letter == original_answer:
                new_answer = new_labels[i]

    metadata["choices"] = new_choices
    metadata["answer"] = new_answer

    return {
        "main_image": main_image,
        "grid_images": frame_images,
        "metadata": metadata,
        "idx": idx,
        "total_rows": total_rows,
    }


def get_dataset_info(dataset_type: int) -> Dict[str, Any]:
    """
    Get information about a dataset type.

    Args:
        dataset_type: 1, 2, or 3

    Returns:
        Dictionary with dataset information including:
            - "id": Dataset identifier
            - "splits" or "subsets": Available splits/subsets
            - "metadata_fields": List of metadata field names
            - "main_image_field": Name of the main image field
    """
    if dataset_type == 1:
        return {
            "id": DATASET_1_ID,
            "splits": DATASET_1_SPLITS,
            "metadata_fields": DATASET_1_METADATA_FIELDS,
            "main_image_field": "topdown_map",
            "grid_description": "frame_* images",
        }
    elif dataset_type == 2:
        return {
            "id": DATASET_2_ID,
            "subsets": DATASET_2_SUBSETS,
            "metadata_fields": DATASET_2_METADATA_FIELDS,
            "main_image_field": "topdown_image",
            "grid_description": "sideview_image + ego_images",
        }
    elif dataset_type == 3:
        return {
            "id": DATASET_3_ID,
            "splits": DATASET_3_SPLITS,
            "metadata_fields": DATASET_3_METADATA_FIELDS,
            "main_image_field": "topdown_map",
            "grid_description": "frame_* images",
        }
    else:
        raise ValueError(f"Invalid dataset_type: {dataset_type}. Must be 1, 2, or 3.")
