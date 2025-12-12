from app.schemas.generation import StoryboardModel


def test_storyboard_model_accepts_keyframe_urls():
    storyboard = StoryboardModel.model_validate(
        {
            "frames": [
                {
                    "frame_number": 1,
                    "scene_number": 1,
                    "description": "角色走进房间，停下。",
                    "start_image_url": "https://cdn.example.com/start.png",
                    "end_image_url": "https://cdn.example.com/end.png",
                    "video_url": "https://cdn.example.com/clip.mp4",
                }
            ]
        }
    )

    assert storyboard.frames[0].start_image_url == "https://cdn.example.com/start.png"
    assert storyboard.frames[0].end_image_url == "https://cdn.example.com/end.png"
    assert storyboard.frames[0].video_url == "https://cdn.example.com/clip.mp4"

