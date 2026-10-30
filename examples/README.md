# Examples

<div style="border-left: 4px solid #cf222e; padding: 0.5em 1em; background-color: rgba(207, 34, 46, 0.1);">

**Everything in this folder is AI-generated.** The people in `group.jpg` do not exist: the photo was generated from a text prompt with FLUX 3 Image Klein. The costumes and the animation were then produced by the app's own pipeline, FLUX 3 Image Klein for the edit and LTX 2.5 for the image-to-video.

</div>

![Original photo and the three presets](presets.jpg)

| File                                       | Preset              | Content                                                        |
| ------------------------------------------ | ------------------- | -------------------------------------------------------------- |
| [group.jpg](group.jpg)                     | —                   | input photo, 1248×832, five people                             |
| [reveal_vampire.mp4](reveal_vampire.mp4)   | Vampire gala        | 5.5 s reveal: 1.5 s original photo, white flash, animated clip |
| [reveal_witch.mp4](reveal_witch.mp4)       | Witches             | same                                                           |
| [reveal_skeleton.mp4](reveal_skeleton.mp4) | Skeleton face paint | same                                                           |
| [presets.jpg](presets.jpg)                 | all                 | the original and the three edited stills, before animation     |
| [thumbnail.jpg](thumbnail.jpg)             | Skeleton face paint | 1280×720 demo video thumbnail, split before / after            |

The videos are 1620×1080, the frame matching the 3:2 photo (`--format auto`), and use the synthesized reveal sound. They were re-encoded at CRF 24 to keep the repository light; the app writes CRF 18. To reproduce them, run the app on `group.jpg`. The seed is random by default, so your results will differ from these.

<div style="border-left: 4px solid #9a6700; padding: 0.5em 1em; background-color: rgba(154, 103, 0, 0.1);">

The clips show the current limits of the image-to-video step: the camera drifts despite the "static camera" prompt (a zoom-in on Vampire and Skeleton, a zoom-out on Witches), and on Vampire the smiles fade after about 2 s.

</div>
