"""Halloween presets: edit prompt (FLUX 3 Klein) and motion prompt (LTX 2.5 I2V).

The edit prompt is written as the caption of the desired photo; Klein refers to the original photo as
<ref_image_0>. Skin tone is enforced explicitly: "pale porcelain skin" whitened dark skin
(benchmark of Oct 28).
"""

from __future__ import annotations

from dataclasses import dataclass

KEEP_PEOPLE = (
    "Every person keeps their exact natural skin tone, identity, facial features, expression, hairstyle, "
    "accessories and head pose; same body poses, same number of people, same framing and composition."
)
# I2V: static camera, frozen faces. "Frozen group portrait" + "as in the first frame": the only lever that
# kept expressions over 5 s (neither 3 s nor strength 1.0 was enough, tests of Oct 28).
STILL_PEOPLE = (
    "Static camera, no zoom, no pan. A frozen group portrait: the people hold their pose and keep their exact "
    "expressions, with exactly the same faces, headwear and glasses as in the first frame, only subtle blinking."
)


@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    edit_prompt: str
    motion_prompt: str
    # One person in the photo: a plural prompt ("people", "capes", KEEP_PEOPLE) makes Klein add a clone
    # (vampire on a selfie: 0/3 plural, 3/3 singular, tests of Oct 29).
    solo_edit_prompt: str | None = None

    def edit_prompt_for(self, n_faces: int) -> str:
        return self.solo_edit_prompt if n_faces == 1 and self.solo_edit_prompt else self.edit_prompt


PRESETS: dict[str, Preset] = {
    p.key: p
    for p in [
        # Klein benchmark: 3/3 (v2, skin tone preserved).
        Preset(
            "vampire",
            "Vampire gala",
            "A photorealistic photo of the exact same people from <ref_image_0>, now as elegant Halloween vampires "
            "at a gothic gala: small subtle fangs, dark red lips, deep red irises, black and burgundy Victorian "
            f"high-collar capes with lace over their clothes. {KEEP_PEOPLE} Same location as <ref_image_0>, but at "
            "night, lit by warm candlelight with light fog.",
            f"{STILL_PEOPLE} Candle flames flicker, light fog drifts slowly, the capes move slightly in a faint draft.",
            solo_edit_prompt="A photorealistic photo of the exact same person from <ref_image_0>, transformed into an elegant Halloween "
            "vampire at a gothic gala. Show exactly one person only; do not add any extra people, duplicates, or "
            "clones. Preserve the person's exact natural skin tone, facial identity, hairstyle, body type, and overall "
            "resemblance. Add small subtle fangs, dark red lips, deep red irises, and a black and burgundy Victorian "
            "high-collar cape with lace worn over their existing clothes. Same location as <ref_image_0>, but at "
            "night, lit by warm candlelight with light fog.",
        ),
        # Klein benchmark: 2/2 (selfie, street). "coven" added a person, hence "witches" and
        # "no additional people". The hat replaces any headwear (an instruction to the contrary was ignored, removed).
        Preset(
            "witch",
            "Witches",
            "A photorealistic photo of the exact same people from <ref_image_0>, now dressed as Halloween witches: "
            "tall black pointed witch hats with wide brims that never cover the eyes, dark velvet cloaks in deep "
            "purple and black over their clothes, subtle smoky eye makeup, small silver moon and star jewelry. "
            f"{KEEP_PEOPLE[:-1]}; no additional people. Same location as <ref_image_0>, but at dusk, lit by "
            "glowing jack-o'-lanterns with low purple mist.",
            f"{STILL_PEOPLE} The jack-o'-lantern light flickers, purple mist swirls slowly at their feet.",
            solo_edit_prompt="A photorealistic photo of the exact same person from <ref_image_0>, dressed as a Halloween "
            "witch. Show exactly one person only; do not add any extra people, duplicates, or clones. Preserve the person's exact "
            "natural skin tone, facial identity, expression, hairstyle, body type, and overall resemblance. Add a tall "
            "black pointed witch hat with a wide brim that never covers the eyes, a dark velvet cloak in deep purple and "
            "black worn over their existing clothes, subtle smoky eye makeup, and small silver moon and star jewelry. "
            "Same location as <ref_image_0>, but at dusk, lit by glowing jack-o'-lanterns with low purple mist.",
        ),
        # Klein benchmark: 3/3.
        Preset(
            "skeleton",
            "Skeleton face paint",
            "A photorealistic photo of the exact same people from <ref_image_0>, now wearing Day of the Dead "
            "skeleton face paint: white base, black circles around the eyes, a black painted nose tip, painted "
            "teeth lines across the lips, fine black and white swirl details. The paint follows each face's real "
            "features so everyone stays clearly recognizable; every person keeps the same eyes, expression, "
            "hairstyle, head pose, clothes and body pose; same number of people, same framing and composition. "
            "Same location as <ref_image_0>, at dusk with orange Halloween lighting.",
            f"{STILL_PEOPLE} The orange light flickers gently, dry leaves drift slowly through the air.",
            solo_edit_prompt="A photorealistic photo of the exact same person from <ref_image_0>, now wearing Day of the "
            "Dead skeleton face paint. Show exactly one person only; do not add any extra people, duplicates, or clones. Add a white "
            "base, black circles around the eyes, a black painted nose tip, painted teeth lines across the lips, and fine "
            "black and white swirl details. The paint follows the face's real features so the person stays clearly "
            "recognizable; they keep the same eyes, expression, hairstyle, head pose, clothes and body pose, same framing "
            "and composition. Same location as <ref_image_0>, at dusk with orange Halloween lighting.",
        ),
    ]
}
