# ADR-0001 — Inicialización de repositorio, identidad y credenciales

- **Fecha:** 2026-10-14
- **Estado:** Aceptado

## Contexto

El proyecto debía inicializarse sin tocar la identidad global de Git ni la
cuenta personal de GitHub del equipo, vinculando únicamente el repositorio
privado `github.com/valensan18/yacopi-project`.

## Decisión

1. Repositorio local en `C:\Users\DIEGHOST\Documents\yacopi-project`, rama
   `dev` basada sobre el commit inicial de `main` del remoto.
2. Clave SSH dedicada `~/.ssh/id_ed25519_valensan18` (ed25519, sin
   passphrase, comentario `valensan18-yacopi`) y alias de host
   `github-valensan18` con `IdentitiesOnly yes` en `~/.ssh/config` (archivo
   nuevo; no existía configuración previa).
3. `origin = git@github-valensan18:valensan18/yacopi-project.git`.
4. Identidad de autor a nivel de repo (no global): `valensan18` /
   `342352447+valensan18@users.noreply.github.com`. El ID numérico proviene de
   la API pública de GitHub (`users/valensan18` → `id: 342352447`); el formato
   noreply es el oficial de GitHub. Pendiente confirmar "Keep my email
   addresses private" en la cuenta.
5. Datos sensibles fuera del versionado: `data/raw|processed|external|splits`,
   `*.csv`, `*.db`, `.env*`, claves, artefactos ML (ver `.gitignore`).

## Alternativas rechazadas

- Reutilizar la clave personal `id_ed25519`: mezclaría identidades y cuentas.
- Configurar `user.name`/`user.email` global: modificaría la cuenta personal.
- Forzar `push -f` para alinear `main`: innecesario; se rebasó localmente.

## Riesgos

- Si "Keep my email addresses private" no está activo, el noreply puede no
  atribuirse; mitigación: verificar antes del primer push (pendiente #8).

## Pruebas asociadas

- `ssh -T git@github-valensan18` → "Hi valensan18!" (verificado).
- `git ls-remote origin` OK sobre SSH (verificado).
