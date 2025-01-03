from torch.utils.data import Dataset, DataLoader
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error, normalized_root_mse

from .cnn_models import *
from .cnn_utils import *
from .gen_cnn_dataset import *

def subsequent_comp(pre_recons_roi, recons_roi):
    mse_noise = (normalized_root_mse(pre_recons_roi, recons_roi, normalization='min-max'))
    ssim_list = []
    for ch in range(recons_roi.shape[0]):
        im1, im2  = pre_recons_roi[ch,], recons_roi[ch,]
        ssim_list.append(ssim(im1, im2, data_range=im1.max() - im1.min(), channel_axis = 0))
    ssim_noise = np.mean(ssim_list)
    return mse_noise, ssim_noise

def cnn_data_pre(recon_roi):
    cube_h, cube_w = (100, 100)
    stride = 10
    interval = 8; stride_z = 4

    roi_cube = np.moveaxis(recon_roi, 0, -1)
    cube_slots = create_slots(roi_cube, cube_h, cube_w, stride, interval, stride_z)

    real_dataset = RealDataset(cube_slots)
    real_dataloader = DataLoader(real_dataset, batch_size = 64, shuffle=True, num_workers=0)

    return real_dataloader

def load_cnn_model():
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    model = CNN3D(5).to(device)
    ckp_path = ("/storage/gxt/cnn_model_save/"
                "New_Epoch-100-Test_loss-0.9707233309745789.pth")
    model = load_ckp(ckp_path, model, device)
    model.eval()

    return model, device

def cnn_score(recon_roi):
    dataloader = cnn_data_pre(recon_roi)
    model, device = load_cnn_model()
    pred_sum = 0
    total = 0
    for data in dataloader:
        data = data.to(device, dtype=torch.float)
        with torch.no_grad():
            output = model(data)
        pred = torch.argmax(output, 1)+1
        pred_sum += pred.sum().float()
        total += len(data)
        average_pred = pred_sum / total
    return average_pred

def comp_QI(recon_score, ssim_noise, nrmse, nrmse_ref, score_diff, diff_ref, eva_paras):
    comp_diff = 5*(1-((nrmse/nrmse_ref) + (score_diff/diff_ref))/2)+0.2
    subseq_score=(5*ssim_noise + comp_diff)/2

    QI = eva_paras['alpha'] * recon_score + eva_paras['beta'] * subseq_score
    return subseq_score, QI
