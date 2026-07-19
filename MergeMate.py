"""
MergeMate — File Merger Tool
Merge multiple text/code files into one organized document.
"""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

import chardet
import streamlit as st

# ─── Constants ───────────────────────────────────────────────────────────────

__version__ = "1.1.0"

# Single source of truth for supported text file extensions
TEXT_EXTENSIONS: frozenset[str] = frozenset({
    ".txt", ".xml", ".java", ".py", ".js", ".html", ".css", ".json",
    ".md", ".yml", ".yaml", ".ini", ".cfg", ".conf", ".log", ".sql",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".rb", ".go", ".rs",
    ".sh", ".bat", ".ps1", ".r", ".scala", ".kt", ".swift", ".dart",
    ".tsx", ".jsx", ".vue", ".svelte", ".ts", ".coffee", ".less",
    ".scss", ".sass", ".styl", ".pug", ".ejs", ".hbs", ".mustache",
    ".toml", ".env", ".gitignore", ".dockerfile",
})

# Streamlit file_uploader expects extensions WITHOUT the leading dot
UPLOAD_EXTENSIONS: list[str] = [ext.lstrip(".") for ext in sorted(TEXT_EXTENSIONS)]

DEFAULT_SEPARATOR = "\n" + "=" * 80 + "\n"

# How many bytes to sample for encoding detection (64 KB is enough for chardet)
ENCODING_SAMPLE_BYTES = 65_536

# ─── Core Utilities ──────────────────────────────────────────────────────────


def detect_encoding(file_path: str) -> str:
    """
    Detect the encoding of a file by sampling up to ENCODING_SAMPLE_BYTES.
    Falls back to 'utf-8' on any error.
    """
    try:
        with open(file_path, "rb") as fh:
            raw = fh.read(ENCODING_SAMPLE_BYTES)
        result = chardet.detect(raw)
        return result.get("encoding") or "utf-8"
    except (OSError, IOError):
        return "utf-8"


def read_file_content(file_path: str) -> Tuple[str, bool]:
    """
    Read file content with encoding detection.
    Returns (content, success).  On failure, content is a human-readable
    error message so the caller can embed it in the merged output.
    """
    try:
        encoding = detect_encoding(file_path)
        with open(file_path, encoding=encoding) as fh:
            return fh.read(), True
    except UnicodeDecodeError:
        try:
            with open(file_path, encoding="utf-8", errors="replace") as fh:
                return fh.read(), True
        except Exception as exc:  # noqa: BLE001
            return f"[Error: Could not read file — {exc}]", False
    except Exception as exc:  # noqa: BLE001
        return f"[Error reading {file_path}: {exc}]", False


def is_text_file(file_path: str) -> bool:
    """Return True if *file_path* has a recognised text-based extension."""
    return Path(file_path).suffix.lower() in TEXT_EXTENSIONS


def sanitize_filename(name: str) -> str:
    """
    Strip path-traversal characters and control characters from a filename.
    Ensures the result is a plain filename (no directory components).
    """
    # Take only the final component (no slashes / backslashes)
    name = os.path.basename(name)
    # Remove null bytes and other control characters
    name = "".join(ch for ch in name if ch.isprintable() and ch not in r'\/:*?"<>|')
    return name.strip() or "merged_files.txt"


# ─── File Operations ─────────────────────────────────────────────────────────


def merge_files(file_paths: List[str], separator: str = DEFAULT_SEPARATOR) -> str:
    """Merge multiple files into one string with filename headers."""
    parts: list[str] = []
    last_index = len(file_paths) - 1

    for i, file_path in enumerate(file_paths):
        filename = os.path.basename(file_path)
        header = f"\n{filename}:\n{'-' * (len(filename) + 1)}\n"
        parts.append(header)

        content, _ok = read_file_content(file_path)
        parts.append(content)

        if i < last_index:
            parts.append(separator)

    return "".join(parts)


