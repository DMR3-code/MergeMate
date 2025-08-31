import streamlit as st
import os
from pathlib import Path
import zipfile
import tempfile
from typing import List, Tuple
import chardet

def detect_encoding(file_path: str) -> str:
    """Detect the encoding of a file."""
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            return result['encoding'] if result['encoding'] else 'utf-8'
    except:
        return 'utf-8'

def read_file_content(file_path: str) -> Tuple[str, bool]:
    """Read file content with proper encoding detection."""
    try:
        # First try to detect encoding
        encoding = detect_encoding(file_path)
        
        with open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
            return content, True
    except UnicodeDecodeError:
        # Fallback to utf-8 with error handling
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                return content, True
        except:
            return f"[Error: Could not read file {file_path}]", False
    except Exception as e:
        return f"[Error reading {file_path}: {str(e)}]", False

def merge_files(file_paths: List[str], separator: str = "\n" + "="*80 + "\n") -> str:
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

def save_merged_file(content: str, output_filename: str) -> str:
    """Save merged content to a file and return the file path."""
    output_path = os.path.join(tempfile.gettempdir(), output_filename)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return output_path
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None

def extract_zip_files(zip_file) -> List[str]:
    """Extract files from uploaded zip and return list of file paths."""
    temp_dir = tempfile.mkdtemp()
    file_paths = []
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # Get all files recursively
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Only include text-based files
                if is_text_file(file_path):
                    file_paths.append(file_path)
                    
        return sorted(file_paths)
    except Exception as e:
        st.error(f"Error extracting zip file: {str(e)}")
        return []

def is_text_file(file_path: str) -> bool:
    """Check if a file is likely a text file based on extension."""
    text_extensions = {
        '.txt', '.xml', '.java', '.py', '.js', '.html', '.css', '.json', 
        '.md', '.yml', '.yaml', '.ini', '.cfg', '.conf', '.log', '.sql',
        '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs',
        '.sh', '.bat', '.ps1', '.r', '.scala', '.kt', '.swift', '.dart',
        '.tsx', '.jsx', '.vue', '.svelte', '.ts', '.coffee', '.less',
        '.scss', '.sass', '.styl', '.pug', '.ejs', '.hbs', '.mustache'
    }
    
    return Path(file_path).suffix.lower() in text_extensions

def main():
    st.set_page_config(
        page_title="File Merger Tool",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 File Merger Tool")
    st.markdown("Merge multiple text files into one file with filename headers")
    
    # Create two columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Files")
        
        # File upload options
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
                type=['txt', 'xml', 'java', 'py', 'js', 'html', 'css', 'json', 
                      'md', 'yml', 'yaml', 'ini', 'cfg', 'conf', 'log', 'sql',
                      'c', 'cpp', 'h', 'hpp', 'cs', 'php', 'rb', 'go', 'rs',
                      'sh', 'bat', 'ps1', 'r', 'scala', 'kt', 'swift', 'dart',
                      'tsx', 'jsx', 'vue', 'svelte', 'ts', 'coffee', 'less',
                      'scss', 'sass', 'styl', 'pug', 'ejs', 'hbs', 'mustache']
            )
            
            if uploaded_files:
                # Save uploaded files temporarily
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
                file_paths = extract_zip_files(zip_file)
    
    with col2:
        st.subheader("Options")
        
        # Output filename
        output_filename = st.text_input(
            "Output filename:",
            value="merged_files.txt",
            help="Name for the merged output file"
        )
        
        # Custom separator
        use_custom_separator = st.checkbox("Use custom separator")
        if use_custom_separator:
            separator = st.text_area(
                "Custom separator:",
                value="\n" + "="*80 + "\n",
                height=100,
                help="Text to insert between files"
            )
        else:
            separator = "\n" + "="*80 + "\n"
        
        # Show file count
        if file_paths:
            st.success(f"📁 {len(file_paths)} files selected")
    
    # Display selected files
    if file_paths:
        st.subheader("Selected Files")
        
        # Show files in an expander
        with st.expander(f"View {len(file_paths)} selected files", expanded=False):
            for i, file_path in enumerate(file_paths, 1):
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                st.write(f"{i}. **{filename}** ({file_size:,} bytes)")
        
        # Merge button
        if st.button("🔗 Merge Files", type="primary", use_container_width=True):
            with st.spinner("Merging files..."):
                try:
                    # Merge files
                    merged_content = merge_files(file_paths, separator)
                    
                    # Save merged file
                    output_path = save_merged_file(merged_content, output_filename)
                    
                    if output_path:
                        st.success("✅ Files merged successfully!")
                        
                        # Show preview
                        st.subheader("Preview")
                        preview_length = min(1000, len(merged_content))
                        st.text_area(
                            "Merged content preview:",
                            value=merged_content[:preview_length] + 
                                  ("..." if len(merged_content) > preview_length else ""),
                            height=200,
                            disabled=True
                        )
                        
                        # Download button
                        with open(output_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                            
                        st.download_button(
                            label="📥 Download Merged File",
                            data=file_content,
                            file_name=output_filename,
                            mime="text/plain",
                            use_container_width=True
                        )
                        
                        # Statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Files Merged", len(file_paths))
                        with col2:
                            st.metric("Total Characters", f"{len(merged_content):,}")
                        with col3:
                            st.metric("Total Lines", f"{merged_content.count(chr(10)) + 1:,}")
                        
                except Exception as e:
                    st.error(f"❌ Error merging files: {str(e)}")
                
                finally:
                    # Clean up temporary files
                    for temp_file in temp_files:
                        try:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                        except:
                            pass
    
    else:
        st.info("👆 Please upload files to begin merging")
    
    # Instructions
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

if __name__ == "__main__":
    main()