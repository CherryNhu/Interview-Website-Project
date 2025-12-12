'''
-----------------------------------------------------------------------
File: latex_ops.py
Creation Time: Nov 24th 2023 3:29 am
Author: Saurabh Zinjad
Developer Email: zinjadsaurabh1997@gmail.com
Copyright (c) 2023 Saurabh Zinjad. All rights reserved | GitHub: Ztrimus
-----------------------------------------------------------------------
'''

import os
import jinja2
import subprocess
import base64
import zipfile

def escape_for_latex(data):
    if isinstance(data, dict):
        new_data = {}
        for key in data.keys():
            new_data[key] = escape_for_latex(data[key])
        return new_data
    elif isinstance(data, list):
        return [escape_for_latex(item) for item in data]
    elif isinstance(data, str):
        # Adapted from https://stackoverflow.com/q/16259923
        latex_special_chars = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\^{}",
            "\\": r"\textbackslash{}",
            "\n": "\\newline%\n",
            "-": r"{-}",
            "\xA0": "~",  # Non-breaking space
            "[": r"{[}",
            "]": r"{]}",
        }
        return "".join([latex_special_chars.get(c, c) for c in data])

    return data

def latex_to_pdf(json_resume, dst_path):
    try:
        module_dir = os.path.dirname(__file__)
        templates_path = os.path.join(os.path.dirname(module_dir), 'templates')

        latex_jinja_env = jinja2.Environment(
            block_start_string="\BLOCK{",
            block_end_string="}",
            variable_start_string="\VAR{",
            variable_end_string="}",
            comment_start_string="\#{",
            comment_end_string="}",
            line_statement_prefix="%-",
            line_comment_prefix="%#",
            trim_blocks=True,
            autoescape=False,
            loader=jinja2.FileSystemLoader(templates_path),
        )

        escaped_json_resume = escape_for_latex(json_resume)

        resume_latex = use_template(latex_jinja_env, escaped_json_resume)

        tex_temp_path = os.path.join(os.path.realpath(templates_path), os.path.basename(dst_path).replace(".pdf", ".tex"))

        write_file(tex_temp_path, resume_latex)
        save_latex_as_pdf(tex_temp_path, dst_path)
        return resume_latex
    except Exception as e:
        print(e)
        return None

def use_template(jinja_env, json_resume):
    try:
        resume_template = jinja_env.get_template(f"resume.tex.jinja")
        resume = resume_template.render(json_resume)

        return resume
    except Exception as e:
        print(e)
        return None
def write_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(data)
import os
import time
import subprocess

def save_latex_as_pdf(tex_file_path: str, dst_path: str):
    try:
        prev_loc = os.getcwd()
        # print(f"Current working directory: {prev_loc}")
        os.chdir(os.path.dirname(tex_file_path))
        # print(f"Changed to directory: {os.getcwd()}")
        if not os.path.exists(tex_file_path):
            raise FileNotFoundError(f"TeX file not found: {tex_file_path}")
        if not os.path.exists(os.path.join(os.path.dirname(tex_file_path), "resume.cls")):
            raise FileNotFoundError(f"resume.cls not found in {os.path.dirname(tex_file_path)}")
        # print(f"Running pdflatex on: {tex_file_path}")
        # with open(tex_file_path, 'r', encoding='utf-8') as f:
        #     print(f"LaTeX content:\n{f.read()}")
        result = subprocess.run(
            ["pdflatex", tex_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # print(f"pdflatex stdout: {result.stdout}")
        # print(f"pdflatex stderr: {result.stderr}")
        if result.returncode != 0:
            raise Exception(f"pdflatex failed: {result.stderr}")
        resulted_pdf_path = os.path.abspath(tex_file_path.replace(".tex", ".pdf"))
        dst_path = os.path.abspath(os.path.join(prev_loc, dst_path))  # Ensure dst_path is absolute
        # print(f"Checking for PDF at: {resulted_pdf_path}")
        if not os.path.exists(resulted_pdf_path):
            raise FileNotFoundError(f"PDF file not found: {resulted_pdf_path}")
        dst_tex_path = dst_path.replace(".pdf", ".tex")
        # print(f"Renaming {resulted_pdf_path} to {dst_path}")
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)  # Ensure destination directory exists
        os.rename(resulted_pdf_path, dst_path)
        # print(f"Renaming {tex_file_path} to {dst_tex_path}")
        os.rename(tex_file_path, dst_tex_path)
        os.chdir(prev_loc)
        filename_without_ext = os.path.basename(tex_file_path).split(".")[0]
        unnecessary_files = [
            file
            for file in os.listdir(os.path.dirname(os.path.realpath(tex_file_path)))
            if file.startswith(filename_without_ext) and not file.endswith((".pdf", ".tex"))
        ]
        for file in unnecessary_files:
            file_path = os.path.join(os.path.dirname(tex_file_path), file)
            if os.path.exists(file_path):
                os.remove(file_path)
        return dst_path
    except Exception as e:
        os.chdir(prev_loc)
        raise Exception(f"Failed to convert LaTeX to PDF: {str(e)}")

def encode_tex_file(pdf_path: str) -> str:
    """Encode tex file and resume.cls into base64 zip for Overleaf."""
    try:
        # Get paths for .tex file and resume.cls template
        tex_path = pdf_path.replace('.pdf', '.tex')
        
        # ✅ CẬP NHẬT ĐƯỜNG DẪN ĐẾN RESUME.CLS
        current_file_dir = os.path.dirname(__file__)  # utils directory
        src_dir = os.path.dirname(current_file_dir)   # src directory
        templates_dir = os.path.join(src_dir, 'templates')
        resume_cls_path = os.path.join(templates_dir, 'resume.cls')
        
        # ✅ KIỂM TRA FILE TỒN TẠI TRƯỚC KHI TẠO ZIP
        if not os.path.exists(tex_path):
            print(f"Warning: TEX file not found at {tex_path}")
            return None
            
        if not os.path.exists(resume_cls_path):
            print(f"Warning: resume.cls not found at {resume_cls_path}")
            return None
        
        # Create zip file path
        zip_path = pdf_path.replace('.pdf', '.zip')
        
        # ✅ TẠO ZIP FILE VỚI CẢ .TEX VÀ .CLS
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add .tex file with original name
            zipf.write(tex_path, os.path.basename(tex_path))
            
            # Add resume.cls file
            zipf.write(resume_cls_path, 'resume.cls')
        
        # ✅ ĐỌC VÀ ENCODE ZIP FILE
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        encoded_zip = base64.b64encode(zip_content).decode('utf-8')
        
        # Clean up zip file
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
        return encoded_zip
    except Exception as e:
        print(f"Error encoding tex file: {e}")
        import traceback
        traceback.print_exc()
        return None