"""Pydantic output schemas for media tools."""

from pydantic import BaseModel, Field

from src.humcp.schemas import ToolResponse

# =============================================================================
# Giphy Schemas
# =============================================================================


class GiphyGif(BaseModel):
    """A single GIF result from Giphy."""

    url: str = Field(..., description="URL of the original GIF")
    alt_text: str | None = Field(None, description="Alt text for the GIF")
    title: str | None = Field(None, description="Title of the GIF")


class GiphySearchData(BaseModel):
    """Output data for giphy_search tool."""

    query: str = Field(..., description="The search query that was executed")
    gifs: list[GiphyGif] = Field(default_factory=list, description="List of found GIFs")
    total_count: int = Field(0, description="Total number of results available")


class GiphyTrendingData(BaseModel):
    """Output data for giphy_trending tool."""

    gifs: list[GiphyGif] = Field(
        default_factory=list, description="List of trending GIFs"
    )


# =============================================================================
# Unsplash Schemas
# =============================================================================


class UnsplashPhoto(BaseModel):
    """A single photo result from Unsplash."""

    id: str = Field(..., description="Unique photo identifier")
    description: str | None = Field(None, description="Photo description")
    width: int | None = Field(None, description="Photo width in pixels")
    height: int | None = Field(None, description="Photo height in pixels")
    color: str | None = Field(None, description="Dominant color hex code")
    urls: dict[str, str | None] = Field(
        default_factory=dict, description="Photo URLs at different sizes"
    )
    author_name: str | None = Field(None, description="Photographer name")
    author_username: str | None = Field(None, description="Photographer username")
    likes: int | None = Field(None, description="Number of likes")


class UnsplashSearchData(BaseModel):
    """Output data for unsplash_search_photos tool."""

    query: str = Field(..., description="The search query that was executed")
    total: int = Field(0, description="Total number of results available")
    photos: list[UnsplashPhoto] = Field(
        default_factory=list, description="List of photo results"
    )


class UnsplashRandomPhotoData(BaseModel):
    """Output data for unsplash_get_random_photo tool."""

    query: str | None = Field(None, description="Optional query used to filter")
    photos: list[UnsplashPhoto] = Field(
        default_factory=list, description="List of random photos"
    )


# =============================================================================
# DALL-E Schemas
# =============================================================================


class DalleGeneratedImage(BaseModel):
    """A single generated image from DALL-E."""

    url: str = Field(..., description="URL of the generated image")
    revised_prompt: str | None = Field(
        None, description="The revised prompt used by DALL-E"
    )


class DalleGenerateImageData(BaseModel):
    """Output data for dalle_generate_image tool."""

    prompt: str = Field(..., description="The original prompt")
    images: list[DalleGeneratedImage] = Field(
        default_factory=list, description="List of generated images"
    )


# =============================================================================
# Replicate Schemas
# =============================================================================


class ReplicateOutput(BaseModel):
    """A single output from a Replicate model run."""

    url: str = Field(..., description="URL of the generated media")
    media_type: str = Field(..., description="Type of media (image or video)")


class ReplicateRunData(BaseModel):
    """Output data for replicate_run_model tool."""

    model: str = Field(..., description="The model that was run")
    outputs: list[ReplicateOutput] = Field(
        default_factory=list, description="List of generated outputs"
    )


class ReplicatePredictionData(BaseModel):
    """Output data for replicate_get_prediction tool."""

    prediction_id: str = Field(..., description="The prediction ID")
    status: str = Field(..., description="Current status of the prediction")
    output: list[str] | None = Field(None, description="Output URLs when completed")
    error: str | None = Field(None, description="Error message if failed")


# =============================================================================
# LumaLab Schemas
# =============================================================================


class LumaLabVideoData(BaseModel):
    """Output data for lumalab_generate_video tool."""

    prompt: str = Field(..., description="The prompt used for generation")
    video_url: str | None = Field(None, description="URL of the generated video")
    state: str = Field(..., description="Current state of the generation")
    generation_id: str | None = Field(None, description="Luma generation ID")


