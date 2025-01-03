import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import glob

from skimage.transform import hough_line, hough_line_peaks, probabilistic_hough_line
from skimage import feature
from skimage.io import imread


def phantomInfo(path):
    file_list = glob.glob(path + '/*.tiff')
    file_list.sort()
    print('phantom slice start: %s'%file_list[0].split('/')[-1])
    print('phantom slice end: %s'%file_list[-1].split('/')[-1])

def phantomLoad(path, z_start, z_numSlice):
    file_list = glob.glob(path + '/*.tiff')
    file_list.sort()

    temp_im = imread(file_list[0])

    phantom = np.zeros((z_numSlice, temp_im.shape[0],temp_im.shape[0]))

    for i in range(z_numSlice):
        phantom[i,] = imread(file_list[i+z_start])

    return phantom, file_list[z_start : z_start + z_numSlice]

def im_norm(img):
    """
    0-1 Normalize image (Global)
    """
    return (img-img.min())/(img.max()-img.min())

def angle_cost_exp(angle, prev_angles_list):
    """
    Compute the cost of current angles from previous angles (@Diyu)
    """
    cost = 0
    for prev_angle in prev_angles_list:
        dist_angle = min(abs(angle - prev_angle), 180-abs(angle-prev_angle))
        cost_angle = -1/(dist_angle+1e-6)
        cost += cost_angle
    return np.exp(cost)

def angle_selection(x_hat, ang_radian, canny_paras, hough_paras, mode = 'fix', **kwargs):
    """ Edge Alignment Angle Selection Algorithim Application
    Args:
        x_hat (ndarray): 3D reconstruction [num_slice, num_rows, num_cols]
        ang_radian (ndarray): 1D angles that been scanned in radian
        canny_paras (dict): parameters for canny detector
            [sigma] = Standard deviation of the Gaussian filter.
            low_thresh = [a] * img.mean()
            high_thresh = [b] * img.mean()
        hough_paras (dict): parameters for hough transform
            [line_length]: Minimum accepted length of detected lines.
            Increase the parameter to extract longer lines.
            [line_gap]: Maximum gap between pixels to still form a line.
            Increase the parameter to merge broken lines more aggressively.
        mode (string): beta/gamma generated mode
            'fix' = fixed number. default: beta = 1, gamma =1
                    gamma can be customized
            'cos' = cosine mutual model
                    **need x_hat_old input
        **kwargs:
            x_hat_old (ndarray): previous recosntruction.
                                **Must input for 'cos' mode
            gamma (int/float): set gamma value for 'fix' mode
                               optional for 'fix' mode
    Returns:
        new_angle (float): the next scan angle (deg)
    """
    edge_img_3D = edge_img_gen(x_hat, canny_paras)
    if 'x_hat_old' in kwargs.keys():
        x_hat_old = kwargs['x_hat_old']
        edge_img_3D_old = edge_img_gen(x_hat_old, canny_paras)

    if mode == 'cos':
        if 'x_hat_old' in kwargs.keys():
            beta = (cosine_angle(edge_img_3D, edge_img_3D_old))
            gamma = (cosine_angle(x_hat, x_hat_old))
        else:
            print('ERROR: Need previouse recon for beta/gamma compute!!')
            return None
    else:
        beta = 1
        gamma = kwargs['gamma'] if 'gamma' in kwargs.keys() else 1

    ll, lg = hough_paras['line_length'], hough_paras['line_gap']
    new_ang = select_next_angle(edge_img_3D, np.pi - ang_radian,
                                ll, lg,  beta=beta, gamma=gamma,
                                filename=None)
    return 180.0 - new_ang

################### Start angle selection algorithm
def select_next_angle(edge_img_3D, angles_k, ll, lg, beta, gamma, hough_test_angles=None, view_angle_candidates=None, filename=None):
    """ Angle selection algorithm based on edge alignment.
        @Diyu Yang, 10/10/2022

    Args:
        edge_img_3D (ndarray): 3D binary edge image used to compute edge alignment cost.
        angle_k (ndarray): 1D view angles that has been scanned in radian.
        beta (float): scalar associated to edge alignment cost.
        gamma (float): scalar associated to angle spacing cost.
        hough_test_angles: candidates for Hough Angles in radian. Default = np.linspace(0, np.pi, 360, endpoint=False)
        view_angle_candidates: candidates for the next view angle in deg. Default = np.linspace(0, np.pi, 180, endpoint=False)
        filename: filename to store the plots for cost functions. If None, then no plots will be saved.
    Returns:
        The next view angle in deg
    """
    num_slices, num_rows, num_cols = edge_img_3D.shape
    # view angles candidates
    if view_angle_candidates is None:
        view_angle_candidates = np.linspace(0, 180, 180, endpoint=False)
    # hough angles candidates
    if hough_test_angles is None:
        hough_test_angles = np.linspace(0, np.pi, 360, endpoint=False)
    Theta = []; lsum = [];
    for slice_idx in range(num_slices):
        # Hough features
        lines = probabilistic_hough_line(edge_img_3D[slice_idx], threshold=1, line_length=ll, line_gap=lg, theta=hough_test_angles,seed=123)
        for line in lines: #Transfer Hough feature into Longer Lineds
            p0, p1 = line
            midpt = ((p0[0]+p1[0])/2, (p0[1]+p1[1])/2)
            theta = 90 if p0[0]-p1[0] ==0 else np.rad2deg(np.arctan((p0[1]-p1[1])/(p0[0]-p1[0])))
            if theta < 0: theta = theta + 180
            theta_lst = [theta] + view_angle_candidates.tolist()
            for t in theta_lst:
                # if t is previously scanned,
                # then we simply do not consider it as a candidate for the next view angle.
                if np.any(abs(t-np.rad2deg(angles_k))<0.5):
                    continue
                Lx, Ly = line_extract(t, midpt, num_rows, num_cols)
                edge_cost_angle = edge_img_3D[slice_idx][Ly, Lx].sum()
                # if t has been detected in previous slices
                if t in Theta:
                    lsum[Theta.index(t)] += edge_cost_angle  # edge cost = sum of 2D edge cost in each slice
                else:
                    lsum.append(edge_cost_angle)
                    Theta.append(t)
    # angle spacing cost for each angle
    h = np.array([angle_cost_exp(t, np.rad2deg(angles_k)) for t in Theta])
    lsum = np.array(lsum)
    # normalize lsum and h so that they have max value of 1.
    lsum /= np.max(lsum)
    h /= np.max(h)
    # theta = argmax(final_cost).
    final_cost = beta*lsum + gamma*h
    theta_new = Theta[np.argmax(final_cost)]
    return theta_new
