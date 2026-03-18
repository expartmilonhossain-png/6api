import os
import zipfile

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        if '.venv' in dirs: dirs.remove('.venv')
        if '.git' in dirs: dirs.remove('.git')
        if '__pycache__' in dirs: dirs.remove('__pycache__')
        if '.idea' in dirs: dirs.remove('.idea')
        
        for file in files:
            if file == 'backend_4.0.zip' or file == 'pack.py' or file == 'pack.ps1':
                continue
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, path)
            ziph.write(file_path, arcname)

if __name__ == '__main__':
    backend_dir = r"C:\Users\Google11\Desktop\apphub3\backend"
    zip_path = r"C:\Users\Google11\Desktop\apphub3\backend_4.0.zip"
    
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    print(f"Creating {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir(backend_dir, zipf)
    print("Zipping complete.")
