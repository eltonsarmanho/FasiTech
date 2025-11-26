Compilar:
lualatex -halt-on-error -interaction=nonstopmode Apresentacao.tex

sudo apt-get update
sudo apt-get install -y texlive-luatex texlive-fonts-recommended texlive-fonts-extra
sudo apt-get install -y fonts-noto-color-emoji
sudo fc-cache -fv

sudo apt-get install -y texlive-luatex texlive-fonts-extra fonts-noto-color-emoji

# Atualizar repositórios
sudo apt-get update

# Instalar fontes LaTeX essenciais
sudo apt-get install -y texlive-latex-base
sudo apt-get install -y texlive-fonts-recommended
sudo apt-get install -y texlive-fonts-extra
sudo apt-get install -y texlive-latex-extra
sudo apt-get install -y texlive-xetex

# Instalar fontes do sistema
sudo apt-get install -y fonts-liberation
sudo apt-get install -y fonts-dejavu
sudo apt-get install -y fonts-noto
sudo apt-get install -y cm-super
sudo apt-get install -y dvipng

# Atualizar cache de fontes
sudo fc-cache -fv