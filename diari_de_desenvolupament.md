### Inicialitzar repositori
git init

### Configuració de la identitat global
git config --global user.name "diego"
git config --global user.email "diegodiegola33@gmail.com"

### Crear el gitignore abans del primer commit
curl -o .gitignore https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore

## Primer Commit
git add .

### Bug i solució
warning: in the working copy of '.gitignore', LF will be replaced by CRLF the next time Git touches it

git config --global core.autocrlf true 

git status
git commit -m "Initial commit: estructura base del proyecto"