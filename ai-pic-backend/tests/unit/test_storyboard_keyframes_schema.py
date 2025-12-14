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
                    "start_image_urls": [
                        "https://cdn.example.com/start.png",
                        "https://cdn.example.com/start-2.png",
                    ],
                    "end_image_url": "https://cdn.example.com/end.png",
                    "end_image_urls": [
                        "https://cdn.example.com/end.png",
                        "https://cdn.example.com/end-2.png",
                    ],
                    "video_url": "https://cdn.example.com/clip.mp4",
                    "video_thumbnail_url": "https://cdn.example.com/thumb.png",
                    "video_url_original": "https://provider.example.com/clip.mp4",
                    "video_last_frame_url": "https://cdn.example.com/last.png",
                    "video_generation": {
                        "provider": "volcengine",
                        "model": "doubao",
                        "last_frame_url": "https://cdn.example.com/last.png",
                    },
                }
            ]
        }
    )

    assert storyboard.frames[0].start_image_url == "https://cdn.example.com/start.png"
    assert storyboard.frames[0].start_image_urls == [
        "https://cdn.example.com/start.png",
        "https://cdn.example.com/start-2.png",
    ]
    assert storyboard.frames[0].end_image_url == "https://cdn.example.com/end.png"
    assert storyboard.frames[0].end_image_urls == [
        "https://cdn.example.com/end.png",
        "https://cdn.example.com/end-2.png",
    ]
    assert storyboard.frames[0].video_url == "https://cdn.example.com/clip.mp4"
    assert storyboard.frames[0].video_thumbnail_url == "https://cdn.example.com/thumb.png"
    assert storyboard.frames[0].video_url_original == "https://provider.example.com/clip.mp4"
    assert storyboard.frames[0].video_last_frame_url == "https://cdn.example.com/last.png"
    assert storyboard.frames[0].video_generation["provider"] == "volcengine"
