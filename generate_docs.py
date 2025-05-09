import os
from pathlib import Path
import yaml
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Gemini setup
genai.configure(api_key=API_KEY)

MODEL_NAME = "models/gemini-2.0-flash-thinking-exp-01-21"

SYSTEM_PROMPT = """Act as a Python code documentation assistant. Your task is to add comprehensive documentation to the provided Python code snippet, making it clear, understandable, and maintainable.

**Instructions:**

1.  **Analyze the Code:** Understand the purpose and logic of the provided Python code.
2.  **Add Docstrings:**
    * Include a **module-level docstring** at the very beginning of the script explaining its overall purpose and functionality.
    * Add **function/method/class docstrings** immediately following their definition lines (`def` or `class`).
    * Follow a clear and standard convention, preferably **Google style**:
        * Start with a concise one-line summary (using the imperative mood, e.g., "Calculate..." not "Calculates..."). End with a period.
        * Include a blank line after the summary if more detail follows.
        * Add further elaboration on the object's purpose or logic if necessary.
        * Use an `Args:` section to detail each parameter (`parameter_name (type): Description of the parameter.`).
        * Use a `Returns:` section to detail the return value (`type: Description of the return value.`). If the function doesn't return anything explicitly (returns `None`), you can state that or omit the section.
        * Use a `Raises:` section (if applicable) to detail any specific exceptions the code might intentionally raise (`ExceptionType: Condition under which it's raised.`).
3.  **Add Inline Comments:** Insert inline comments (`#`) judiciously to clarify specific lines or blocks of code that involve complex logic, non-obvious operations, or important algorithmic steps. Avoid commenting on obvious code.
4.  **Maintain Code Integrity:** Do not change the original code's logic or functionality. Only add documentation elements (docstrings and comments).
5.  **Output Format:** Return the *complete* Python code, including the original logic, with all the added docstrings and relevant inline comments integrated directly into the code. Ensure the output is presented as a single, well-formatted Python code block.

**Python Code to Document:**
"""

def call_gemini(code: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content([
        {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n```python\n{code}\n```"}]}
    ])
    return response.text

def generate_docs(code_path: Path, output_path: Path):
    code = code_path.read_text(encoding="utf-8")
    documentation = call_gemini(code)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"# Documentation for `{code_path.name}`\n\n{documentation}", encoding="utf-8")

def update_mkdocs_yml():
    GENERATED_DIR = Path("docs/generated")
    MKDOCS_YML_PATH = Path("mkdocs.yml")

    with open(MKDOCS_YML_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    files = [f for f in GENERATED_DIR.iterdir() if f.suffix == ".md"]
    files.sort()

    new_nav = []
    for item in config.get("nav", []):
        if isinstance(item, dict) and "Generated Docs" in item:
            continue
        new_nav.append(item)

    generated_section = {"Generated Docs": []}
    for file in files:
        title = file.stem.replace("_", " ").title()
        generated_section["Generated Docs"].append({title: f"generated/{file.name}"})

    new_nav.append(generated_section)
    config["nav"] = new_nav

    with open(MKDOCS_YML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, sort_keys=False)

    print("✅ mkdocs.yml updated successfully.")

def main():
    src_dir = Path("src")
    out_dir = Path("docs/generated")

    for file in src_dir.rglob("*.py"):
        generate_docs(file, out_dir / f"{file.stem}.md")

    update_mkdocs_yml()
    print("🎉 Documentation generated and mkdocs navigation updated.")

if __name__ == "__main__":
    main()