"""
Gradio application for viewing and quizzing on AI2Thor datasets.
Keyboard-optimized for fast human evaluation with session management.

Keyboard Shortcuts:
  W / E     : Previous / Next unanswered row
  ↑ / ↓     : Previous / Next answered row (review completed)
  ← / →     : Previous / Next gallery image
  Q         : First gallery image
  1/2/3/4   : Select answer A/B/C/D
  Space     : Toggle bookmark
  Enter     : Load dataset
  F         : Finish quiz (show score)
  G         : Focus row number input
  S         : Screenshot to clipboard
  N         : New session
"""

import gradio as gr
from data_loader import (
    load_dataset_1,
    load_dataset_2,
    load_dataset_3,
    get_row_data,
)
from session_manager import (
    load_current_session,
    save_current_session,
    create_empty_session,
    archive_session,
    record_answer,
    record_answer_allow_change,
    toggle_bookmark,
    is_row_answered,
    is_row_bookmarked,
    get_next_unanswered_row,
    get_session_stats,
    delete_current_session,
    load_session_by_id,
    list_archived_sessions,
    get_next_answered_row,
)

# Dataset options
DATASET_1_NAME = "Dataset 1: ai2thor-vsi-eval-400"
DATASET_2_NAME = "Dataset 2: ai2thor_path_tracing"
DATASET_3_NAME = "Dataset 3: ai2thor-multiview-counting"

DATASET_1_SPLITS = ["rotation", "multi_camera"]
DATASET_2_SUBSETS = [
    "dh_midpoint", "td_ego_dir", "td_ego_dir_arrow", "td_ego_side",
    "td_ego_side_arrow", "td_midpoint", "td_path", "td_path_arrow"
]
DATASET_3_SPLITS = ["train"]


def get_split_subset_options(dataset_choice):
    """Return split/subset options based on dataset choice."""
    if dataset_choice == DATASET_1_NAME:
        return gr.Dropdown(choices=DATASET_1_SPLITS, value=DATASET_1_SPLITS[0], label="Split")
    elif dataset_choice == DATASET_2_NAME:
        return gr.Dropdown(choices=DATASET_2_SUBSETS, value=DATASET_2_SUBSETS[0], label="Subset")
    else:
        return gr.Dropdown(choices=DATASET_3_SPLITS, value=DATASET_3_SPLITS[0], label="Split")


def load_data(dataset_choice, split_or_subset_choice):
    """Load the appropriate split/subset based on user selection."""
    if dataset_choice == DATASET_1_NAME:
        split = load_dataset_1(split_or_subset_choice)
        dataset_type = 1
    elif dataset_choice == DATASET_2_NAME:
        split = load_dataset_2(split_or_subset_choice)
        dataset_type = 2
    else:
        split = load_dataset_3(split_or_subset_choice)
        dataset_type = 3
    return split, dataset_type


def format_progress_bar(session):
    """Create a text-based progress bar."""
    if session is None:
        return "No session loaded"

    stats = get_session_stats(session)
    total = stats["total"]
    answered = stats["answered"]
    correct = stats["correct"]
    incorrect = stats["incorrect"]

    if total == 0:
        return "Load a dataset to start"

    progress_pct = stats["progress"]
    accuracy = stats["accuracy"]

    # Create visual progress bar
    bar_width = 30
    filled = int(bar_width * progress_pct / 100)
    bar = "█" * filled + "░" * (bar_width - filled)

    return f"""**Progress:** [{bar}] {answered}/{total} ({progress_pct:.1f}%)
**Score:** ✓ {correct} | ✗ {incorrect} | Accuracy: {accuracy:.1f}%
**Bookmarks:** {stats['bookmarks']}"""


def get_row_status_indicator(session, row_idx):
    """Get status indicator for a row."""
    if session is None:
        return ""

    indicators = []
    if is_row_answered(session, row_idx):
        answer_data = session["answers"].get(str(row_idx), {})
        if answer_data.get("is_correct"):
            indicators.append("✓")
        else:
            indicators.append("✗")

    if is_row_bookmarked(session, row_idx):
        indicators.append("🔖")

    return " ".join(indicators)


