"""Methods for loading and saving mask images."""
import numpy as np
import rasterio
from scipy.misc import imread
from skimage.filters import threshold_otsu

from ..extract import extract_features
from ..features import NirNDVI
from ..features.feature import Feature
from .conversions import multipolygon2mask
from .shapefile import load_shapefile2multipolygon


def save_mask2file(mask, filename, crs=None, transform=None):
    """Save a mask to filename."""
    height, width = mask.shape
    if mask.dtype == np.bool:
        mask = mask.astype(np.uint8)
    with rasterio.open(
            filename,
            'w',
            driver='GTiff',
            dtype=mask.dtype,
            count=1,
            width=width,
            height=height,
            crs=crs,
            transform=transform,
    ) as dst:
        dst.write(mask, indexes=1)


def load_mask_from_file(filename):
    """Load a binary mask from filename into a numpy array.

    @returns mask The mask image loaded as a numpy array
    """
    mask = imread(filename)

    return mask


def load_mask_from_shapefile(filename, shape, transform):
    """Load a mask from a shapefile."""
    multipolygon, _ = load_shapefile2multipolygon(filename)
    mask = multipolygon2mask(multipolygon, shape, transform)
    return mask


class _MeanFeature(Feature):
    base_image = 'pan'
    size = 1
    compute = staticmethod(np.mean)


def resample(generator, threshold=0.8):
    """Extract the mask points generated by generator."""
    windows = (generator.step_size, )
    feature = _MeanFeature(windows)
    values = next(extract_features([feature], generator, n_jobs=1)).vector
    values.shape = (values.shape[0], values.shape[1])
    return values > threshold


def get_ndxi_mask(generator, feature=NirNDVI):
    """Compute a mask based on an NDXI feature."""
    windows = (generator.step_size, )
    values = next(extract_features([feature(windows)], generator)).vector
    values.shape = (values.shape[0], values.shape[1])
    mask = np.array(values.mask)
    unmasked_values = np.array(values[~values.mask])
    mask[~mask] = unmasked_values < threshold_otsu(unmasked_values)
    return mask
