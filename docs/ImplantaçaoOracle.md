rsync -avz --progress \
  --exclude 'venv/' \
  --exclude 'env/' \
  --exclude '.venv/' \
  --exclude '.git/' \
  --exclude '.gitignore' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  --exclude '*.pyd' \
  --exclude '.Python' \
  --exclude '*.so' \
  --exclude '*.egg' \
  --exclude '*.egg-info/' \
  --exclude 'dist/' \
  --exclude 'build/' \
  --exclude '.pytest_cache/' \
  --exclude '.vscode/' \
  --exclude '.idea/' \
  --exclude '*.log' \
  --exclude '.DS_Store' \
  --exclude 'Thumbs.db' \
  --exclude '*~' \
  -e "ssh -i chave.key" \
  /home/eltonss/Documents/VS\ CODE/FasiTech/ \
  opc@IP:/home/opc/appStreamLit/