# =============================================================================
# Fal Schemas
# =============================================================================


class FalOutput(BaseModel):
    """A single output from a Fal model run."""

    url: str = Field(..., description="URL of the generated media")
    media_type: str = Field(..., description="Type of media (image or video)")


class FalRunData(BaseModel):
    """Output data for fal_run_model tool."""

    model_id: str = Field(..., description="The Fal model that was run")
    outputs: list[FalOutput] = Field(
        default_factory=list, description="List of generated outputs"
    )


# =============================================================================
# MoviePy Schemas
# =============================================================================


class MoviePyVideoData(BaseModel):
    """Output data for moviepy_create_video tool."""

    output_path: str = Field(..., description="Path to the created video file")
    num_images: int = Field(..., description="Number of images used")
    fps: int = Field(..., description="Frames per second of the output video")
    duration_per_image: float = Field(
        ..., description="Duration each image is shown in seconds"
    )


# =============================================================================
# ModelsLab Schemas
# =============================================================================


class ModelsLabGenerateData(BaseModel):
    """Output data for models_labs_generate_image tool."""

    prompt: str = Field(..., description="The prompt used for generation")
    status: str = Field(..., description="Generation status")
    output_urls: list[str] = Field(
        default_factory=list, description="URLs of generated media"
    )
    eta: int | None = Field(None, description="Estimated time in seconds until ready")


# =============================================================================
# NanoBanana Schemas
# =============================================================================


class NanoBananaRunData(BaseModel):
    """Output data for nano_banana_run tool."""

    model_name: str = Field(..., description="The model that was run")
    output_urls: list[str] = Field(
        default_factory=list, description="URLs of generated outputs"
    )
    status: str = Field(..., description="Status of the generation")


# =============================================================================
# OpenCV Schemas
# =============================================================================


class OpenCVResizeData(BaseModel):
    """Output data for opencv_resize_image tool."""

    input_path: str = Field(..., description="Path to the input image")
    output_path: str = Field(..., description="Path to the resized image")
    width: int = Field(..., description="New width in pixels")
    height: int = Field(..., description="New height in pixels")


class OpenCVConvertData(BaseModel):
    """Output data for opencv_convert_format tool."""

    input_path: str = Field(..., description="Path to the input image")
    output_path: str = Field(..., description="Path to the converted image")
    input_format: str = Field(..., description="Original image format")
    output_format: str = Field(..., description="Target image format")


class GiphyRandomData(BaseModel):
    """Output data for giphy_random tool."""

    tag: str | None = Field(None, description="Tag used to filter the random GIF")
    gif: GiphyGif = Field(..., description="The random GIF result")


class GiphyStickerSearchData(BaseModel):
    """Output data for giphy sticker search."""

    query: str = Field(..., description="The search query that was executed")
    stickers: list[GiphyGif] = Field(
        default_factory=list, description="List of found stickers"
    )
    total_count: int = Field(0, description="Total number of results available")


class UnsplashGetPhotoData(BaseModel):
    """Output data for unsplash_get_photo tool."""

    photo: UnsplashPhoto = Field(..., description="The retrieved photo")


class ReplicateSearchModelItem(BaseModel):
    """A single model result from Replicate search."""

    owner: str = Field(..., description="Owner of the model")
    name: str = Field(..., description="Name of the model")
    description: str = Field("", description="Description of the model")
    url: str = Field(..., description="URL of the model on Replicate")
    run_count: int = Field(0, description="Number of times the model has been run")


class ReplicateSearchData(BaseModel):
    """Output data for replicate_search_models tool."""

    query: str = Field(..., description="The search query that was executed")
    models: list[ReplicateSearchModelItem] = Field(
        default_factory=list, description="List of matching models"
    )


