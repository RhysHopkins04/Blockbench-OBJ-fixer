import os
import shutil
import re
from logic.blender_cleaner import run_blender_cleaner

TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "temp")

# === Normalize Group Name ===
def normalize_group_name(name):
    # Convert 'bone.001' → 'bone_1', etc.
    return re.sub(r'\.(\d+)', r'_\1', name)

# === Deduplicate and Normalize OBJ Groups ===
def deduplicate_obj(obj_path):
    group_counts = {}
    new_lines = []

    with open(obj_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("o "):
                raw_name = line.strip().split(" ", 1)[1]
                norm_name = normalize_group_name(raw_name)
                count = group_counts.get(norm_name, 0)
                new_group = f"{norm_name}_{count}" if count > 0 else norm_name
                group_counts[norm_name] = count + 1
                new_lines.append(f"o {new_group}\n")
            else:
                new_lines.append(line)

    with open(obj_path, 'w', encoding='utf-8') as out_obj:
        out_obj.writelines(new_lines)

    return sorted(group_counts.keys())

# === Java Group Class Generator ===
def write_java_class(class_name, group_names, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, class_name + ".java")
    with open(path, 'w') as f:
        f.write("public class " + class_name + " {\n")
        for name in group_names:
            const_name = name.upper().replace('-', '_').replace('.', '_')
            f.write(f"    public static final String {const_name} = \"{name}\";\n")
        f.write("}\n")
    return path

# === TXT Group List Generator ===
def write_txt_list(group_names, output_dir, output_name):
    os.makedirs(output_dir, exist_ok=True)
    txt_path = os.path.join(output_dir, f"{output_name}.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        for group in group_names:
            f.write(group + "\n")
    return txt_path

# === Main File Processor ===
def process_obj_file(input_path, output_dir, java_class=None, logger=print, generate_txt=False, output_name="model"):
    if not os.path.isfile(input_path):
        raise FileNotFoundError("File not found: " + input_path)

    logger("Cleaning model with Blender...")
    cleaned_path = run_blender_cleaner(input_path)

    if not os.path.exists(cleaned_path):
        raise RuntimeError("Blender failed to generate cleaned OBJ.")

    logger("Deduplicating group names...")
    group_names = deduplicate_obj(cleaned_path)

    logger(f"Found {len(group_names)} group(s) after processing.")

    final_name = output_name + ".obj"
    final_path = os.path.join(output_dir, final_name)
    shutil.move(cleaned_path, final_path)
    logger(f"Final OBJ saved to: {final_path}")

    if java_class:
        java_path = write_java_class(java_class, group_names, output_dir)
        logger(f"Java mapping saved to: {java_path}")

    if generate_txt:
        txt_path = write_txt_list(group_names, output_dir, output_name)
        logger(f"Group list saved to: {txt_path}")

    # Clean temp folder
    for f in os.listdir(TEMP_DIR):
        try:
            os.remove(os.path.join(TEMP_DIR, f))
        except Exception as e:
            logger(f"⚠️ Failed to clean temp file: {f} → {e}")
