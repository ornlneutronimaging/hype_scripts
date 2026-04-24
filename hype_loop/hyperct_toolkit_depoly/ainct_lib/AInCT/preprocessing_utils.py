import numpy as np

def replace_bad_pixels(image, radius, threshold_ratio=0.1):
    """
    Replace bad pixels in the image using the average of neighbors above a threshold.
    Args:
        image (np.ndarray): Input image to clean.
        radius (int): Neighborhood size for pixel replacement.
        threshold_ratio (float): Percentage of the median to define the threshold.
    
    Returns:
        np.ndarray: Cleaned image with bad pixels replaced.
    """
    corrected_image = image.copy()
    threshold = threshold_ratio * np.median(corrected_image)

    x_coords, y_coords = np.nonzero(corrected_image <= threshold)
    for x, y in zip(x_coords, y_coords):
        neighborhood = corrected_image[
            max(0, x - radius):min(image.shape[0], x + radius + 1),
            max(0, y - radius):min(image.shape[1], y + radius + 1)
        ]
        if np.sum(neighborhood > threshold) >= 4:
            corrected_image[x, y] = np.mean(neighborhood)
        else:
            print(f"Failed to replace pixel at ({x}, {y}): insufficient neighbors.")
    return corrected_image

def correct_alignment(image, x_offset, y_offset, center_x, center_y, fill_gap=True):
    """
    Corrects alignment of subregions in an image caused by detector misalignment.
    """
    # Subdivide and align chips
    chip_top_left = image[:center_x, :center_y]
    chip_top_right = image[:center_x, center_y:]
    chip_bottom_left = image[center_x:, :center_y]
    chip_bottom_right = image[center_x:, center_y:]

    aligned = np.zeros((image.shape[0] + x_offset, image.shape[1] + y_offset))
    aligned[:center_x, :center_y] = chip_top_left
    aligned[:center_x, center_y + y_offset:] = chip_top_right
    aligned[center_x + x_offset:, :center_y] = chip_bottom_left
    aligned[center_x + x_offset:, center_y + y_offset:] = chip_bottom_right

    return aligned