# Custom head with keyboard shortcuts
CUSTOM_HEAD = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script>
    function captureScreenshot() {
        html2canvas(document.body, {
            allowTaint: true,
            useCORS: true,
            scrollY: -window.scrollY,
            scrollX: -window.scrollX,
            windowWidth: document.documentElement.scrollWidth,
            windowHeight: document.documentElement.scrollHeight
        }).then(canvas => {
            canvas.toBlob(blob => {
                const item = new ClipboardItem({ 'image/png': blob });
                navigator.clipboard.write([item]).then(() => {
                    showNotification('Screenshot copied!', '#22c55e');
                }).catch(err => {
                    alert('Failed to copy to clipboard');
                });
            });
        });
    }

    function showNotification(msg, color) {
        const n = document.createElement('div');
        n.style.cssText = `position:fixed;top:20px;right:20px;background:${color};color:white;padding:12px 24px;border-radius:8px;z-index:10000;font-weight:600;font-size:16px;`;
        n.textContent = msg;
        document.body.appendChild(n);
        setTimeout(() => n.remove(), 2000);
    }

    // Track current gallery image index
    let currentGalleryIndex = 0;
    let galleryImages = [];

    function updateGallerySelection() {
        galleryImages = document.querySelectorAll('.large-gallery .thumbnail-item, .large-gallery [data-testid="thumbnail"]');
        if (galleryImages.length > 0 && currentGalleryIndex < galleryImages.length) {
            galleryImages[currentGalleryIndex]?.click();
        }
    }

    function getGalleryThumbnails() {
        // Get unique thumbnails - Gradio may have duplicates
        const thumbnails = document.querySelectorAll('.large-gallery .thumbnail-item, .large-gallery [data-testid="thumbnail"], .large-gallery button[class*="thumbnail"]');
        // Filter to unique elements based on their image content
        const seen = new Set();
        const unique = [];
        thumbnails.forEach(t => {
            const img = t.querySelector('img');
            const src = img ? img.src : t.innerHTML;
            if (!seen.has(src)) {
                seen.add(src);
                unique.push(t);
            }
        });
        return unique.length > 0 ? unique : Array.from(thumbnails).slice(0, Math.ceil(thumbnails.length / 2));
    }

    function nextGalleryImage() {
        galleryImages = getGalleryThumbnails();
        if (galleryImages.length > 0) {
            currentGalleryIndex = (currentGalleryIndex + 1) % galleryImages.length;
            galleryImages[currentGalleryIndex]?.click();
            showNotification(`Image ${currentGalleryIndex + 1}/${galleryImages.length}`, '#3b82f6');
        }
    }

    function prevGalleryImage() {
        galleryImages = getGalleryThumbnails();
        if (galleryImages.length > 0) {
            currentGalleryIndex = (currentGalleryIndex - 1 + galleryImages.length) % galleryImages.length;
            galleryImages[currentGalleryIndex]?.click();
            showNotification(`Image ${currentGalleryIndex + 1}/${galleryImages.length}`, '#3b82f6');
        }
    }

    function gotoGalleryImage(idx) {
        galleryImages = getGalleryThumbnails();
        if (idx >= 0 && idx < galleryImages.length) {
            currentGalleryIndex = idx;
            galleryImages[currentGalleryIndex]?.click();
            showNotification(`Image ${currentGalleryIndex + 1}/${galleryImages.length}`, '#3b82f6');
        }
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ignore if typing in input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            if (e.key === 'Escape') {
                e.target.blur();
            }
            return;
        }

        // Arrow keys for gallery image navigation
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            prevGalleryImage();
            return;
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            nextGalleryImage();
            return;
        }
        // Q to go to first image
        else if (e.key === 'q' || e.key === 'Q') {
            e.preventDefault();
            gotoGalleryImage(0);
            return;
        }

        // W/E for row navigation (skip answered)
        if (e.key === 'w' || e.key === 'W') {
            e.preventDefault();
            currentGalleryIndex = 0;
            document.getElementById('prev-btn')?.click();
        } else if (e.key === 'e' || e.key === 'E') {
            e.preventDefault();
            currentGalleryIndex = 0;
            document.getElementById('next-btn')?.click();
        }
        // Up/Down arrows for navigating completed rows
        else if (e.key === 'ArrowUp') {
            e.preventDefault();
            currentGalleryIndex = 0;
            document.getElementById('prev-answered-btn')?.click();
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            currentGalleryIndex = 0;
            document.getElementById('next-answered-btn')?.click();
        }
        // Number keys 1-4 for answers
        else if (e.key === '1') {
            e.preventDefault();
            document.getElementById('choice-a')?.click();
        } else if (e.key === '2') {
            e.preventDefault();
            document.getElementById('choice-b')?.click();
        } else if (e.key === '3') {
            e.preventDefault();
            document.getElementById('choice-c')?.click();
        } else if (e.key === '4') {
            e.preventDefault();
            document.getElementById('choice-d')?.click();
        }
        // F for finish
        else if (e.key === 'f' || e.key === 'F') {
            e.preventDefault();
            document.getElementById('finish-btn')?.click();
        }
        // G for go to row
        else if (e.key === 'g' || e.key === 'G') {
            e.preventDefault();
            const rowInput = document.querySelector('#row-input input');
            if (rowInput) {
                rowInput.focus();
                rowInput.select();
            }
        }
        // Enter for load
        else if (e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('load-btn')?.click();
        }
        // S for screenshot
        else if (e.key === 's' || e.key === 'S') {
            e.preventDefault();
            captureScreenshot();
        }
        // Space for bookmark
        else if (e.key === ' ') {
            e.preventDefault();
            document.getElementById('bookmark-btn')?.click();
        }
        // N for new session
        else if (e.key === 'n' || e.key === 'N') {
            e.preventDefault();
            document.getElementById('new-session-btn')?.click();
        }
    });
