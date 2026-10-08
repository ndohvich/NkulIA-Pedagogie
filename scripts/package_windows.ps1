# scripts/package_windows.ps1
# Construit l'exécutable Windows de NkulIA (mode onedir).
# Corrige un bug P1 relevé lors de la revue de la PR #1 : `npm ci` exige
# un package-lock.json déjà présent, absent d'un clone tout neuf.

$ErrorActionPreference = 'Stop'

Write-Host "== Frontend ==" -ForegroundColor Cyan
Push-Location frontend
if (Test-Path package-lock.json) {
    npm ci
} else {
    npm install
}
npm run build
Pop-Location

Write-Host "== Backend ==" -ForegroundColor Cyan
Push-Location backend
python -m pip install --upgrade pip
pip install -e ".[dev,desktop]"
Pop-Location

Write-Host "== PyInstaller ==" -ForegroundColor Cyan
# `alembic.ddl.sqlite` est chargé par nom au moment des migrations ; `reportlab`
# (polices/ressources du PDF) et `docx` (gabarit par défaut) embarquent des
# fichiers de données que l'analyse statique ne voit pas.
# Les --hidden-import ci-dessous ne sont pas optionnels : uvicorn charge
# ces sous-modules dynamiquement (par nom, à l'exécution), ce
# qu'aucune analyse statique de PyInstaller ne peut détecter seule —
# sans eux, l'exécutable démarre puis plante immédiatement.
pyinstaller `
  --name NkulIA `
  --onedir `
  --noconfirm `
  --add-data "backend;backend" `
  --add-data "frontend/dist;frontend/dist" `
  --hidden-import uvicorn.logging `
  --hidden-import uvicorn.loops.auto `
  --hidden-import uvicorn.protocols.http.auto `
  --hidden-import uvicorn.protocols.websockets.auto `
  --hidden-import uvicorn.lifespan.on `
  --hidden-import alembic.ddl.sqlite `
  --collect-data reportlab `
  --collect-data docx `
  desktop/main.py

Write-Host "Terminé : dist/NkulIA/NkulIA.exe" -ForegroundColor Green
