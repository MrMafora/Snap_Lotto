# Preview Enhancements for Snap Lotto

## Overview
This document explains the new approach to handling website previews in the Snap Lotto application. We've replaced the real-time preview generation with a more reliable approach that displays the most recently captured screenshots.

## Why These Changes Were Made

1. **Anti-Scraping Measures**: Many lottery websites employ anti-scraping technologies that detect and block automated screenshot attempts, especially when made frequently.

2. **Reliability Issues**: Previous preview attempts often timed out or failed completely, resulting in error images instead of useful previews.

3. **Resource Usage**: Generating real-time previews for every screenshot view consumed significant server resources, particularly when multiple admin users were viewing the screenshot gallery simultaneously.

## New Preview Approach

### How It Works

1. **Use Existing Screenshots**: Instead of attempting to generate a new real-time preview when viewing the screenshot gallery, the system now displays the most recently captured screenshot.

2. **Timestamp Information**: Each preview image includes a timestamp overlay showing when the screenshot was captured, formatted in a human-readable way (e.g., "Captured 2 hours ago").

3. **Clear Labeling**: The previews are clearly labeled as "CAPTURED PREVIEW" to distinguish them from live content.

### Benefits

1. **Consistent Experience**: Admins always see a preview image, even when the lottery website is actively blocking scraping attempts.

2. **Reduced Resource Usage**: Server resources are conserved by not attempting new screenshot captures for every preview view.

3. **Faster Loading**: Preview images load instantly since they're served from existing files rather than requiring a new capture process.

4. **Visual Verification**: Admins can still verify the content and appearance of lottery websites through the most recent successful capture.

## When to Sync Screenshots

With this approach, it's recommended to use the "Sync All Screenshots" button periodically (e.g., once a day) to refresh all screenshot captures. Individual screenshots can also be refreshed using their respective "Resync" buttons when needed.

## Fallback Behavior

If no screenshot exists for a URL (such as when a new screenshot entry is added), the preview will display an informative message indicating that no screenshot is available and suggesting to use the "Sync All Screenshots" or "Resync" button.

## Technical Implementation

The implementation:

1. Modifies the `/preview-website/<int:screenshot_id>` route to always use the existing screenshot file
2. Adds timestamp information and "CAPTURED PREVIEW" labeling to the images
3. Provides clear error handling and fallback images when no screenshot is available

This approach aligns with our goal of maintaining reliable, consistent functionality while avoiding triggering anti-scraping protections on the source websites.