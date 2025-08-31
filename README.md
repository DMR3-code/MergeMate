# 📄 MergeMate


Easily merge multiple text/code/config files into a single, organized document.
Supports individual file uploads or entire ZIP archives. Each file is merged with clear headers and separators, making it perfect for developers, writers, and anyone managing lots of text-based files.

---

## ✨ Features

* 📂 **Upload Options**: Upload individual files or a complete ZIP archive.
* 🛠️ **Wide File Support**: `.txt`, `.py`, `.java`, `.json`, `.html`, `.css`, `.yml`, `.cpp`, and more.
* 🔍 **Automatic Encoding Detection** (via `chardet`).
* 📝 **Custom Separators**: Insert your own separator between files.
* 📊 **Statistics Dashboard**: Files merged, total characters, and line count.
* 👀 **Preview Mode**: Check the merged output before saving.
* 📥 **Download Ready**: Save the merged file instantly.

---

## 🚀 Installation & Run

### 1. Clone the repository

```bash
git clone https://github.com/DMR3-code/mergemate.git
cd mergemate
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate      # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run src/app.py
```

---

## 📖 Usage

1. Open the app in your browser (Streamlit will give you a local URL).
2. Choose upload method: **Individual Files** or **ZIP Archive**.
3. Select files to merge.
4. Configure options: **output filename** and **custom separator**.
5. Click **🔗 Merge Files**.
6. Preview the merged result and **download** the final file.

---

## 🛠️ Tech Stack

* **Python 3.8+**
* **Streamlit** – interactive UI
* **chardet** – encoding detection
* **zipfile & tempfile** – file handling

---