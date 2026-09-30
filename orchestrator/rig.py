"""Auto-rig placeholder.

Does not call Mixamo. Writes a humanoid bone map Unity can retarget against
a locally downloaded idle/walk/run/attack FBX set.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HUMANOID_BONES = {
    "Hips": "hips",
    "Spine": "spine",
    "Chest": "chest",
    "Neck": "neck",
    "Head": "head",
    "LeftUpperArm": "arm_l",
    "LeftLowerArm": "forearm_l",
    "LeftHand": "hand_l",
    "RightUpperArm": "arm_r",
    "RightLowerArm": "forearm_r",
    "RightHand": "hand_r",
    "LeftUpperLeg": "thigh_l",
    "LeftLowerLeg": "shin_l",
    "LeftFoot": "foot_l",
    "RightUpperLeg": "thigh_r",
    "RightLowerLeg": "shin_r",
    "RightFoot": "foot_r",
}

ANIM_SET = ("idle", "walk", "run", "attack")


def write_rig(mesh_path: str, out_dir: Path, hero: dict[str, Any]) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rig = {
        "tool": "local-humanoid-map",
        "notes": (
            "Prefer Tripo built-in rigging or an open-source auto-rigger when available. "
            "Do not use live Mixamo. Drop a one-time idle/walk/run/attack FBX set into "
            "unity-templates/Shared/Animations/."
        ),
        "mesh": mesh_path,
        "humanoid": HUMANOID_BONES,
        "animations_expected": list(ANIM_SET),
        "export": "fbx",
        "hero": hero.get("name"),
    }
    path = out_dir / "hero.rig.json"
    path.write_text(json.dumps(rig, indent=2), encoding="utf-8")
    # FBX is binary; Unity import happens later. We keep OBJ + rig map as the
    # safe artifact, and a sidecar that BatchBuild copies into StreamingAssets.
    sidecar = out_dir / "hero.fbx.txt"
    sidecar.write_text(
        "Placeholder. Replace with a real FBX from the auto-rigger.\n"
        "Unity Humanoid retargeting will apply the local animation set.\n",
        encoding="utf-8",
    )
    return {"rig_json": str(path), "fbx_placeholder": str(sidecar), "source": "local-humanoid-map"}