class OpenCVRotateData(BaseModel):
    """Output data for opencv_rotate_image tool."""

    output_path: str = Field(..., description="Path to the rotated image")
    angle: float = Field(..., description="Rotation angle in degrees")
    original_size: str = Field(..., description="Original image dimensions (WxH)")


class OpenCVCropData(BaseModel):
    """Output data for opencv_crop_image tool."""

    output_path: str = Field(..., description="Path to the cropped image")
    crop_region: str = Field(..., description="Crop region as (x, y, width, height)")
    original_size: str = Field(..., description="Original image dimensions (WxH)")


class MoviePyTrimData(BaseModel):
    """Output data for moviepy_trim_video tool."""

    output_path: str = Field(..., description="Path to the trimmed video file")
    start_time: float = Field(..., description="Start time of the trim in seconds")
    end_time: float = Field(..., description="End time of the trim in seconds")
    duration: float = Field(..., description="Duration of the trimmed video in seconds")


# =============================================================================
# Response Wrappers (inheriting from ToolResponse[T])
# =============================================================================


class GiphySearchResponse(ToolResponse[GiphySearchData]):
    """Response schema for giphy_search tool."""

    pass


class GiphyTrendingResponse(ToolResponse[GiphyTrendingData]):
    """Response schema for giphy_trending tool."""

    pass


class UnsplashSearchResponse(ToolResponse[UnsplashSearchData]):
    """Response schema for unsplash_search_photos tool."""

    pass


class UnsplashRandomPhotoResponse(ToolResponse[UnsplashRandomPhotoData]):
    """Response schema for unsplash_get_random_photo tool."""

    pass


class DalleGenerateImageResponse(ToolResponse[DalleGenerateImageData]):
    """Response schema for dalle_generate_image tool."""

    pass


class ReplicateRunResponse(ToolResponse[ReplicateRunData]):
    """Response schema for replicate_run_model tool."""

    pass


class ReplicatePredictionResponse(ToolResponse[ReplicatePredictionData]):
    """Response schema for replicate_get_prediction tool."""

    pass


class LumaLabVideoResponse(ToolResponse[LumaLabVideoData]):
    """Response schema for lumalab_generate_video tool."""

    pass


class FalRunResponse(ToolResponse[FalRunData]):
    """Response schema for fal_run_model tool."""

    pass


class MoviePyVideoResponse(ToolResponse[MoviePyVideoData]):
    """Response schema for moviepy_create_video tool."""

    pass


class ModelsLabGenerateResponse(ToolResponse[ModelsLabGenerateData]):
    """Response schema for models_labs_generate_image tool."""

    pass


class NanoBananaRunResponse(ToolResponse[NanoBananaRunData]):
    """Response schema for nano_banana_run tool."""

    pass


class OpenCVResizeResponse(ToolResponse[OpenCVResizeData]):
    """Response schema for opencv_resize_image tool."""

    pass


class OpenCVConvertResponse(ToolResponse[OpenCVConvertData]):
    """Response schema for opencv_convert_format tool."""

    pass


class GiphyRandomResponse(ToolResponse[GiphyRandomData]):
    """Response schema for giphy_random tool."""

    pass


class GiphyStickerSearchResponse(ToolResponse[GiphyStickerSearchData]):
    """Response schema for giphy sticker search tool."""

    pass


class UnsplashGetPhotoResponse(ToolResponse[UnsplashGetPhotoData]):
    """Response schema for unsplash_get_photo tool."""

    pass


class ReplicateSearchResponse(ToolResponse[ReplicateSearchData]):
    """Response schema for replicate_search_models tool."""

    pass


class OpenCVRotateResponse(ToolResponse[OpenCVRotateData]):
    """Response schema for opencv_rotate_image tool."""

    pass


class OpenCVCropResponse(ToolResponse[OpenCVCropData]):
    """Response schema for opencv_crop_image tool."""

    pass


class MoviePyTrimResponse(ToolResponse[MoviePyTrimData]):
    """Response schema for moviepy_trim_video tool."""

    pass
