import streamlit as st
import tempfile
import os
from typing import List
from .file_utils import read_file_content, save_content_to_file, get_file_info, SUPPORTED_EXTENSIONS
from .zip_utils import extract_zip_files


class FileMergerApp:
    def __init__(self):
        self.set_page_config()

    def set_page_config(self):
        st.set_page_config(
            page_title="MergeMate",
            page_icon="📄",
            layout="wide"
        )

    def render_header(self):
        st.title("📄 MergeMate")
        st.markdown("Merge multiple text files into one file with filename headers")

    def render_upload_section(self):
        col1, col2 = st.columns([2, 1])

        with col1:
            return self.render_file_upload()

        with col2:
            return self.render_options()

    def render_file_upload(self):
        st.subheader("Upload Files")

        upload_method = st.radio(
            "Choose upload method:",
            ["Individual Files", "ZIP Archive"],
            horizontal=True
        )

        file_paths = []
        temp_files = []

        if upload_method == "Individual Files":
            uploaded_files = st.file_uploader(
                "Choose files to merge",
                accept_multiple_files=True,
                type=list(ext.replace('.', '') for ext in SUPPORTED_EXTENSIONS)
            )

            if uploaded_files:
                for uploaded_file in uploaded_files:
                    temp_file_path = os.path.join(
                        tempfile.gettempdir(),
                        uploaded_file.name
                    )
                    with open(temp_file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    file_paths.append(temp_file_path)
                    temp_files.append(temp_file_path)

        else:  # ZIP Archive
            zip_file = st.file_uploader(
                "Upload ZIP archive containing text files",
                type=['zip']
            )

            if zip_file:
                try:
                    file_paths = extract_zip_files(zip_file)
                except Exception as e:
                    st.error(str(e))

        return file_paths, temp_files

    def render_options(self):
        st.subheader("Options")

        output_filename = st.text_input(
            "Output filename:",
            value="merged_files.txt",
            help="Name for the merged output file"
        )

        use_custom_separator = st.checkbox("Use custom separator")
        if use_custom_separator:
            separator = st.text_area(
                "Custom separator:",
                value="\n" + "=" * 80 + "\n",
                height=100,
                help="Text to insert between files"
            )
        else:
            separator = "\n" + "=" * 80 + "\n"

        return output_filename, separator

    def render_file_list(self, file_paths: List[str]):
        if file_paths:
            st.subheader("Selected Files")

            with st.expander(f"View {len(file_paths)} selected files", expanded=False):
                for i, file_path in enumerate(file_paths, 1):
                    file_info = get_file_info(file_path)
                    st.write(f"{i}. **{file_info['name']}** ({file_info['size']:,} bytes)")

    def merge_files(self, file_paths: List[str], separator: str) -> str:
        """Merge multiple files into one string with filename headers."""
        merged_content = []

        for file_path in file_paths:
            filename = os.path.basename(file_path)

            # Add filename header
            header = f"\n{filename}:\n{'-' * (len(filename) + 1)}\n"
            merged_content.append(header)

            # Read and add file content
            content, success = read_file_content(file_path)
            merged_content.append(content)

            # Add separator between files (except for the last file)
            if file_path != file_paths[-1]:
                merged_content.append(separator)

        return "".join(merged_content)

    def process_merge(self, file_paths: List[str], output_filename: str, separator: str):
        if st.button("🔗 Merge Files", type="primary", use_container_width=True):
            with st.spinner("Merging files..."):
                try:
                    merged_content = self.merge_files(file_paths, separator)

                    output_path = os.path.join(tempfile.gettempdir(), output_filename)
                    save_content_to_file(merged_content, output_path)

                    st.success("✅ Files merged successfully!")
                    self.render_preview(merged_content)
                    self.render_download_button(output_path, output_filename)
                    self.render_statistics(merged_content, file_paths)

                except Exception as e:
                    st.error(f"❌ Error merging files: {str(e)}")

    def render_preview(self, merged_content: str):
        st.subheader("Preview")
        preview_length = min(1000, len(merged_content))
        st.text_area(
            "Merged content preview:",
            value=merged_content[:preview_length] +
                  ("..." if len(merged_content) > preview_length else ""),
            height=200,
            disabled=True
        )

    def render_download_button(self, output_path: str, output_filename: str):
        with open(output_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        st.download_button(
            label="📥 Download Merged File",
            data=file_content,
            file_name=output_filename,
            mime="text/plain",
            use_container_width=True
        )

    def render_statistics(self, merged_content: str, file_paths: List[str]):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Files Merged", len(file_paths))
        with col2:
            st.metric("Total Characters", f"{len(merged_content):,}")
        with col3:
            st.metric("Total Lines", f"{merged_content.count(chr(10)) + 1:,}")

    def render_instructions(self):
        with st.expander("ℹ️ How to use", expanded=False):
            st.markdown("""
            ### Instructions:
            1. **Choose upload method**: Select either individual files or a ZIP archive
            2. **Upload files**: Use the file uploader to select your text files
            3. **Configure options**: Set output filename and separator (optional)
            4. **Merge files**: Click the merge button to combine all files
            5. **Download**: Download the merged file with all content combined

            ### Supported file types:
            - Programming files: `.java`, `.py`, `.js`, `.cpp`, `.c`, `.cs`, etc.
            - Web files: `.html`, `.css`, `.xml`, `.json`, `.tsx`, `.jsx`
            - Configuration files: `.yml`, `.ini`, `.cfg`, `.conf`
            - Documentation: `.md`, `.txt`, `.log`
            - And many more text-based formats

            ### Output format:
            Each file's content will be preceded by its filename like this:
            ```
            filename.ext:
            --------------
            [file content here]

            ================================================================================

            nextfile.ext:
            -------------
            [next file content here]
            ```
            """)

    def cleanup_temp_files(self, temp_files: List[str]):
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

    def run(self):
        self.render_header()
        file_paths, temp_files = self.render_upload_section()

        if file_paths:
            output_filename, separator = self.render_options()
            st.success(f"📁 {len(file_paths)} files selected")
            self.render_file_list(file_paths)
            self.process_merge(file_paths, output_filename, separator)
            self.cleanup_temp_files(temp_files)
        else:
            st.info("👆 Please upload files to begin merging")

        self.render_instructions()


def main():
    app = FileMergerApp()
    app.run()


if __name__ == "__main__":
    main()