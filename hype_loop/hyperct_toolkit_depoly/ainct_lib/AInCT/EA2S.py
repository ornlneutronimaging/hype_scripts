"""
EA2S — Edge/Angle selection utilities (refactored)

This module provides utilities to detect dominant line angles in 2D/3D image stacks using
probabilistic Hough transforms and a scoring scheme that prefers diverse angles and
penalizes vertical/horizontal bias. 

Highlights of this refactor:
- Type annotations and clearer docstrings
- Configurable parallelism (n_jobs)
- Configurable Hough theta sampling
- Better validation and clearer errors
- No change to algorithmic intent (keeps Hough-based scoring approach)
"""

from typing import Iterable, List, Optional, Tuple, Dict

import logging
from collections import defaultdict

import numpy as np
from joblib import Parallel, delayed
from skimage. draw import line as draw_line
from skimage. filters import threshold_otsu
from skimage.morphology import binary_erosion
from skimage.transform import probabilistic_hough_line

logger = logging.getLogger(__name__)

__all__ = [
    "auto_threshold",
    "edge_img_gen",
    "angle_cost_exp",
    "angle_penalty",
    "line_angle_and_score",
    "process_slice",
    "select_next_angle",
    "angle_selection",
]


def auto_threshold(volume: np.ndarray) -> np.ndarray:
    """Compute Otsu threshold and return a binary mask for 2D or 3D arrays.

    Parameters
    ----------
    volume
        Input image or stack.  If 3D, Otsu is applied to the flattened intensities.

    Returns
    -------
    Binary mask ndarray with same shape as `volume`.
    """
    if volume.size == 0:
        raise ValueError("auto_threshold received empty input.")
    thresh = threshold_otsu(volume)
    return volume > thresh


def edge_img_gen(x_hat: np.ndarray) -> np.ndarray:
    """Generate an edge-like binary image via Otsu thresholding and one-pixel erosion.

    This returns the pixels that are foreground in the thresholded image but
    are removed by a single erosion operation (i.e., edge ring approximation).

    Parameters
    ----------
    x_hat
        2D or 3D image (if 3D, it is treated as a stack of 2D slices).

    Returns
    -------
    Binary ndarray of same shape as x_hat.
    """
    bi_data = auto_threshold(x_hat)
    eroded = binary_erosion(bi_data)
    return bi_data & ~eroded


def angle_cost_exp(angle_deg: float, prev_angles_deg:  Iterable[float]) -> float:
    """Compute an angle diversity score in degrees.

    The function returns an exponential penalty based on reciprocal distance
    to all previous angles; small distances lead to small values.

    Credit: Diyu Yang

    Parameters
    ----------
    angle_deg
        angle in degrees (0.. 180)
    prev_angles_deg
        iterable of previously selected angles in degrees

    Returns
    -------
    float
        Diversity score (higher is better).
    """
    prev = list(prev_angles_deg)
    if not prev:
        return 1.0
    # avoid zero division; consider circular distance mod 180
    distances = [min(abs(angle_deg - p), 180.0 - abs(angle_deg - p)) for p in prev]
    score = np.exp(np.sum([-1.0 / (d + 1e-6) for d in distances]))
    return float(score)


def angle_penalty(theta_deg: float) -> float:
    """Empirical penalty to slightly de-prioritize perfectly vertical/horizontal angles.

    Returns a multiplicative factor <= 1.0 to scale line scores. 
    """
    # Penalize if within 1 degree of 0/90/180:
    if abs(theta_deg - 90.0) < 1.0:
        return 0.8
    if theta_deg < 1.0 or abs(theta_deg - 180.0) < 1.0:
        return 0.8
    return 1.0


