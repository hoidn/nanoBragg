import json
import sys
import torch
import subprocess
from datetime import datetime

# Get git commit
git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()

metadata = {
    "timestamp": datetime.now().isoformat(),
    "git_commit": git_commit,
    "python_version": sys.version,
    "torch_version": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "default_dtype": str(torch.get_default_dtype()),
}

if torch.cuda.is_available():
    metadata["cuda_device"] = torch.cuda.get_device_name(0)

print(json.dumps(metadata, indent=2))
