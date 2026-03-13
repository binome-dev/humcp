"""MoviePy video creation tool for assembling images into a video."""

from __future__ import annotations

import logging
from pathlib import Path

from src.humcp.decorator import tool
from src.tools.media.schemas import (
    MoviePyTrimData,
    MoviePyTrimResponse,
    MoviePyVideoData,
    MoviePyVideoResponse,
)

logger = logging.getLogger("humcp.tools.moviepy_video")


@tool()
async def moviepy_create_video(
    image_paths: list[str],
    output_path: str,
    fps: int = 24,
    duration_per_image: float = 2.0,
) -> MoviePyVideoResponse:
    """Create a video from a sequence of images using MoviePy.

    Args:
        image_paths: List of file paths to images to include in the video.
        output_path: Path where the output video file will be saved (e.g., "output.mp4").
        fps: Frames per second of the output video. Default: 24.
        duration_per_image: Duration in seconds each image is displayed. Default: 2.0.

    Returns:
        Path to the created video file and metadata.
    """
    try:
        if not image_paths:
            return MoviePyVideoResponse(
                success=False, error="image_paths must not be empty."
            )

        if not output_path.strip():
            return MoviePyVideoResponse(
                success=False, error="output_path must not be empty."
            )

        if fps < 1:
            return MoviePyVideoResponse(success=False, error="fps must be at least 1.")

        if duration_per_image <= 0:
            return MoviePyVideoResponse(
                success=False, error="duration_per_image must be positive."
            )

        missing = [p for p in image_paths if not Path(p).exists()]
        if missing:
            return MoviePyVideoResponse(
                success=False,
                error=f"Image files not found: {', '.join(missing)}",
            )

        try:
            from moviepy import ImageClip, concatenate_videoclips
        except ImportError:
            return MoviePyVideoResponse(
                success=False,
                error="moviepy package is required. Install with: pip install moviepy",
            )

        logger.info(
            "MoviePy creating video images=%d fps=%d duration_per_image=%.1f",
            len(image_paths),
            fps,
            duration_per_image,
        )

        clips = []
        for img_path in image_paths:
            clip = ImageClip(img_path).with_duration(duration_per_image)
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video.write_videofile(
            output_path,
            fps=fps,
            codec="libx264",
            audio=False,
        )

        for clip in clips:
            clip.close()
        video.close()

        logger.info("MoviePy video created at %s", output_path)

        return MoviePyVideoResponse(
            success=True,
            data=MoviePyVideoData(
                output_path=output_path,
                num_images=len(image_paths),
                fps=fps,
                duration_per_image=duration_per_image,
            ),
        )
    except Exception as e:
        logger.exception("MoviePy video creation failed")
        return MoviePyVideoResponse(
            success=False, error=f"MoviePy video creation failed: {str(e)}"
        )


@tool()
async def moviepy_trim_video(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
) -> MoviePyTrimResponse:
    """Trim a video to a specified time range using MoviePy.

    Args:
        input_path: Path to the input video file.
        output_path: Path where the trimmed video will be saved (e.g., "trimmed.mp4").
        start_time: Start time in seconds for the trim.
        end_time: End time in seconds for the trim.

    Returns:
        Path to the trimmed video file and trim metadata.
    """
    try:
        if not input_path.strip() or not output_path.strip():
            return MoviePyTrimResponse(
                success=False, error="Input and output paths must not be empty."
            )

        if start_time < 0:
            return MoviePyTrimResponse(
                success=False, error="start_time must not be negative."
            )

        if end_time <= start_time:
            return MoviePyTrimResponse(
                success=False, error="end_time must be greater than start_time."
            )

        input_file = Path(input_path)
        if not input_file.exists():
            return MoviePyTrimResponse(
                success=False, error=f"Input file not found: {input_path}"
            )

        try:
            from moviepy import VideoFileClip
        except ImportError:
            return MoviePyTrimResponse(
                success=False,
                error="moviepy package is required. Install with: pip install moviepy",
            )

        logger.info(
            "MoviePy trimming %s from %.1fs to %.1fs",
            input_path,
            start_time,
            end_time,
        )

        video = VideoFileClip(input_path)

        if end_time > video.duration:
            video.close()
            return MoviePyTrimResponse(
                success=False,
                error=f"end_time ({end_time}s) exceeds video duration ({video.duration:.1f}s).",
            )

        trimmed = video.subclipped(start_time, end_time)
        duration = end_time - start_time

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        trimmed.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
        )

        trimmed.close()
        video.close()

        logger.info(
            "MoviePy trim complete output=%s duration=%.1fs", output_path, duration
        )

        return MoviePyTrimResponse(
            success=True,
            data=MoviePyTrimData(
                output_path=output_path,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
            ),
        )
    except Exception as e:
        logger.exception("MoviePy trim failed")
        return MoviePyTrimResponse(
            success=False, error=f"MoviePy trim failed: {str(e)}"
        )