def line_angle_and_score(
    line:  Tuple[Tuple[int, int], Tuple[int, int]],
    edge:  np.ndarray,
    shift: int = 2,
) -> Tuple[float, float]:
    """Compute the line angle (in degrees 0..180) and a normalized line score.

    For near-vertical or near-horizontal lines, the function averages scores
    across a few parallel offsets to produce a more stable estimate.

    Parameters
    ----------
    line
        ((x0, y0), (x1, y1)) pixel coordinates from skimage probabilistic_hough_line
        Note: skimage returns points as (x, y) = (col, row) so this function keeps that convention.
    edge
        Binary edge image (2D) where True indicates edge pixels.
    shift
        Number of parallel offsets to average for near-vertical/horizontal lines.

    Returns
    -------
    (theta_deg, score)
    """
    (x0, y0), (x1, y1) = line
    # compute angle in degrees; arctan2 with arguments (dy, dx) where dy = row difference
    dx = x0 - x1
    dy = y0 - y1
    if dx == 0:
        theta = 90.0
    else:
        theta = np.degrees(np.arctan2(dy, dx))
        if theta < 0:
            theta += 180.0

    # Score:  proportion of True edge pixels along the line (or averaged parallel lines)
    h, w = edge.shape
    if abs(theta - 90.0) < 1.0:
        # near-vertical:  sample columns around the mid column
        mid_col = int(round((x0 + x1) / 2.0))
        scores = []
        rr = np.arange(0, h)
        for dx_off in range(-shift, shift + 1):
            col = np.clip(mid_col + dx_off, 0, w - 1)
            scores.append(np.sum(edge[rr, col]) / (h + 1e-6))
        score = float(np.mean(scores))
    elif abs(theta) < 1.0 or abs(theta - 180.0) < 1.0:
        # near-horizontal: sample rows around mid row
        mid_row = int(round((y0 + y1) / 2.0))
        scores = []
        cc = np.arange(0, w)
        for dy_off in range(-shift, shift + 1):
            row = np. clip(mid_row + dy_off, 0, h - 1)
            scores.append(np.sum(edge[row, cc]) / (w + 1e-6))
        score = float(np.mean(scores))
    else:
        rr, cc = draw_line(int(y0), int(x0), int(y1), int(x1))
        rr = np.clip(rr, 0, h - 1)
        cc = np.clip(cc, 0, w - 1)
        score = float(np.sum(edge[rr, cc]) / (len(rr) + 1e-6))

    score *= angle_penalty(theta)
    return theta, score


def process_slice(
    edge:  np.ndarray,
    angles_k: np.ndarray,
    line_length: int,
    line_gap: int,
    hough_thetas: np.ndarray,
    angle_bin_size: float = 1.0,
) -> Dict[int, List]: 
    """Run Hough line detection on a single 2D edge slice and bin scores by rounded angle.

    Returns a dict mapping bin_angle (int degrees) to [total_score, (max_score, real_angle)].
    """
    # deterministic sampling to keep tests repeatable
    np.random.seed(123)
    lines = probabilistic_hough_line(
        edge,
        threshold=1,
        line_length=line_length,
        line_gap=line_gap,
        theta=hough_thetas,
    )
    angle_score:  Dict[int, List] = defaultdict(lambda: [0.0, (0.0, 0.0)])
    for ln in lines:
        real_angle, score = line_angle_and_score(ln, edge)
        bin_angle = int(np.round(real_angle / angle_bin_size) * angle_bin_size)
        # Skip angles that are already selected (angles_k in radians are converted by caller to degrees)
        if angles_k. size > 0 and np.any(np.abs(bin_angle - np.rad2deg(angles_k)) < 0.5):
            continue
        angle_score[bin_angle][0] += score
        if score > angle_score[bin_angle][1][0]:
            angle_score[bin_angle][1] = (score, real_angle)
    return angle_score


def select_next_angle(
    edge_img_3D: np.ndarray,
    angles_k: np.ndarray,
    line_length: int,
    line_gap: int,
    beta: float,
    gamma: float,
    hough_test_angles: Optional[np.ndarray] = None,
    angle_bin_size: float = 1.0,
    n_jobs: int = -1,
) -> Tuple[int, float, float]:
    """Aggregate angle scores across all slices and select the next best angle.

    Credit: Cost function design by Diyu Yang

    Parameters
    ----------
    edge_img_3D
        3D binary edge stack with shape (num_slices, rows, cols)
    angles_k
        array of already-selected angles in radians (as used elsewhere in the package)
    line_length, line_gap
        Hough parameters
    beta, gamma
        weighting parameters:  final_cost = beta * normalized_score + gamma * normalized_diversity
    hough_test_angles
        array of theta values in radians to pass to probabilistic_hough_line.  If None, a default
        uniform sampling over [0, pi) is used.
    angle_bin_size
        bin size in degrees for grouping line angles
    n_jobs
        number of parallel jobs (joblib). Default -1 (all cores). Use 1 for deterministic single-thread.

    Returns
    -------
    (theta_bin_deg, real_angle_deg, max_score)
    """
    num_slices = int(edge_img_3D.shape[0])
    if num_slices == 0:
        raise ValueError("select_next_angle received empty edge image stack.")

    if hough_test_angles is None:
        hough_test_angles = np.linspace(0.0, np.pi, 360, endpoint=False)

    # Process slices in parallel (configurable)
    results = Parallel(n_jobs=n_jobs)(
        delayed(process_slice)(
            edge_img_3D[sidx], angles_k, line_length, line_gap, hough_test_angles, angle_bin_size
        )
        for sidx in range(num_slices)
    )

    total_angle_score:  Dict[int, List] = defaultdict(lambda: [0.0, (0.0, 0.0)])
    for d in results:
        for angle_bin, (sum_score, max_pair) in d.items():
            total_angle_score[angle_bin][0] += sum_score
            if max_pair[0] > total_angle_score[angle_bin][1][0]:
                total_angle_score[angle_bin][1] = max_pair

    if not total_angle_score:
        raise RuntimeError("No candidate angles found across all slices.")

    Theta = np.array(list(total_angle_score.keys()))
    lsum = np.array([total_angle_score[t][0] for t in Theta], dtype=float)

    # Diversity score: angle_cost_exp expects degrees for prev angles
    prev_angles_deg = np.rad2deg(angles_k) if angles_k.size > 0 else np.array([], dtype=float)
    h = np.array([angle_cost_exp(float(t), prev_angles_deg) for t in Theta], dtype=float)

    # Normalize
    if lsum.max() > 0:
        lsum = lsum / lsum. max()
    if h.max() > 0:
        h = h / h.max()

    # Cost function (Credit:  Diyu Yang)
    final_cost = beta * lsum + gamma * h
    idx = int(np.argmax(final_cost))
    theta_bin = int(Theta[idx])
    max_score, real_angle = total_angle_score[theta_bin][1]
    return theta_bin, float(real_angle), float(max_score)