</script>
<style>
    #question-display {
        max-height: none !important;
        overflow: visible !important;
        font-size: 1.8em !important;
        line-height: 1.4 !important;
        font-weight: 700 !important;
    }
    #question-display p {
        font-size: 1.8em !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }
    .large-gallery { min-height: 450px !important; }
    .choice-btn { font-size: 1em !important; padding: 8px 12px !important; }
    #main-image img { max-height: 250px !important; object-fit: contain !important; }
    .progress-box {
        background: #f3f4f6;
        padding: 8px 12px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.9em;
    }
    /* Compact buttons */
    button { padding: 6px 12px !important; }
    .compact-row { gap: 4px !important; }
    /* Hide labels where not needed */
    .hide-label label { display: none !important; }
    /* Session label alignment */
    .session-label { display: flex; align-items: center; margin: 0 !important; padding: 0 8px !important; }
    .session-label p { margin: 0 !important; white-space: nowrap; font-size: 0.85em !important; }
    /* Smaller session search input */
    #session-search-input input { font-size: 0.8em !important; padding: 4px 8px !important; height: auto !important; min-height: 0 !important; }
    #session-search-input { min-width: 0 !important; }
</style>
"""

# Build the Gradio interface
with gr.Blocks(title="AI2Thor Dataset Viewer") as demo:

    # State variables
    current_split = gr.State(None)
    current_dataset_type = gr.State(1)
    current_row_idx = gr.State(0)
    current_session = gr.State(None)
    correct_answer_state = gr.State("")

    # Header
    gr.Markdown("""# AI2Thor Dataset Viewer