################### END angle selection algorithm
def edge_img_gen(x_hat, canny_paras):
    """ Edge detection for Edge Alignment Angle Selection Algorithim
    Args:
        x_hat (ndarray): 3D reconstruction [num_slice, num_rows, num_cols]
        canny_paras (dict): parameters for canny detector
            [sigma] = Standard deviation of the Gaussian filter.
            low_thresh = [a] * img.mean()
            high_thresh = [b] * img.mean()
    Returns:
        edge_img_3D (ndarray): 3D binary edge image
    """
    sigma, a, b = canny_paras['sigma'], canny_paras['a'], canny_paras['b']
    edge_img_3D = np.zeros_like(x_hat)
    total_slices, _, _ = edge_img_3D.shape
    for slice_idx in range(total_slices):
        im_temp = im_norm(x_hat[slice_idx,])
        edge_im = feature.canny(im_temp, sigma = sigma,
                                low_threshold = a*im_temp.mean(),
                                high_threshold = b*im_temp.mean())
        edge_im[:3,:] = False; edge_im[-3:,:] = False
        edge_im[:,:3] = False; edge_im[:,-3:] = False
        edge_img_3D[slice_idx] = edge_im

    return edge_img_3D

def cosine_angle(x,y):
    nominator = np.sum(x*y)
    denominator = np.sum(np.sqrt(np.sum(x*x)) * np.sqrt(np.sum(y*y)))
    if np.abs(denominator < 1e-6):
        return 0
    else:
        return nominator / denominator

def line_extract(t, midpt, num_rows, num_cols):
    """
    Get the x/y coordinates along the projection angle
    """
    if t == 90:
        _y =  np.linspace(0, num_rows, int(num_cols/2), endpoint=False).astype(int)
        Lx, Ly = int(midpt[0]) * np.ones(len(_y), dtype=int), _y
    else:
        slo = np.tan(np.deg2rad(t))
        x = np.arange(0, num_cols, 1)
        y = ((midpt[1]-slo*midpt[0])+x*slo).astype(int)
        y_trim_idx = np.where(np.where(np.where(y < num_rows, y, 0 )>0, y, 0)!=0)
        x_trim, y_trim = x[y_trim_idx].astype(int), y[y_trim_idx]

        if x_trim.max()-x_trim.min()<= (num_cols/20):
            Lx = np.linspace(x_trim.min(), x_trim.max(), int(num_cols/2), endpoint=False).astype(int)
            Ly = np.linspace(0, y_trim.max(), int(num_cols/2), endpoint=False).astype(int)
            #np.linspace(0, num_rows_cols-1, int(num_rows_cols/2), endpoint=False).astype(int)
        else:
            Lx = np.linspace(x_trim.min(), x_trim.max(), num_cols, endpoint=False).astype(int)
            Ly = ((midpt[1]-slo*midpt[0])+Lx*slo).astype(int)
    return Lx, Ly

#>>>>>>>>Display Relatives<<<<<<<<<<
def draw_hough(img, lines):
    """
    [Display] show the image with hough proposed lines
    """
    plt.imshow(img, cmap = 'gray')
    for line in lines:
        p0, p1 = line
        plt.plot([p0[0], p1[0]], [p0[1], p1[1]], '-o')
    plt.xlim((0, img.shape[1]))

def plot_with_initial(data, linestys, line_cl, line_lb, xlabel, ylabel, savepath=None):
    """
    [Display] plot MSE/Angles/others with intial highlight
    """
    plt.plot(data, linestys, color = line_cl, label = line_lb)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid('on', axis = 'y', linestyle = '--')
    if savepath is not None:
        plt.savefig(savepath)

def plotReconNew(ax_polar, angle, lt, color, lw, lb):
    r = np.arange(0, 2, 0.1)
    ax_polar.patch.set_alpha(0)
    for phi in angle:
        theta0 = np.deg2rad(phi)*np.ones(len(r))
        theta1 = np.deg2rad(180+phi)*np.ones(len(r))
        ax_polar.plot(theta0, r, linestyle=lt, color=color, linewidth = lw, label = lb)
        ax_polar.plot(theta1, r, linestyle=lt, color=color, linewidth = lw, label = lb)
