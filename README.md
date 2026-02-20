# HF Dataset Viewer

A keyboard-optimized Gradio application for viewing and quizzing on AI2-THOR visual question answering datasets with full session management.

## Features

### Core Features
- **3 HuggingFace datasets** with multiple splits/subsets
- **Quiz mode** with instant feedback and score tracking
- **Session management** - auto-save progress, resume on restart, archive sessions
- **Bookmark questions** for later review
- **Change answers** - update your answer anytime, scores adjust automatically
- **Skip answered questions** - navigation jumps to unanswered rows
- **Progress bar** with real-time accuracy tracking

### Keyboard-Optimized Workflow
No mouse needed for evaluation:

| Key | Action |
|-----|--------|
| `W` / `E` | Previous / Next unanswered row |
| `↑` / `↓` | Previous / Next answered row (review completed) |
| `←` / `→` | Previous / Next gallery image |
| `Q` | First gallery image |
| `1` `2` `3` `4` | Select answer A/B/C/D |
| `Space` | Toggle bookmark |
| `G` | Go to specific row (focus input) |
| `Enter` | Load dataset |
| `N` | New session (archives current) |
| `F` | Finish quiz (show score) |
| `S` | Screenshot to clipboard |
| `Esc` | Exit text input |

### UI Features
- **Large image gallery** (4 columns, 520px height)
- **Bold 3x question text** for readability
- **Sorted choices** in ascending numeric order (for counting questions)
- **Visual answer highlighting** with arrow (→) indicator
- **Screenshot capture** copies entire window to clipboard
- **Compact controls** to maximize image viewing area
- **Session search bar** to load any archived session by ID

## Supported Datasets

### Dataset 1: `weikaih/ai2thor-vsi-eval-400`
- **Splits**: `rotation`, `multi_camera`
- **Main image**: topdown_map
- **Grid images**: frame_* images
- **Answer format**: Single letter (A, B, C, or D)

### Dataset 2: `linjieli222/ai2thor_path_tracing_2point_tifa_filtered_eval`
- **Subsets**: `dh_midpoint`, `td_ego_dir`, `td_ego_dir_arrow`, `td_ego_side`, `td_ego_side_arrow`, `td_midpoint`, `td_path`, `td_path_arrow`
- **Main image**: topdown_image
- **Grid images**: sideview_image + ego_images
- **Answer format**: Full choice text

### Dataset 3: `weikaih/ai2thor-multiview-counting-val-800-v2-400`
- **Splits**: `train` (400 rows)
- **Main image**: topdown_map
- **Grid images**: frame_0 to frame_7
- **Answer format**: Single letter (A, B, C, or D)
- **Special**: Choices sorted in ascending numeric order

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Start the Viewer
```bash
cd /path/to/hf_viewer
python viewer.py
```
Open http://localhost:7860 in your browser.

### Quick Start Workflow
1. Press `Enter` to load the default dataset (Dataset 3)
2. Use `←`/`→` to browse images in current row
3. Press `1-4` to answer
4. Press `E` to go to next unanswered question
5. Press `Space` to bookmark unclear questions
6. Press `F` when done to see your score

### Session Management
- **Auto-save**: Every answer is saved immediately
- **Resume**: Sessions persist across browser refreshes and app restarts
- **New session**: Press `N` to archive current session and start fresh
- **Bookmarks**: Press `Space` to mark questions for review
- **Load old session**: Enter session ID in the search bar to resume any archived session
- **Review answered**: Use `↑`/`↓` arrows to navigate through completed questions

### Load Old Sessions
Use the session search bar in the UI to load any archived session:
1. Enter the session ID (e.g., `20260214_120040`)
2. Click "Load Session" or press Enter
3. The session will load with all previous answers preserved
4. Use `↑`/`↓` arrows to navigate through answered questions

### Analyze Sessions
```bash
# Analyze current session
python analyze_session.py

# List all sessions
python analyze_session.py --list

# Analyze specific session
python analyze_session.py --session <session_id> # E.g 20260214_120040

# Export to CSV
python analyze_session.py --export

# Analyze all archived sessions
python analyze_session.py --all
```


## Performance (WSL Users)

If running on WSL, move the HuggingFace cache to Linux filesystem for better performance:

```bash
# Add to ~/.bashrc
export HF_HOME=~/hf_cache
export HF_DATASETS_CACHE=~/hf_cache/datasets
source ~/.bashrc
```

This prevents Windows processes (Git for Windows) from spawning and consuming memory.

### Pre-download Datasets
```bash
python download_datasets.py
```

## File Structure

```
hf_viewer/
├── viewer.py             # Main Gradio application
├── data_loader.py        # Dataset loading and extraction
├── session_manager.py    # Session save/load/archive
├── analyze_session.py    # Session analysis and reporting
├── eval_dataset3.py      # Claude Opus VQA evaluation
├── download_datasets.py  # Pre-download datasets
├── requirements.txt      # Dependencies
├── sessions/             # Saved sessions (auto-created)
│   ├── current_session.json
│   └── session_*.json    # Archived sessions
└── README.md
```

## Session Data Format

Sessions are saved as JSON with the following structure (no images stored):

```json
{
  "id": "20240215_143022",
  "dataset": "Dataset 3: ai2thor-multiview-counting",
  "split_subset": "train",
  "total_questions": 400,
  "answered_count": 50,
  "correct_count": 45,
  "incorrect_count": 5,
  "bookmarks": [12, 45, 78],
  "answers": {
    "0": {
      "question": "Count the number of...",
      "user_answer": "B",
      "correct_answer": "B",
      "is_correct": true,
      "query_object": "shelvingunit",
      "timestamp": "2024-02-15T14:30:45"
    }
  }
}
```

## Requirements

- Python 3.8+
- gradio
- datasets
- pillow