<small style='color:#666'>**W/E** Rows | **↑/↓** Answered | **←/→** Images | **1-4** Answer | **Space** Bookmark | **G** Go to | **N** New | **F** Finish | **S** Screenshot</small>""")

    # Progress bar at top
    progress_display = gr.Markdown(value="No session loaded", elem_classes=["progress-box"])

    # Controls row
    with gr.Row():
        with gr.Column(scale=2):
            with gr.Row():
                dataset_dropdown = gr.Dropdown(
                    choices=[DATASET_1_NAME, DATASET_2_NAME, DATASET_3_NAME],
                    value=DATASET_3_NAME,
                    label="Dataset",
                    scale=2
                )
                split_subset_dropdown = gr.Dropdown(
                    choices=DATASET_3_SPLITS,
                    value=DATASET_3_SPLITS[0],
                    label="Split/Subset",
                    scale=2
                )
                row_input = gr.Number(
                    value=1,
                    label="Row #",
                    minimum=1,
                    precision=0,
                    scale=1,
                    elem_id="row-input"
                )
                load_btn = gr.Button("Load [Enter]", variant="primary", scale=1, elem_id="load-btn")

        with gr.Column(scale=1):
            with gr.Row():
                prev_btn = gr.Button("W ←", scale=1, elem_id="prev-btn", size="sm")
                next_btn = gr.Button("→ E", scale=1, elem_id="next-btn", size="sm")
            row_info = gr.Textbox(value="", label="", interactive=False, show_label=False)

    # Session controls (compact)
    with gr.Row():
        new_session_btn = gr.Button("New [N]", variant="secondary", elem_id="new-session-btn", scale=1, size="sm")
        bookmark_btn = gr.Button("🔖 [Space]", variant="secondary", elem_id="bookmark-btn", scale=1, size="sm")
        finish_btn = gr.Button("Finish [F]", variant="secondary", elem_id="finish-btn", scale=1, size="sm")
        # Answered row navigation buttons (↑/↓)
        prev_answered_btn = gr.Button("↑ Prev Answered", variant="secondary", elem_id="prev-answered-btn", scale=1, size="sm")
        next_answered_btn = gr.Button("↓ Next Answered", variant="secondary", elem_id="next-answered-btn", scale=1, size="sm")

    # Session search bar (all in one row)
    with gr.Row():
        gr.Markdown("**Load Session:**", elem_classes=["session-label"])
        session_search_input = gr.Textbox(
            placeholder="Session ID (e.g., 20260214_120040)",
            show_label=False,
            scale=2,
            elem_id="session-search-input"
        )
        load_session_btn = gr.Button("Load", variant="secondary", scale=1, size="sm", elem_id="load-session-btn")
        session_search_status = gr.Textbox(value="", show_label=False, interactive=False, scale=2)

    # Main content - images larger, controls compact
    with gr.Row():
        # Left: Large image gallery (bigger)
        with gr.Column(scale=4):
            image_gallery = gr.Gallery(
                label="Frame Images (←/→)",
                columns=4,
                height=520,
                object_fit="contain",
                elem_classes=["large-gallery"]
            )

        # Right: Main image + Question/Answers (compact)
        with gr.Column(scale=2):
            main_image = gr.Image(
                label="Topdown",
                type="pil",
                height=220,
                elem_id="main-image"
            )

            question_text = gr.Markdown(value="", elem_id="question-display")

            with gr.Row():
                choice_btns = []
                for i, label in enumerate(['A', 'B', 'C', 'D']):
                    btn = gr.Button(
                        f"{i+1}:{label}",
                        visible=True,
                        elem_id=f"choice-{label.lower()}",
                        elem_classes=["choice-btn"],
                        size="sm"
                    )
                    choice_btns.append(btn)

            with gr.Row():
                answer_display = gr.Textbox(value="", visible=False, interactive=False, show_label=False)
                correctness_display = gr.HTML(value="", visible=False)

            with gr.Accordion("Metadata", open=False):
                metadata_display = gr.Markdown(value="")

            score_display = gr.Markdown(value="", visible=False)

    loading_status = gr.Markdown(value="", visible=True)

    # Event handlers
    dataset_dropdown.change(
        fn=get_split_subset_options,
        inputs=[dataset_dropdown],
        outputs=[split_subset_dropdown]
    )

    def load_and_display(dataset_choice, split_or_subset, row_num, session):
        """Load dataset and display row, with session management."""
        split, dtype = load_data(dataset_choice, split_or_subset)

        if split is None:
            return (
                split, dtype, 0, session, "",
                None, [], "", "", "",
                gr.update(visible=False), gr.update(visible=False),
                gr.update(value="A."), gr.update(value="B."),
                gr.update(value="C."), gr.update(value="D."),
                "Error loading dataset", 1, "No session"
            )

        total_rows = len(split)

        # Load or create session
        if session is None or session.get("dataset") != dataset_choice or session.get("split_subset") != split_or_subset:
            # Try to load existing session for this dataset/split
            existing = load_current_session()
            if existing and existing.get("dataset") == dataset_choice and existing.get("split_subset") == split_or_subset:
                session = existing
            else:
                # Create new session
                session = create_empty_session(dataset_choice, split_or_subset)
                session["total_questions"] = total_rows
                save_current_session(session)
        else:
            session["total_questions"] = total_rows

        # Get row index
        idx = int(row_num) - 1 if row_num else 0
        idx = max(0, min(idx, total_rows - 1))

        # Update session current row
        session["current_row"] = idx
        save_current_session(session)

        return display_row_data(split, idx, dtype, session)

    def display_row_data(split, idx, dtype, session):
        """Display data for a specific row."""
        if split is None:
            return (
                split, dtype, idx, session, "",
                None, [], "", "", "",
                gr.update(visible=False), gr.update(visible=False),
                gr.update(value="A."), gr.update(value="B."),
                gr.update(value="C."), gr.update(value="D."),
                "", idx + 1, "No session"
            )

        total_rows = len(split)
        row_data = get_row_data(split, idx, dtype)

        main_img = row_data['main_image']
        img_grid = [img for name, img in row_data['grid_images']]
        metadata_dict = row_data['metadata']

        question = metadata_dict.get('question', 'No question available')
        choices_raw = metadata_dict.get('choices', []) or []
        correct_ans = metadata_dict.get('answer', '')

        # Build metadata string
        if dtype == 1:
            metadata = f"""**Scene:** {metadata_dict.get('scene_name', 'N/A')}
