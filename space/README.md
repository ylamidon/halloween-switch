---
title: Halloween Switch
emoji: 🎃
colorFrom: orange
colorTo: purple
sdk: gradio
sdk_version: 6.31.0
python_version: "3.12"
app_file: app.py
pinned: false
license: mit
short_description: Group photo → Halloween costume reveal video
---

# 🎃 Halloween Switch

Upload a group photo, pick a costume, get a short **before → flash → after** video. FLUX 3 Image Klein edits the costumes, LTX 2.5 animates them, both on [Comfy Cloud](https://cloud.comfy.org); FFmpeg assembles the reveal. Open weights only. A job takes a few minutes, one at a time.

Source code, local install and model downloads: see the GitHub repository.

Space secrets: `COMFY_URL=https://cloud.comfy.org`, `COMFY_API_KEY`, `APP_AUTH=<user>:<password>`.
