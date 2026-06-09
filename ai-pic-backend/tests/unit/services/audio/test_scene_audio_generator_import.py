import subprocess
import sys


def test_scene_audio_generator_imports_without_script_package_cycle() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from app.services.audio.scene_audio_generator "
                "import generate_scene_dialogue_audio; "
                "print(generate_scene_dialogue_audio.__name__)"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "generate_scene_dialogue_audio" in result.stdout