**Question Type:** {metadata_dict.get('question_type', 'N/A')}
**Movement Type:** {metadata_dict.get('movement_type', 'N/A')}
**Total Frames:** {metadata_dict.get('total_frames', 'N/A')}"""
        elif dtype == 3:
            metadata = f"""**Scene:** {metadata_dict.get('scene_name', 'N/A')}
**Query Object:** {metadata_dict.get('query_object', 'N/A')}
**Question Type:** {metadata_dict.get('question_type', 'N/A')}
**Movement Type:** {metadata_dict.get('movement_type', 'N/A')}
**Count:** {metadata_dict.get('count', 'N/A')}"""
        else:
            metadata = f"""**Room Type:** {metadata_dict.get('room_type', 'N/A')}
**Variant Type:** {metadata_dict.get('variant_type', 'N/A')}
**Is Egocentric:** {metadata_dict.get('is_egocentric', 'N/A')}"""

        # Row info with status
        status = get_row_status_indicator(session, idx)
        r_info = f"Row {idx + 1} / {total_rows} {status}"

        # Format choices
        choice_labels = ['A', 'B', 'C', 'D']
        btn_updates = []
        for i in range(4):
            if i < len(choices_raw):
                choice_text = choices_raw[i]
                if ')' not in str(choice_text):
                    display_text = f"{choice_labels[i]}) {choice_text}"
                else:
                    display_text = choice_text
                btn_updates.append(gr.update(value=display_text, visible=True, variant="secondary"))
            else:
                btn_updates.append(gr.update(value=f"{choice_labels[i]}.", visible=False, variant="secondary"))

        # Check if already answered
        answer_visible = False
        answer_text = ""
        correctness_html = ""

        if session and is_row_answered(session, idx):
            answer_data = session["answers"].get(str(idx), {})
            answer_visible = True
            answer_text = f"Answer: {correct_ans}"
            if answer_data.get("is_correct"):
                correctness_html = "<span style='color: #22c55e; font-size: 1.5em; font-weight: bold;'>✓ CORRECT</span>"
            else:
                correctness_html = f"<span style='color: #ef4444; font-size: 1.5em; font-weight: bold;'>✗ WRONG (You: {answer_data.get('user_answer')})</span>"

            # Highlight the user's previous answer
            user_ans = answer_data.get("user_answer", "")
            for i in range(len(btn_updates)):
                if i < len(choices_raw):
                    choice_text = choices_raw[i]
                    if ')' not in str(choice_text):
                        display_text = f"{choice_labels[i]}) {choice_text}"
                    else:
                        display_text = choice_text

                    if choice_labels[i] == user_ans:
                        btn_updates[i] = gr.update(value=f"→ {display_text}", visible=True, variant="primary")

        progress = format_progress_bar(session)

        return (
            split, dtype, idx, session, correct_ans,
            main_img, img_grid, question, metadata, r_info,
            gr.update(visible=answer_visible, value=answer_text),
            gr.update(visible=answer_visible, value=correctness_html),
            btn_updates[0], btn_updates[1], btn_updates[2], btn_updates[3],
            "", idx + 1, progress
        )

    def check_answer_and_save(selected_choice, correct_answer, split, row_idx, session, dtype,
                              btn0, btn1, btn2, btn3):
        """Check answer and save to session. Allows changing answers."""
        if not selected_choice or not correct_answer or session is None:
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                session,
                gr.update(), gr.update(), gr.update(), gr.update(),
                format_progress_bar(session)
            )

        all_choices = [btn0, btn1, btn2, btn3]

        # Extract user's answer letter
        user_letter = selected_choice.split(')')[0].strip()
        # Handle both "1:A" format and "→ 1:A" format
        if ':' in user_letter:
            user_letter = user_letter.split(':')[-1].strip()
        if user_letter.startswith("→"):
            user_letter = user_letter[1:].strip()
            if ':' in user_letter:
                user_letter = user_letter.split(':')[-1].strip()

        is_correct = user_letter == correct_answer.strip()

        # Get question text for saving
        row_data = get_row_data(split, row_idx, dtype)
        question = row_data['metadata'].get('question', '')
        query_object = row_data['metadata'].get('query_object', '')

        # Check if already answered (for updating counts correctly)
        row_key = str(row_idx)
        was_answered = row_key in session.get("answers", {})
        previous_correct = False
        if was_answered:
            previous_correct = session["answers"][row_key].get("is_correct", False)

        # Record/update answer in session
        session = record_answer_allow_change(
            session, row_idx, question, user_letter, correct_answer,
            is_correct, query_object, was_answered, previous_correct
        )

        # Prepare display
        answer_text = f"Answer: {correct_answer}"
        if is_correct:
            correctness_msg = "<span style='color: #22c55e; font-size: 1.5em; font-weight: bold;'>✓ CORRECT</span>"
        else:
            correctness_msg = f"<span style='color: #ef4444; font-size: 1.5em; font-weight: bold;'>✗ WRONG</span>"

        # Highlight selected button
        choice_labels = ['A', 'B', 'C', 'D']
        btn_updates = []
        for i, label in enumerate(choice_labels):
            if i < len(all_choices) and all_choices[i]:
                btn_text = all_choices[i]
                # Remove previous arrow if present
                if btn_text.startswith("→ "):
                    btn_text = btn_text[2:]
                # Check if this is the selected choice
                btn_letter = btn_text.split(':')[-1].split(')')[0].strip() if ':' in btn_text else btn_text.split(')')[0].strip()
                if btn_letter == user_letter:
                    btn_updates.append(gr.update(value=f"→ {btn_text}", variant="primary"))
                else:
                    btn_updates.append(gr.update(value=btn_text, variant="secondary"))
            else:
                btn_updates.append(gr.update())

        return (
            gr.update(visible=True, value=answer_text),
            gr.update(visible=True, value=correctness_msg),
            session,
            btn_updates[0], btn_updates[1], btn_updates[2], btn_updates[3],
            format_progress_bar(session)
        )

    def navigate_to_next(split, current_idx, direction, dtype, session):
        """Navigate to next unanswered row."""
        if split is None:
            return display_row_data(None, 0, dtype, session)

        total = len(split)

        # Find next unanswered row
        if session:
            new_idx = get_next_unanswered_row(session, current_idx, total, direction)
        else:
            new_idx = (current_idx + direction) % total

        if session:
            session["current_row"] = new_idx
            save_current_session(session)

        return display_row_data(split, new_idx, dtype, session)

    def goto_row(split, row_num, dtype, session):
        """Go to a specific row."""
        if split is None:
            return display_row_data(None, 0, dtype, session)

        idx = int(row_num) - 1
        idx = max(0, min(idx, len(split) - 1))

        if session:
            session["current_row"] = idx
            save_current_session(session)

        return display_row_data(split, idx, dtype, session)

    def toggle_bookmark_handler(session, row_idx):
        """Toggle bookmark for current row."""
        if session is None:
            return session, format_progress_bar(session), ""

        session = toggle_bookmark(session, row_idx)
        status = get_row_status_indicator(session, row_idx)

        return session, format_progress_bar(session), f"Row {row_idx + 1} {status}"

    def start_new_session(dataset_choice, split_or_subset, session):
        """Archive current session and start a new one."""
        if session and session.get("answered_count", 0) > 0:
            filepath = archive_session(session)
            print(f"Session archived to: {filepath}")

        # Create new session
        new_session = create_empty_session(dataset_choice, split_or_subset)
        save_current_session(new_session)

        return new_session, format_progress_bar(new_session), "New session started"

    def finish_quiz(session):
        """Display final score."""
        if session is None:
            return gr.update(visible=True, value="No session to finish"), session

        stats = get_session_stats(session)

        score_text = f"""## Quiz Complete!

