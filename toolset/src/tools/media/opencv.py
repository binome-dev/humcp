"""OpenCV image processing tools for resizing and format conversion."""

from __future__ import annotations

import logging
from pathlib import Path

from src.humcp.decorator import tool
from src.tools.media.schemas import (
    OpenCVConvertData,
    OpenCVConvertResponse,
    OpenCVCropData,
    OpenCVCropResponse,
    OpenCVResizeData,
    OpenCVResizeResponse,
    OpenCVRotateData,
    OpenCVRotateResponse,
)

logger = logging.getLogger("humcp.tools.opencv")

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


@tool()
async def opencv_resize_image(
    input_path: str,
    output_path: str,
    width: int,
    height: int,
) -> OpenCVResizeResponse:
    """Resize an image to the specified dimensions using OpenCV.

    Args:
        input_path: Path to the input image file.
        output_path: Path where the resized image will be saved.
        width: Target width in pixels.
        height: Target height in pixels.

    Returns:
        Paths and dimensions of the resized image.
    """
    try:
        if not input_path.strip() or not output_path.strip():
            return OpenCVResizeResponse(
                success=False, error="Input and output paths must not be empty."
            )

        if width < 1 or height < 1:
            return OpenCVResizeResponse(
                success=False, error="Width and height must be at least 1 pixel."
            )

        input_file = Path(input_path)
        if not input_file.exists():
            return OpenCVResizeResponse(
                success=False, error=f"Input file not found: {input_path}"
            )

        if input_file.suffix.lower() not in SUPPORTED_FORMATS:
            return OpenCVResizeResponse(
                success=False,
                error=f"Unsupported input format '{input_file.suffix}'. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            )

        output_file = Path(output_path)
        if output_file.suffix.lower() not in SUPPORTED_FORMATS:
            return OpenCVResizeResponse(
                success=False,
                error=f"Unsupported output format '{output_file.suffix}'. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            )

        try:
            import cv2
        except ImportError:
            return OpenCVResizeResponse(
                success=False,
                error="opencv-python package is required. Install with: pip install opencv-python",
            )

        logger.info("OpenCV resizing %s to %dx%d", input_path, width, height)

        img = cv2.imread(input_path)
        if img is None:
            return OpenCVResizeResponse(
                success=False, error=f"Failed to read image: {input_path}"
            )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        resized = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
        success = cv2.imwrite(output_path, resized)

        if not success:
            return OpenCVResizeResponse(
                success=False, error=f"Failed to write resized image to: {output_path}"
            )

        logger.info("OpenCV resize complete output=%s", output_path)

        return OpenCVResizeResponse(
            success=True,
            data=OpenCVResizeData(
                input_path=input_path,
                output_path=output_path,
                width=width,
                height=height,
            ),
        )
    except Exception as e:
        logger.exception("OpenCV resize failed")
        return OpenCVResizeResponse(
            success=False, error=f"OpenCV resize failed: {str(e)}"
        )


@tool()
async def opencv_convert_format(
    input_path: str,
    output_path: str,
) -> OpenCVConvertResponse:
    """Convert an image from one format to another using OpenCV.

    The output format is determined by the file extension of output_path.

    Args:
        input_path: Path to the input image file.
        output_path: Path where the converted image will be saved.
            The file extension determines the output format
            (e.g., ".png", ".jpg", ".bmp", ".webp").

    Returns:
        Paths and format information of the converted image.
    """
    try:
        if not input_path.strip() or not output_path.strip():
            return OpenCVConvertResponse(
                success=False, error="Input and output paths must not be empty."
            )

        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            return OpenCVConvertResponse(
                success=False, error=f"Input file not found: {input_path}"
            )

        input_ext = input_file.suffix.lower()
        output_ext = output_file.suffix.lower()

        if input_ext not in SUPPORTED_FORMATS:
            return OpenCVConvertResponse(
                success=False,
                error=f"Unsupported input format '{input_ext}'. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            )

        if output_ext not in SUPPORTED_FORMATS:
            return OpenCVConvertResponse(
                success=False,
                error=f"Unsupported output format '{output_ext}'. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            )

        try:
            import cv2
        except ImportError:
            return OpenCVConvertResponse(
                success=False,
                error="opencv-python package is required. Install with: pip install opencv-python",
            )

        logger.info(
            "OpenCV converting %s (%s) to %s (%s)",
            input_path,
            input_ext,
            output_path,
            output_ext,
        )

        img = cv2.imread(input_path)
        if img is None:
            return OpenCVConvertResponse(
                success=False, error=f"Failed to read image: {input_path}"
            )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        success = cv2.imwrite(output_path, img)

        if not success:
            return OpenCVConvertResponse(
                success=False,
                error=f"Failed to write converted image to: {output_path}",
            )

        logger.info("OpenCV conversion complete output=%s", output_path)

        return OpenCVConvertResponse(
            success=True,
            data=OpenCVConvertData(
                input_path=input_path,
                output_path=output_path,
                input_format=input_ext.lstrip("."),
                output_format=output_ext.lstrip("."),
            ),
        )
    except Exception as e:
        logger.exception("OpenCV conversion failed")
        return OpenCVConvertResponse(
            success=False, error=f"OpenCV conversion failed: {str(e)}"
        )


@tool()
async def opencv_rotate_image(
    input_path: str,
    output_path: str,
    angle: float,
) -> OpenCVRotateResponse:
    """Rotate an image by a specified angle using OpenCV.

    The image is rotated around its center. The output canvas is expanded
    to fit the entire rotated image without cropping.

    Args:
        input_path: Path to the input image file.
        output_path: Path where the rotated image will be saved.
        angle: Rotation angle in degrees (positive = counter-clockwise).

    Returns:
        Path to the rotated image, angle, and original dimensions.
    """
    try:
        if not input_path.strip() or not output_path.strip():
            return OpenCVRotateResponse(
                success=False, error="Input and output paths must not be empty."
            )

        input_file = Path(input_path)
        if not input_file.exists():
            return OpenCVRotateResponse(
                success=False, error=f"Input file not found: {input_path}"
            )

        if input_file.suffix.lower() not in SUPPORTED_FORMATS:
            return OpenCVRotateResponse(
                success=False,
                error=f"Unsupported input format '{input_file.suffix}'. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            )

        output_file = Path(output_path)
        if output_file.suffix.lower() not in SUPPORTED_FORMATS:
            return OpenCVRotateResponse(
                success=False,
                error=f"Unsupported output format '{output_file.suffix}'. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            )

        try:
            import cv2
            import numpy as np
        except ImportError:
            return OpenCVRotateResponse(
                success=False,
                error="opencv-python and numpy packages are required. Install with: pip install opencv-python numpy",
            )

        logger.info("OpenCV rotating %s by %.1f degrees", input_path, angle)

        img = cv2.imread(input_path)
        if img is None:
            return OpenCVRotateResponse(
                success=False, error=f"Failed to read image: {input_path}"
            )

        h, w = img.shape[:2]
        original_size = f"{w}x{h}"
        center = (w / 2, h / 2)

        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        cos_val = np.abs(rotation_matrix[0, 0])
        sin_val = np.abs(rotation_matrix[0, 1])
        new_w = int(h * sin_val + w * cos_val)
        new_h = int(h * cos_val + w * sin_val)

        rotation_matrix[0, 2] += (new_w / 2) - center[0]
        rotation_matrix[1, 2] += (new_h / 2) - center[1]

        rotated = cv2.warpAffine(img, rotation_matrix, (new_w, new_h))

        output_file.parent.mkdir(parents=True, exist_ok=True)
        success = cv2.imwrite(output_path, rotated)

        if not success:
            return OpenCVRotateResponse(
                success=False, error=f"Failed to write rotated image to: {output_path}"
            )

        logger.info("OpenCV rotation complete output=%s", output_path)

        return OpenCVRotateResponse(
            success=True,
            data=OpenCVRotateData(
                output_path=output_path,
                angle=angle,
                original_size=original_size,
            ),
        )
    except Exception as e:
        logger.exception("OpenCV rotation failed")
        return OpenCVRotateResponse(
            success=False, error=f"OpenCV rotation failed: {str(e)}"
        )


@tool()
async def opencv_crop_image(
    input_path: str,
    output_path: str,
    x: int,
    y: int,
    width: int,
    height: int,
) -> OpenCVCropResponse:
    """Crop a region from an image using OpenCV.

    Args:
        input_path: Path to the input image file.
        output_path: Path where the cropped image will be saved.
        x: X coordinate of the top-left corner of the crop region.
        y: Y coordinate of the top-left corner of the crop region.
        width: Width of the crop region in pixels.
        height: Height of the crop region in pixels.

    Returns:
        Path to the cropped image, crop region, and original dimensions.
    """
    try:
        if not input_path.strip() or not output_path.strip():
            return OpenCVCropResponse(
                success=False, error="Input and output paths must not be empty."
            )

        if width < 1 or height < 1:
            return OpenCVCropResponse(
                success=False, error="Crop width and height must be at least 1 pixel."
            )

        if x < 0 or y < 0:
            return OpenCVCropResponse(
                success=False, error="Crop x and y coordinates must not be negative."
            )

        input_file = Path(input_path)
        if not input_file.exists():
            return OpenCVCropResponse(
                success=False, error=f"Input file not found: {input_path}"
            )

        if input_file.suffix.lower() not in SUPPORTED_FORMATS:
            return OpenCVCropResponse(
                success=False,
                error=f"Unsupported input format '{input_file.suffix}'. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            )

        output_file = Path(output_path)
        if output_file.suffix.lower() not in SUPPORTED_FORMATS:
            return OpenCVCropResponse(
                success=False,
                error=f"Unsupported output format '{output_file.suffix}'. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            )

        try:
            import cv2
        except ImportError:
            return OpenCVCropResponse(
                success=False,
                error="opencv-python package is required. Install with: pip install opencv-python",
            )

        logger.info(
            "OpenCV cropping %s region=(%d,%d,%d,%d)", input_path, x, y, width, height
        )

        img = cv2.imread(input_path)
        if img is None:
            return OpenCVCropResponse(
                success=False, error=f"Failed to read image: {input_path}"
            )

        h, w = img.shape[:2]
        original_size = f"{w}x{h}"

        if x + width > w or y + height > h:
            return OpenCVCropResponse(
                success=False,
                error=f"Crop region ({x},{y},{width},{height}) exceeds image bounds ({w}x{h}).",
            )

        cropped = img[y : y + height, x : x + width]

        output_file.parent.mkdir(parents=True, exist_ok=True)
        success = cv2.imwrite(output_path, cropped)

        if not success:
            return OpenCVCropResponse(
                success=False, error=f"Failed to write cropped image to: {output_path}"
            )

        logger.info("OpenCV crop complete output=%s", output_path)

        return OpenCVCropResponse(
            success=True,
            data=OpenCVCropData(
                output_path=output_path,
                crop_region=f"({x}, {y}, {width}, {height})",
                original_size=original_size,
            ),
        )
    except Exception as e:
        logger.exception("OpenCV crop failed")
        return OpenCVCropResponse(success=False, error=f"OpenCV crop failed: {str(e)}")
