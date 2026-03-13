---
name: media-tools
description: Media generation and manipulation tools for creating images, videos, and GIFs. Use when the user needs to generate, search for, or transform visual media content.
---

# Media Tools

Tools for generating and manipulating media content including images, videos, and GIFs.

## Available Tools

### Image Generation
- **dalle_generate_image** - Generate images using OpenAI DALL-E
- **models_labs_generate_image** - Generate images via ModelsLab API
- **nano_banana_run** - Generate media via NanoBanana/Banana.dev API

### Image Search
- **unsplash_search_photos** - Search Unsplash for high-quality royalty-free photos
- **unsplash_get_random_photo** - Get random photos from Unsplash
- **giphy_search** - Search for GIFs on Giphy
- **giphy_trending** - Get trending GIFs from Giphy

### Video Generation
- **lumalab_generate_video** - Generate videos using Luma AI
- **moviepy_create_video** - Create videos from image sequences using MoviePy

### AI Model Platforms
- **replicate_run_model** - Run any model on Replicate
- **replicate_get_prediction** - Check status of a Replicate prediction
- **fal_run_model** - Run AI models via Fal.ai

### Image Processing
- **opencv_resize_image** - Resize images using OpenCV
- **opencv_convert_format** - Convert image format using OpenCV

## Requirements

Set environment variables as needed:
- `GIPHY_API_KEY` - Giphy API key
- `UNSPLASH_ACCESS_KEY` - Unsplash API access key
- `OPENAI_API_KEY` - OpenAI API key (for DALL-E)
- `REPLICATE_API_TOKEN` - Replicate API token
- `LUMAAI_API_KEY` - Luma AI API key
- `FAL_KEY` - Fal.ai API key
- `MODELS_LAB_API_KEY` - ModelsLab API key
- `BANANA_API_KEY` - Banana.dev API key

## Examples

### Generate an image with DALL-E

```python
result = await dalle_generate_image(
    prompt="A serene mountain landscape at sunset",
    size="1024x1024",
    quality="hd"
)
```

### Search for GIFs

```python
result = await giphy_search(
    query="happy dance",
    limit=5,
    rating="g"
)
```

### Search Unsplash photos

```python
result = await unsplash_search_photos(
    query="ocean sunset",
    per_page=10
)
```

### Generate a video with Luma AI

```python
result = await lumalab_generate_video(
    prompt="A timelapse of clouds moving over mountains"
)
```

### Resize an image

```python
result = await opencv_resize_image(
    input_path="/path/to/image.jpg",
    output_path="/path/to/resized.jpg",
    width=800,
    height=600
)
```

## Response Format

All tools return a consistent response format:

```json
{
  "success": true,
  "data": {
    "...tool-specific fields..."
  }
}
```

On error:

```json
{
  "success": false,
  "error": "Description of what went wrong"
}
```

## When to Use

- Generating images from text descriptions
- Searching for stock photos or GIFs
- Creating videos from image sequences
- Running AI media generation models
- Resizing or converting image formats