**Answered:** {stats['answered']} / {stats['total']}
**Correct:** {stats['correct']}
**Incorrect:** {stats['incorrect']}
**Accuracy:** {stats['accuracy']:.1f}%
**Bookmarks:** {stats['bookmarks']}

Session saved automatically."""

        # Archive the session
        if stats['answered'] > 0:
            filepath = archive_session(session)
            score_text += f"\n\nArchived to: `{filepath}`"

        return gr.update(visible=True, value=score_text), session

    def load_session_handler(session_id, dataset_dropdown_val, split_dropdown_val):
        """Load an archived session by ID."""
        if not session_id or not session_id.strip():
            return (
                None, 1, 0, None, "",
                None, [], "", "", "",
                gr.update(visible=False), gr.update(visible=False),
                gr.update(value="A."), gr.update(value="B."),
                gr.update(value="C."), gr.update(value="D."),
                "", 1, "No session", "Enter a session ID"
            )

        session_id = session_id.strip()
        loaded_session = load_session_by_id(session_id)

        if loaded_session is None:
            # List available sessions for help
            sessions = list_archived_sessions()
            if sessions:
                available = ", ".join([s["id"] for s in sessions[:5]])
                status_msg = f"Not found. Available: {available}..."
            else:
                status_msg = "Session not found. No archived sessions."
            return (
                None, 1, 0, None, "",
                None, [], "", "", "",
                gr.update(visible=False), gr.update(visible=False),
                gr.update(value="A."), gr.update(value="B."),
                gr.update(value="C."), gr.update(value="D."),
                "", 1, "No session", status_msg
            )

        # Get dataset info from session
        dataset_name = loaded_session.get("dataset", DATASET_3_NAME)
        split_subset = loaded_session.get("split_subset", "train")

        # Load the dataset
        split, dtype = load_data(dataset_name, split_subset)
        if split is None:
            return (
                None, 1, 0, None, "",
                None, [], "", "", "",
                gr.update(visible=False), gr.update(visible=False),
                gr.update(value="A."), gr.update(value="B."),
                gr.update(value="C."), gr.update(value="D."),
                "", 1, "No session", "Error loading dataset"
            )

        # Update session total questions
        loaded_session["total_questions"] = len(split)

        # Set as current session
        save_current_session(loaded_session)

        # Go to first row or current row
        idx = loaded_session.get("current_row", 0)

        # Get display results
        result = display_row_data(split, idx, dtype, loaded_session)

        # Add session ID to status message
        stats = get_session_stats(loaded_session)
        status_msg = f"Loaded: {loaded_session['id']} ({stats['answered']}/{stats['total']} answered)"

        # result has 19 elements, we need to add session_search_status as 20th
        return result + (status_msg,)

    def navigate_to_answered(split, current_idx, direction, dtype, session):
        """Navigate to next/previous answered row."""
        if split is None or session is None:
            return display_row_data(None, 0, dtype, session)

        # Find next answered row
        new_idx = get_next_answered_row(session, current_idx, direction)

        if new_idx is None:
            # No answered rows, stay at current
            new_idx = current_idx

        if session:
            session["current_row"] = new_idx
            save_current_session(session)

        return display_row_data(split, new_idx, dtype, session)

    # Button handlers
    def show_loading():
        return "Loading..."

    load_btn.click(
        fn=show_loading,
        outputs=[loading_status]
    ).then(
        fn=load_and_display,
        inputs=[dataset_dropdown, split_subset_dropdown, row_input, current_session],
        outputs=[
            current_split, current_dataset_type, current_row_idx, current_session, correct_answer_state,
            main_image, image_gallery, question_text, metadata_display, row_info,
            answer_display, correctness_display,
            choice_btns[0], choice_btns[1], choice_btns[2], choice_btns[3],
            loading_status, row_input, progress_display
        ]
    )

    prev_btn.click(
        fn=lambda s, i, d, sess: navigate_to_next(s, i, -1, d, sess),
        inputs=[current_split, current_row_idx, current_dataset_type, current_session],
        outputs=[
            current_split, current_dataset_type, current_row_idx, current_session, correct_answer_state,
            main_image, image_gallery, question_text, metadata_display, row_info,
            answer_display, correctness_display,
            choice_btns[0], choice_btns[1], choice_btns[2], choice_btns[3],
            loading_status, row_input, progress_display
        ]
    )

    next_btn.click(
        fn=lambda s, i, d, sess: navigate_to_next(s, i, 1, d, sess),
        inputs=[current_split, current_row_idx, current_dataset_type, current_session],
        outputs=[
            current_split, current_dataset_type, current_row_idx, current_session, correct_answer_state,
            main_image, image_gallery, question_text, metadata_display, row_info,
            answer_display, correctness_display,
            choice_btns[0], choice_btns[1], choice_btns[2], choice_btns[3],
            loading_status, row_input, progress_display
        ]
    )

    row_input.submit(
        fn=goto_row,
        inputs=[current_split, row_input, current_dataset_type, current_session],
        outputs=[
            current_split, current_dataset_type, current_row_idx, current_session, correct_answer_state,
            main_image, image_gallery, question_text, metadata_display, row_info,
            answer_display, correctness_display,
            choice_btns[0], choice_btns[1], choice_btns[2], choice_btns[3],
            loading_status, row_input, progress_display
        ]
    )

    for btn in choice_btns:
        btn.click(
            fn=check_answer_and_save,
            inputs=[
                btn, correct_answer_state, current_split, current_row_idx, current_session, current_dataset_type,
                choice_btns[0], choice_btns[1], choice_btns[2], choice_btns[3]
            ],
            outputs=[
                answer_display, correctness_display,
                current_session,
                choice_btns[0], choice_btns[1], choice_btns[2], choice_btns[3],
                progress_display
            ]
        )

    bookmark_btn.click(
        fn=toggle_bookmark_handler,
        inputs=[current_session, current_row_idx],
        outputs=[current_session, progress_display, row_info]
    )

    new_session_btn.click(
        fn=start_new_session,
        inputs=[dataset_dropdown, split_subset_dropdown, current_session],
        outputs=[current_session, progress_display, loading_status]
    )

    finish_btn.click(
        fn=finish_quiz,
        inputs=[current_session],
        outputs=[score_display, current_session]
    )

    # Session search handlers
    load_session_btn.click(
        fn=load_session_handler,
        inputs=[session_search_input, dataset_dropdown, split_subset_dropdown],
        outputs=[
            current_split, current_dataset_type, current_row_idx, current_session, correct_answer_state,
            main_image, image_gallery, question_text, metadata_display, row_info,
            answer_display, correctness_display,
            choice_btns[0], choice_btns[1], choice_btns[2], choice_btns[3],
            loading_status, row_input, progress_display, session_search_status
        ]
    )

    session_search_input.submit(
        fn=load_session_handler,
        inputs=[session_search_input, dataset_dropdown, split_subset_dropdown],
        outputs=[
            current_split, current_dataset_type, current_row_idx, current_session, correct_answer_state,
            main_image, image_gallery, question_text, metadata_display, row_info,
            answer_display, correctness_display,
            choice_btns[0], choice_btns[1], choice_btns[2], choice_btns[3],
            loading_status, row_input, progress_display, session_search_status
        ]
    )

    # Answered row navigation handlers (up/down arrows)
    prev_answered_btn.click(
        fn=lambda s, i, d, sess: navigate_to_answered(s, i, -1, d, sess),
        inputs=[current_split, current_row_idx, current_dataset_type, current_session],
        outputs=[
            current_split, current_dataset_type, current_row_idx, current_session, correct_answer_state,
            main_image, image_gallery, question_text, metadata_display, row_info,
            answer_display, correctness_display,
            choice_btns[0], choice_btns[1], choice_btns[2], choice_btns[3],
            loading_status, row_input, progress_display
        ]
    )

    next_answered_btn.click(
        fn=lambda s, i, d, sess: navigate_to_answered(s, i, 1, d, sess),
        inputs=[current_split, current_row_idx, current_dataset_type, current_session],
        outputs=[
            current_split, current_dataset_type, current_row_idx, current_session, correct_answer_state,
            main_image, image_gallery, question_text, metadata_display, row_info,
            answer_display, correctness_display,
            choice_btns[0], choice_btns[1], choice_btns[2], choice_btns[3],
            loading_status, row_input, progress_display
        ]
    )


if __name__ == "__main__":
    demo.launch(head=CUSTOM_HEAD)
