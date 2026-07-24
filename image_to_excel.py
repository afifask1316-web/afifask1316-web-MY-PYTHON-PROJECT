import argparse
import os
import shutil
from pathlib import Path

import cv2
import pandas as pd
import pytesseract
from PIL import Image
from pytesseract import Output

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except ImportError:
    tk = None


def find_tesseract_executable():
    if shutil.which("tesseract"):
        return shutil.which("tesseract")

    default_windows = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if default_windows.exists():
        return str(default_windows)

    raise FileNotFoundError(
        "Tesseract not found. Install it from https://github.com/tesseract-ocr/tesseract and add it to PATH."
    )


def preprocess_image(image_path: Path):
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.bilateralFilter(gray, 9, 75, 75)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def cluster_tokens_by_position(tokens, max_gap=70):
    if not tokens:
        return []

    tokens = sorted(tokens, key=lambda item: item[0])
    groups = []
    current_group = [tokens[0][1]]
    last_x = tokens[0][0]

    for x, text in tokens[1:]:
        if x - last_x > max_gap:
            groups.append(" ".join(current_group).strip())
            current_group = [text]
        else:
            current_group.append(text)
        last_x = x

    groups.append(" ".join(current_group).strip())
    return groups


def extract_rows_from_image(image_path: Path):
    ocr_image = preprocess_image(image_path)
    pil_image = Image.fromarray(ocr_image)

    data = pytesseract.image_to_data(
        pil_image,
        config="--psm 6",
        output_type=Output.DICT,
    )

    rows = {}
    n_boxes = len(data["level"])
    for i in range(n_boxes):
        text = data["text"][i].strip()
        if not text:
            continue

        line_num = data["line_num"][i]
        left = data["left"][i]
        rows.setdefault(line_num, []).append((left, text))

    extracted_rows = []
    for line_num in sorted(rows):
        grouped = cluster_tokens_by_position(rows[line_num])
        extracted_rows.append(grouped)

    return extracted_rows


def normalize_rows(rows):
    max_columns = max((len(row) for row in rows), default=0)
    normalized = [row + [""] * (max_columns - len(row)) for row in rows]
    return normalized


def save_rows_to_excel(rows, output_path: Path):
    if not rows:
        raise ValueError("No text rows were extracted from the image.")

    normalized = normalize_rows(rows)
    df = pd.DataFrame(normalized)
    df.to_excel(output_path, index=False, header=False)
    return output_path


def convert_image_to_excel(image_path: Path, output_path: Path = None):
    if output_path is None:
        output_path = image_path.with_suffix(".xlsx")

    rows = extract_rows_from_image(image_path)
    saved_path = save_rows_to_excel(rows, output_path)
    return saved_path


def convert_folder_to_excel(folder_path: Path, output_folder: Path = None):
    if output_folder is None:
        output_folder = folder_path / "excel_output"
    output_folder.mkdir(parents=True, exist_ok=True)

    image_extensions = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"}
    converted_files = []

    for image_path in sorted(folder_path.iterdir()):
        if image_path.suffix.lower() in image_extensions:
            out_file = output_folder / image_path.with_suffix(".xlsx").name
            convert_image_to_excel(image_path, out_file)
            converted_files.append(out_file)

    return converted_files


def run_cli():
    parser = argparse.ArgumentParser(
        description="Convert hardcopy text image files into Excel spreadsheets using OCR.",
    )
    parser.add_argument("--image", help="Path to a single image file.")
    parser.add_argument("--folder", help="Path to a folder containing images.")
    parser.add_argument("--out", help="Optional output Excel path or output folder.")

    args = parser.parse_args()

    pytesseract.pytesseract.tesseract_cmd = find_tesseract_executable()

    if args.image:
        input_path = Path(args.image)
        output_path = Path(args.out) if args.out else None
        result = convert_image_to_excel(input_path, output_path)
        print(f"Converted image to Excel: {result}")

    elif args.folder:
        folder_path = Path(args.folder)
        output_folder = Path(args.out) if args.out else None
        converted = convert_folder_to_excel(folder_path, output_folder)
        print(f"Converted {len(converted)} images to Excel in: {output_folder}")

    else:
        parser.print_help()


if tk is not None:
    class ImageToExcelApp:
        def __init__(self, root):
            self.root = root
            self.root.title("OCR to Excel Converter")
            self.root.geometry("520x240")
            self.root.resizable(False, False)

            self.source_path = tk.StringVar()
            self.destination_path = tk.StringVar()

            tk.Label(root, text="Select image or folder:").pack(pady=(16, 4))
            tk.Entry(root, textvariable=self.source_path, width=68).pack(padx=16)
            tk.Button(root, text="Browse", command=self.select_source).pack(pady=6)

            tk.Label(root, text="Excel output file or folder:").pack(pady=(12, 4))
            tk.Entry(root, textvariable=self.destination_path, width=68).pack(padx=16)
            tk.Button(root, text="Browse Output", command=self.select_output).pack(pady=6)

            tk.Button(root, text="Convert", width=20, command=self.convert).pack(pady=12)
            tk.Label(root, text="Notes: Install Tesseract OCR and add it to PATH.").pack(pady=(4, 0))

        def select_source(self):
            file_path = filedialog.askopenfilename(
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.tiff *.bmp *.gif")],
            )
            if file_path:
                self.source_path.set(file_path)

        def select_output(self):
            output_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel workbook", "*.xlsx")],
            )
            if output_path:
                self.destination_path.set(output_path)

        def convert(self):
            try:
                source = Path(self.source_path.get())
                if not source.exists():
                    raise ValueError("Selected source does not exist.")

                pytesseract.pytesseract.tesseract_cmd = find_tesseract_executable()

                if source.is_dir():
                    output_folder = Path(self.destination_path.get()) if self.destination_path.get() else None
                    converted = convert_folder_to_excel(source, output_folder)
                    messagebox.showinfo("Done", f"Converted {len(converted)} images to Excel.")
                else:
                    output_file = Path(self.destination_path.get()) if self.destination_path.get() else None
                    result = convert_image_to_excel(source, output_file)
                    messagebox.showinfo("Done", f"Excel saved to: {result}")
            except Exception as exc:
                messagebox.showerror("Error", str(exc))


if __name__ == "__main__":
    if tk is not None and os.name == "nt":
        root = tk.Tk()
        ImageToExcelApp(root)
        root.mainloop()
    else:
        run_cli()
