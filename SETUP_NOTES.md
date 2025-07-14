# Setup Notes

## Virtual Environment Setup

Due to system requirements, you'll need to install the necessary packages first:

### For Python 3.11 (Recommended for TensorFlow/CUDA compatibility):
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
python3.11 -m venv venv
```

### For Python 3.12 (Current system version):
```bash
sudo apt install python3.12-venv
python3 -m venv venv
```

### Activate Virtual Environment:
```bash
source venv/bin/activate
```

### Install Dependencies:
```bash
pip install -r requirements.txt
```

## CUDA Setup
For CUDA support with TensorFlow, ensure you have:
- NVIDIA GPU drivers installed
- CUDA toolkit installed
- cuDNN library installed

The requirements.txt includes tensorflow-gpu and CUDA-compatible versions.