def edge_img_gen(x_hat: np.ndarray) -> np.ndarray:
    """
    Generate a binary edge mask via Otsu threshold + one-pixel erosion.

    Parameters
    ----------
    x_hat : np.ndarray
        Grayscale 2D or 3D image/stack.
    force_otsu : bool, default False
        If True, always apply Otsu+erosion. If False and input is already bool,
        return it unchanged.

    Returns
    -------
    np.ndarray
        Binary edge mask with the same shape as x_hat.
    """
    bi_data = auto_threshold(x_hat)      # Otsu threshold
    eroded = binary_erosion(bi_data) # Remove one-pixel interior
    return bi_data & ~eroded


def angle_selection(
    x_hat: np.ndarray,
    ang_radian: float,
    hough_paras: Dict[str, int],
    *,
    beta: float = 1.0,
    gamma: float = 1.0,
    angle_bin_size: float = 1.0,
    n_jobs: int = -1,
    rescale_percentiles: Optional[Tuple[float, float]] = (1, 99),
) -> Tuple[float, float]:
    """
    Propose the next angle for a 2D/3D stack using Hough-based scoring.

    Optional percentile stretch improves Otsu robustness on low dynamic range data.

    Parameters
    ----------
    x_hat : np.ndarray
        Grayscale image (H,W) or stack (N,H,W).
    ang_radian : float
        Current angle (radians); complements are excluded from candidates.
    hough_paras : Dict[str, int]
        Keys: 'line_length', 'line_gap'.
    beta, gamma : float
        Weights for line score and diversity.
    angle_bin_size : float
        Bin size in degrees for angle grouping.
    n_jobs : int
        Parallel jobs for per-slice Hough (joblib).
    rescale_percentiles : (low, high) or None
        Percentiles for contrast stretch before Otsu. Set None to disable.

    Returns
    -------
    (proposed_angle_deg, max_score)
        Proposed angle in degrees and its max score.
    """
    x = np.asarray(x_hat)

    # Optional contrast stretch to help Otsu on low-range data
    if rescale_percentiles is not None and x.size > 0:
        lo, hi = np.percentile(x, rescale_percentiles)
        if hi > lo:
            x = np.clip((x - lo) / (hi - lo + 1e-9), 0, 1)

    # Build edge stack (Otsu + erosion)
    if x.ndim == 2:
        edge_img_3D = edge_img_gen(x)[None, ...]
    elif x.ndim == 3:
        edge_img_3D = edge_img_gen(x)
    else:
        raise ValueError("angle_selection expects 2D or 3D input")

    ll = int(hough_paras.get("line_length", 10))
    lg = int(hough_paras.get("line_gap", 3))

    theta_bin, real_angle_deg, max_score = select_next_angle(
        edge_img_3D,
        np.pi - ang_radian,
        ll,
        lg,
        beta,
        gamma,
        hough_test_angles=None,
        angle_bin_size=angle_bin_size,
        n_jobs=n_jobs,
    )

    proposed_angle = 180.0 - real_angle_deg  # preserve legacy mapping
    return proposed_angle, max_score
