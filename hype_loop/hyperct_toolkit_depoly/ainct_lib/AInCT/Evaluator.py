import os
from ctqa import *
import pandas as pd
import numpy as np

class CNNEVA(object):
    """Evaluate reconstruction quality using CNN scoring and quality indices."""

    def __init__(self, pre_recon, recon, num_tot_ang, Z_NUM, step, eva_paras, model_pth, res_save_path):
        """
        Args:
            pre_recon: Previous reconstruction volume used as reference; None if unavailable.
            recon: Current reconstruction volume to evaluate.
            num_tot_ang: Total number of projection angles used in this reconstruction.
            Z_NUM: List of slice counts per z-block for batching through the CNN scorer.
            step: Angular increment between reconstructions when logging results.
            eva_paras: Parameter dictionary for quality index computation.
            model_pth: Filesystem path to the CNN scoring model weights.
            res_save_path: Directory where evaluation artifacts are written.
        """
        self.recon = recon
        # prior ROI cropping is already applied upstream if needed
        self.pre_recon = pre_recon
        self.save_path = res_save_path
        self.num_tot_ang = num_tot_ang
        self.Z_NUM = Z_NUM
        self.step = step
        self.eva_paras = eva_paras
        self.model_pth = model_pth
        self.recon_score = self.get_score()

        score_file = os.path.join(self.save_path, 'scores_save.csv')
        self.pre_recon_score = self.save_res(['Score'], [self.recon_score], score_file)

        self.nrmse, self.ssim_noise, self.subseq_score, self.QI = self.evaluate()

    def get_score(self):
        """Run the CNN scorer across z-blocks and return the mean score."""
        score_queue = []
        index = [0] + (self.Z_NUM)
        for idx, z_numSlice in zip(range(len(self.Z_NUM)), self.Z_NUM):
            cnt = sum(index[:idx + 1])
            score_queue.append(
                cnn_score(self.recon[cnt:cnt + z_numSlice,], self.model_pth).to('cpu').numpy()
            )

        return np.mean(score_queue)

    def save_res(self, data_name, data, file_name):
        """
        Append evaluation metrics to a CSV and return prior values for comparison.

        Args:
            data_name: Column headers describing the data being saved.
            data: Metric values to persist.
            file_name: Target CSV file path.
        Returns:
            The previously saved metric column matching the last angular step, or None.
        """
        pre_data = None
        if not os.path.exists(file_name):
            dt = {'name': data_name, 'Ang_num_{:03d}'.format(self.num_tot_ang): data}
            df = pd.DataFrame(dt)
            df.to_csv(file_name)
        else:
            df = pd.read_csv(file_name, index_col=0)
            pre_num_ang = max(self.num_tot_ang - self.step, 0)

            _pre_lst = [s for s in (df.columns.values) if 'Ang_num_{:03d}'.format(pre_num_ang) in s]
            if _pre_lst == []:
                pre_data = None
            else:
                _col_name = _pre_lst[-1]
                pre_data = df[_col_name].values

            new_df = pd.DataFrame({'Ang_num_{:03d}'.format(self.num_tot_ang): data})
            final_df = pd.concat([df, new_df], axis=1)
            final_df.to_csv(file_name)
        return pre_data

    def evaluate(self):
        """
        Compare current reconstruction against the previous one and log metrics.

        Returns:
            Tuple of (nrmse, ssim_noise, subseq_score, QI); all None if no reference.
        """
        if self.pre_recon is None:
            print('No previous reconstruction to compare!')
            return None, None, None, None
        else:
            _score_diff = self.recon_score - self.pre_recon_score
            _nrmse, _ssim_noise = subsequent_comp(self.pre_recon, self.recon)

            noise_data_file = os.path.join(self.save_path, 'MSE_SSIM_save.csv')
            _ = self.save_res(['NRMSE', 'SSIM'], [_nrmse, _ssim_noise], noise_data_file)

            ref_file = os.path.join(self.save_path, 'comp_ref.npz')
            if not os.path.exists(ref_file):
                np.savez(ref_file, nrmse=_nrmse, score_diff=_score_diff)
                ref = np.load(ref_file)
            else:
                ref = np.load(ref_file)

            subseq_score, QI = comp_QI(
                self.recon_score,
                _ssim_noise,
                _nrmse,
                ref['nrmse'],
                _score_diff,
                ref['score_diff'],
                self.eva_paras,
            )

            qi_data_file = os.path.join(self.save_path, 'QI_save.csv')
            _ = self.save_res(['QI'], [QI], qi_data_file)

        return _nrmse, _ssim_noise, subseq_score, QI
