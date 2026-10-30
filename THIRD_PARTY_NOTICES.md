# Third-party notices

Halloween Switch's own code is MIT-licensed (see [LICENSE](LICENSE)). The repository contains **no generative model weights** (the only bundled weights are the 227 KB YuNet face detector, MIT, see below): the app sends ComfyUI workflows (`workflows/*.json`) to a ComfyUI server, local or [Comfy Cloud](https://cloud.comfy.org), which loads the models below. Whoever runs that server downloads the weights and must accept their licenses. The reveal sound effect is synthesized by FFmpeg (`pipeline/reveal.py`), so no audio asset is bundled.

<div style="border-left: 4px solid #cf222e; padding: 0.5em 1em; background-color: rgba(207, 34, 46, 0.1);">

FLUX 3 Image Klein and LTX 2.5 are **not** under an OSI open-source license; the FLUX.2 VAE, Qwen3-VL and Gemma 4 are under Apache 2.0. The MIT license covers this repository's code only, not the models or what you do with them. The LTX-2.x Community License (Attachment A) requires you to disclose that outputs are machine-generated; the FLUX Kommunity License requires it to the extent applicable law does. Both forbid, among other uses, impersonating someone without consent. Only process photos of people who have agreed to it.

</div>

## Models (called through ComfyUI, not distributed)

| Component                                                                                                                            | Files referenced in `workflows/`                                                                                    | License                                                                                                         | Commercial use                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| [FLUX 3 Image Klein](https://huggingface.co/black-forest-labs/flux-3-image-klein), Black Forest Labs (photo edit)                    | `flux3-image-klein-base-int8-convrot`                                                                               | [FLUX Kommunity License v1.0](https://huggingface.co/black-forest-labs/flux-3-image-klein/blob/main/LICENSE.md) | free under US$5M annual revenue (affiliates included); otherwise see [bfl.ai/licensing](https://bfl.ai/licensing) |
| [FLUX.2 VAE](https://huggingface.co/black-forest-labs/FLUX.2-VAE), Black Forest Labs (Klein VAE)                                     | `flux2-vae`                                                                                                         | Apache 2.0                                                                                                      | yes                                                                                                               |
| [Qwen3-VL 4B Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct), Alibaba (Klein text encoder)                               | `qwen3vl_4b_int8_convrot`                                                                                           | Apache 2.0                                                                                                      | yes                                                                                                               |
| [LTX 2.5](https://huggingface.co/Lightricks/LTX-2.5), Lightricks (image-to-video)                                                    | `ltx-2.5-22b-distilled-transformer`, `ltx-2.5-video-vae`, `ltx-2.5-audio-vae`, `ltx-2.5-latent-spatial-upscaler-x2` | [LTX-2.x Community License](https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x)                          | free under US$10M annual revenue (affiliates included); otherwise a paid agreement                                |
| [Gemma 4](https://opensource.googleblog.com/2026/03/gemma-4-expanding-the-gemmaverse-with-apache-20.html), Google (LTX text encoder) | `gemma4-12b-with-proj-ltx-2.5`                                                                                      | Apache 2.0 for the Gemma 4 weights; LTX projections: see below                                                  | see below                                                                                                         |

The `int8-convrot` files are quantized repackagings for ComfyUI; the license of the original model applies.

<div style="border-left: 4px solid #9a6700; padding: 0.5em 1em; background-color: rgba(154, 103, 0, 0.1);">

`gemma4-12b-with-proj-ltx-2.5` is distributed by Lightricks in the [LTX-2.5 repository](https://huggingface.co/Lightricks/LTX-2.5) and bundles LTX projection layers with the Gemma 4 weights. Gemma 4's Apache 2.0 license covers the base model only; it does not establish the license of these additions, which may fall under the LTX-2.x Community License. Treat the whole file as subject to both until Lightricks states otherwise.

</div>

<div style="border-left: 4px solid #9a6700; padding: 0.5em 1em; background-color: rgba(154, 103, 0, 0.1);">

FLUX 3 Image Klein: "This FLUX Model is licensed by Black Forest Labs Inc. under the FLUX Kommunity License. Copyright Black Forest Labs Inc." FLUX is a trademark of Black Forest Labs; LTX is a trademark of Lightricks. They are named here only to describe the models used. This project is not affiliated with or endorsed by either company.

</div>

## Software dependencies

| Package                                              | Role                                                                       | License                                   |
| ---------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------- |
| [Gradio](https://github.com/gradio-app/gradio)       | web UI                                                                     | Apache 2.0                                |
| [HTTPX](https://github.com/encode/httpx)             | ComfyUI HTTP client                                                        | BSD 3-Clause                              |
| [Pillow](https://github.com/python-pillow/Pillow)    | EXIF stripping, resizing                                                   | MIT-CMU (HPND)                            |
| [OpenCV](https://github.com/opencv/opencv)           | face count (1 person vs. group) to pick the edit prompt                    | Apache 2.0                                |
| [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) | face detector weights, bundled: `pipeline/models/face_detection_yunet_2023mar.onnx` | MIT, © 2020 Shiqi Yu ([text](pipeline/models/LICENSE-yunet)) |
| [FFmpeg](https://ffmpeg.org/legal.html)              | reveal video and sound effect; external binary, neither bundled nor linked | LGPL 2.1+ (GPL 2+ depending on the build) |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | inference server, called over HTTP                                         | GPL 3.0                                   |

Licenses are summarized as of 29 October 2026. This is not legal advice: the linked license texts are authoritative.