def save_merged_file(content: str, output_filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Save merged content to a temp file.
    Returns (file_path, None) on success or (None, error_message) on failure.
    Caller is responsible for displaying any error.
    """
    output_path = os.path.join(tempfile.gettempdir(), output_filename)
    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return output_path, None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def extract_zip_files(zip_file_obj) -> Tuple[List[str], Optional[str]]:
    """
    Extract text files from an uploaded ZIP archive.

    Returns (file_paths, error_message).
    Includes Zip Slip protection: any entry whose resolved path escapes
    the temp directory is silently skipped.
    """
    temp_dir = tempfile.mkdtemp()
    file_paths: list[str] = []

    try:
        with zipfile.ZipFile(zip_file_obj) as zf:
            # ── Zip Slip protection ──────────────────────────────────────
            real_temp = os.path.realpath(temp_dir)
            safe_members: list[str] = []
            for member in zf.namelist():
                target = os.path.realpath(os.path.join(real_temp, member))
                if target.startswith(real_temp + os.sep) or target == real_temp:
                    safe_members.append(member)

            zf.extractall(temp_dir, members=safe_members)

        for root, _dirs, files in os.walk(temp_dir):
            for fname in files:
                full_path = os.path.join(root, fname)
                if is_text_file(full_path):
                    file_paths.append(full_path)

        # Store the temp_dir so the caller can clean it up later
        return sorted(file_paths), None

    except zipfile.BadZipFile:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return [], "The uploaded file is not a valid ZIP archive."
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(temp_dir, ignore_errors=True)
        return [], str(exc)


# ─── Session-State Helpers ───────────────────────────────────────────────────


def _cleanup_temp_files(paths: List[str]) -> None:
    """Remove a list of temp file paths, ignoring any errors."""
    for p in paths:
        try:
            if os.path.isfile(p):
                os.remove(p)
            elif os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
        except OSError:
            pass


def _init_session_state() -> None:
    """Ensure all required session-state keys exist."""
    defaults = {
        "temp_individual_files": [],   # paths written for individual uploads
        "zip_temp_dir": None,          # temp dir created for ZIP extraction
        "zip_file_paths": [],          # extracted paths from last ZIP
        "zip_excluded": set(),         # basenames the user has excluded
        "last_upload_method": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─── Main Application ─────────────────────────────────────────────────────────


def _render_sidebar() -> Tuple[str, str]:
    """Render the sidebar options and return (output_filename, separator)."""
    with st.sidebar:
        st.header("⚙️ Options")
        st.markdown("---")

        output_filename = st.text_input(
            "Output filename",
            value="merged_files.txt",
            help="Name for the merged output file",
        )
        output_filename = sanitize_filename(output_filename)
        # Ensure there's at least some extension
        if not Path(output_filename).suffix:
            output_filename += ".txt"
        st.caption(f"Will save as: `{output_filename}`")

        st.markdown("---")
        use_custom_sep = st.checkbox("Use custom separator")
        if use_custom_sep:
            separator = st.text_area(
                "Custom separator",
                value=DEFAULT_SEPARATOR,
                height=80,
                help="Text inserted between each file in the output",
            )
        else:
            separator = DEFAULT_SEPARATOR

        st.markdown("---")
        st.markdown(f"*MergeMate v{__version__}*")

    return output_filename, separator


def _render_upload_section() -> List[str]:
    """
    Render upload controls and return the final list of file paths to merge.
    Manages session-state so temp files are written only when uploads change.
    """
    upload_method = st.radio(
        "Choose upload method",
        ["Individual Files", "ZIP Archive"],
        horizontal=True,
    )

    # Reset state when the method changes
    if st.session_state.last_upload_method != upload_method:
        _cleanup_temp_files(st.session_state.temp_individual_files)
        if st.session_state.zip_temp_dir:
            _cleanup_temp_files([st.session_state.zip_temp_dir])
        st.session_state.temp_individual_files = []
        st.session_state.zip_temp_dir = None
        st.session_state.zip_file_paths = []
        st.session_state.zip_excluded = set()
        st.session_state.last_upload_method = upload_method

    file_paths: list[str] = []

    # ── Individual Files ─────────────────────────────────────────────────────
    if upload_method == "Individual Files":
        uploaded_files = st.file_uploader(
            "Choose files to merge",
            accept_multiple_files=True,
            type=UPLOAD_EXTENSIONS,
        )

        if uploaded_files:
            # Re-write only when the set of filenames changes
            current_names = {f.name for f in uploaded_files}
            existing_names = {os.path.basename(p) for p in st.session_state.temp_individual_files}

            if current_names != existing_names:
                _cleanup_temp_files(st.session_state.temp_individual_files)
                st.session_state.temp_individual_files = []
                tmp = tempfile.gettempdir()
                for uf in uploaded_files:
                    dest = os.path.join(tmp, uf.name)
                    with open(dest, "wb") as fh:
                        fh.write(uf.getbuffer())
                    st.session_state.temp_individual_files.append(dest)

            file_paths = list(st.session_state.temp_individual_files)

    # ── ZIP Archive ──────────────────────────────────────────────────────────
    else:
        zip_file = st.file_uploader("Upload ZIP archive", type=["zip"])

        if zip_file:
            # Re-extract only when a new ZIP is uploaded (detect by filename)
            zip_name = getattr(zip_file, "name", None)
            already_extracted = bool(st.session_state.zip_file_paths)

            # Use the file size + name as a simple change detector
            cache_key = f"{zip_name}_{zip_file.size}"
            if st.session_state.get("_zip_cache_key") != cache_key:
                if st.session_state.zip_temp_dir:
                    _cleanup_temp_files([st.session_state.zip_temp_dir])
                with st.spinner("Extracting ZIP archive…"):
                    paths, err = extract_zip_files(zip_file)
                if err:
                    st.error(f"❌ {err}")
                    paths = []
                st.session_state.zip_file_paths = paths
                st.session_state.zip_excluded = set()
                # Store the temp_dir for later cleanup
                if paths:
                    st.session_state.zip_temp_dir = os.path.dirname(paths[0])
                st.session_state["_zip_cache_key"] = cache_key

            all_paths = st.session_state.zip_file_paths

            if all_paths:
                st.markdown(f"**{len(all_paths)} text file(s) found in archive**")
                with st.expander("Select files to include", expanded=True):
                    for p in all_paths:
                        bname = os.path.basename(p)
                        checked = bname not in st.session_state.zip_excluded
                        if not st.checkbox(bname, value=checked, key=f"zip_chk_{bname}"):
                            st.session_state.zip_excluded.add(bname)
                        else:
                            st.session_state.zip_excluded.discard(bname)

                file_paths = [
                    p for p in all_paths
                    if os.path.basename(p) not in st.session_state.zip_excluded
                ]

    return file_paths


def _render_file_list(file_paths: List[str]) -> None:
    """Display a table of selected files with size info."""
    with st.expander(f"📋 {len(file_paths)} file(s) queued for merge", expanded=False):
        rows = []
        for i, fp in enumerate(file_paths, 1):
            bname = os.path.basename(fp)
            size = os.path.getsize(fp) if os.path.isfile(fp) else 0
            rows.append({"#": i, "Filename": bname, "Size": f"{size:,} bytes"})
        st.table(rows)


def _render_merge_results(merged_content: str, output_filename: str) -> None:
    """Render the success banner, preview, download button, and stats."""
    st.success("✅ Files merged successfully!")

    # ── Preview ──────────────────────────────────────────────────────────────
    st.subheader("Preview")
    preview_chars = st.slider(
        "Preview length (characters)", 500, 5_000, 1_000, step=500
    )
    truncated = len(merged_content) > preview_chars
    preview_text = merged_content[:preview_chars] + ("…" if truncated else "")
    st.text_area("Merged content preview", value=preview_text, height=250, disabled=True)

    # ── Download ─────────────────────────────────────────────────────────────
    st.download_button(
        label="📥 Download Merged File",
        data=merged_content.encode("utf-8"),
        file_name=output_filename,
        mime="text/plain",
        use_container_width=True,
    )

    # ── Statistics ────────────────────────────────────────────────────────────
    total_lines = len(merged_content.splitlines())  # accurate for \r\n and \n
    total_words = len(merged_content.split())
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Characters", f"{len(merged_content):,}")
    c2.metric("Total Lines", f"{total_lines:,}")
    c3.metric("Total Words", f"{total_words:,}")


def _render_how_to_use() -> None:
    with st.expander("ℹ️ How to use", expanded=False):
        st.markdown(f"""
### Instructions
1. **Choose upload method** — select individual files or a ZIP archive.
2. **Upload files** — use the file uploader to select your text files.
3. **Configure options** — set output filename and separator in the **sidebar**.
4. **Merge files** — click **🔗 Merge Files** to combine all files.
5. **Download** — download the merged file with all content combined.

### Output format
Each file's content is preceded by a filename header:
```
filename.ext:
--------------
[file content here]

{"=" * 40}

nextfile.ext:
-------------
[next file content here]
```

### Supported file types
Programming, web, config, and documentation files including
`.py`, `.java`, `.js`, `.html`, `.css`, `.json`, `.yml`,
`.cpp`, `.rs`, `.go`, `.kt`, `.ts`, and {len(TEXT_EXTENSIONS)} extensions total.

### Version
MergeMate v{__version__}
        """)


def main() -> None:
    st.set_page_config(
        page_title="MergeMate — File Merger Tool",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _init_session_state()

    # ── Header ────────────────────────────────────────────────────────────────
    st.title("📄 MergeMate")
    st.markdown("Merge multiple text files into one organized document.")

    # ── Sidebar options ───────────────────────────────────────────────────────
    output_filename, separator = _render_sidebar()

    # ── Upload section ────────────────────────────────────────────────────────
    st.subheader("Upload Files")
    file_paths = _render_upload_section()

    # ── File list & merge action ──────────────────────────────────────────────
    if file_paths:
        st.success(f"📁 {len(file_paths)} file(s) ready to merge")
        _render_file_list(file_paths)

        if st.button("🔗 Merge Files", type="primary", use_container_width=True):
            with st.spinner("Merging files…"):
                merged_content = merge_files(file_paths, separator)
                _output_path, err = save_merged_file(merged_content, output_filename)

            if err:
                st.error(f"❌ Error saving merged file: {err}")
            else:
                _render_merge_results(merged_content, output_filename)

    else:
        st.info("👆 Please upload files to begin merging")

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("---")
    _render_how_to_use()


if __name__ == "__main__":
    main()