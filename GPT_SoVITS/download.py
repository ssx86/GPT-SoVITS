import os
import zipfile
import requests
import shutil
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g2pw_model_path = os.path.join(base_dir, "GPT_SoVITS/text/G2PWModel/g2pW.onnx")

if not os.path.exists(g2pw_model_path):
    print("start download g2pw model")
    parent_directory = os.path.dirname(os.path.dirname(g2pw_model_path))
    zip_dir = os.path.join(parent_directory,"G2PWModel_1.1.zip")
    extract_dir = os.path.join(parent_directory,"G2PWModel_1.1")
    extract_dir_new = os.path.join(parent_directory,"G2PWModel")
    print("Downloading g2pw model...")
    modelscope_url = "https://paddlespeech.bj.bcebos.com/Parakeet/released_models/g2p/G2PWModel_1.1.zip"
    with requests.get(modelscope_url, stream=True) as r:
        r.raise_for_status()
        with open(zip_dir, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    print("Extracting g2pw model...")
    with zipfile.ZipFile(zip_dir, "r") as zip_ref:
        zip_ref.extractall(parent_directory)
    
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            src_path = os.path.join(root, file)
            dst_path = os.path.join(extract_dir_new, file)
            shutil.copy2(src_path, dst_path)
else:
    print("g2pw models exists, continue...")
