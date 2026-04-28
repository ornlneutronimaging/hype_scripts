import datetime
import os
import glob
import warnings
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API",
    category=UserWarning
)
import dxchange
import h5py
import numpy as np
import pandas as pd
import yaml
from skimage.io import imread

#from AInCT import CNNEVA, DataHandler
#from AInCT.EA2S import angle_selection
from AInCT.utils import Enqueue, dir_check, eic_submit_table_scan, generate_gs_angle

# %%
class AIRobo(object):
    def __init__(self, cfg_file, mode = "load", wavIdx = 100):
        self.mode = mode
        self.cfg_file = cfg_file
        # Load YAML config once at init
        self.cfg = yaml.safe_load(open(cfg_file, 'r', encoding = 'utf-8'))
        self.data_handler = None
        
        _exp_name = f"{self.cfg['EIC_vals']['sample_name']}_{self.cfg['EIC_vals']['user_con']}"
        # Folder root for all outputs of this experiment
        self.out_path = os.path.join(self.cfg['OutPath'], _exp_name)
        dir_check(self.out_path)

        self.center_offset = self.cfg['center_offset']
        self.step = self.base_step = self.cfg['step']  # dynamic step may drop to 2 beyond 50 angles
        self.Z_START = self.cfg['Z_START']  # per-block z start indices
        self.Z_NUM = self.cfg['Z_NUM']      # per-block z slice counts
        
        self.angle_propose_flag = self.cfg['angle_propose_flag']
        self.num_ini_ang = self.cfg.get('num_ini_ang', 6)  # default to 6 if not specified

        w_pairs = list(zip(self.cfg['wav_idx_start'], self.cfg['wav_idx_end']))
        if wavIdx < len(w_pairs):
            w_pairs = [w_pairs[wavIdx]]
            print("Processing data from {}th to {}th wavelength".format(*w_pairs[0]))

        if not w_pairs:
            raise RuntimeError('No wavelength index ranges configured; check wav_idx_start/wav_idx_end in config')
        
        mode_handlers = {
            'load': self.run_load,
            'recon': self.run_recon,
            'evaluate': self.run_evaluate,
            'angle': self.run_angle,
        }
        handler = mode_handlers.get(self.mode.lower())
        if not handler:
            raise RuntimeError(f"Unsupported mode '{self.mode}'. Choose one of {list(mode_handlers.keys())}.")
        handler(w_pairs)

    def run_load(self, w_pairs):
        # Normalize OB/projections and persist norm_sino/angles for later steps.
        for st, end in w_pairs:
            self.proj_load(st, end)
        print(f"Saved normalized sinograms and angle lists under {os.path.join(self.out_path, 'norm_sino')}")

    def run_recon(self, w_pairs):
        angle_list_for_csv = None  # collect one angle list for optional CSV export
        for st, end in w_pairs:
            _norm_data, angle_list = self._read_norm_from_h5(st, end)
            if angle_list_for_csv is None:
                angle_list_for_csv = angle_list
            self.Recon(_norm_data, angle_list, st, end)
        if angle_list_for_csv is not None:
            file_name = os.path.join(self.out_path, 'angle_list_real.csv')
            df = pd.DataFrame({'Index': np.arange(1, len(angle_list_for_csv) + 1).tolist(), 'Angle': angle_list_for_csv})
            df.to_csv(file_name, index=False)

    def run_evaluate(self, w_pairs):
        ResQueues = [[], [], []] # RecScore_Queue, SubseqScore_Queue, QI_Queue
        _qi = None
        for st, end in w_pairs:
            _qi = self.EVA(st, end)
            ResQueues = Enqueue(ResQueues, [_qi.recon_score, _qi.subseq_score, _qi.QI])

        if _qi is None:
            raise RuntimeError('EVA returned no quality info; aborting evaluate mode')

        num_tot_ang = _qi.num_tot_ang
        self._set_step(num_tot_ang)
        self.recon_score = np.mean(ResQueues[0])
        self.subseq_score = np.mean(ResQueues[1]) if any(ResQueues[1]) else None
        self.QI = np.mean(ResQueues[2]) if any(ResQueues[2]) else None

        print('Recon Ang_num_{:03d} score is {:.3f}'.format(num_tot_ang, self.recon_score))
        print('Subsequent improvement from Ang_num_{:03d} is {}'.format(num_tot_ang - self.step, self.subseq_score))
        print('Comprehensive QI of Ang_num_{:03d} is {}'.format(num_tot_ang, self.QI))

        if self.QI is not None and self.QI > self.cfg['QIthresh']:
            self.cfg['angle_propose_flag'] = False
            with open(self.cfg_file, 'w') as file:
                yaml.dump(self.cfg, file, default_flow_style=False)
            print(f'{datetime.datetime.now()}\n >>>>>> Reach expected quality, Experiment is stopped <<<<<<')
        elif num_tot_ang >= self.cfg['Max_ang_num']:
            self.cfg['angle_propose_flag'] = False
            with open(self.cfg_file, 'w') as file:
                yaml.dump(self.cfg, file, default_flow_style=False)
            print(f'{datetime.datetime.now()}\n >>>>>> Reach pre-set maximum scans, Experiment is stopped <<<<<<')
        else:
            print(f'{datetime.datetime.now()}\n >>>>>> Need new angles proposing <<<<<<')

    def run_angle(self, w_pairs):
        # Assume angles identical across wavelengths; read once from the first block
        if not w_pairs:
            raise RuntimeError('No wavelength indices configured for angle mode')

        _, angle_list = self._read_norm_from_h5(*w_pairs[0])
        num_tot_ang = len(angle_list)
        if self.angle_propose_flag:
            self._set_step(num_tot_ang)
            if self.cfg['provided_ang_list'] != []:
                # pre-set angle list
                next_angles = self.cfg['provided_ang_list'][num_tot_ang:num_tot_ang + self.step]
                next_angles = list(np.array(next_angles, dtype=np.float64))
                print(f'{datetime.datetime.now()}\n >>>>>> Sending new angles [Provided]<<<<<<')
            else:
                # Edge alignment proposals per wavelength; merged and deduped across wavelengths
                if self.cfg['edge_type'].lower() == 'ea2s':
                    next_angles = self._run_ea2s(w_pairs, angle_list)
                else:
                    next_angles = self._run_vcls(w_pairs, angle_list)

                print(f'{datetime.datetime.now()}\n >>>>>> Sending new angles [AI]<<<<<<')
            
            file_name = os.path.join(self.out_path, 'angle_list_setting.csv')
            self.save_data(file_name, np.arange(num_tot_ang + 1, 
                                                num_tot_ang + 1 + len(next_angles)).tolist(),
                                                next_angles)
            print(f'{datetime.datetime.now()} > {next_angles =}')
            
            #self._send_angles(next_angles, num_tot_ang)
        else:
            print(f'{datetime.datetime.now()} > No need propse angles')

    def save_data(self, file_name, index, data):
        ct = datetime.datetime.now()
        time_str = ct.isoformat(timespec='seconds')
        if not os.path.exists(file_name):
            df = pd.DataFrame({'Time': [time_str]*len(data), 
                               'Index':index,'Angle/deg': data})
            df.to_csv(file_name)
        else:
            new_df = pd.DataFrame({'Time': [time_str]*len(data),
                                   'Index': index, 'Angle/deg': data})
            final_df = pd.concat([pd.read_csv(file_name, index_col=0), new_df], 
                                 axis = 0)
            final_df.to_csv(file_name)

    def _set_step(self, num_angles):
        # Drop to step=2 once total angles exceed 50
        self.step = 2 if num_angles > 50 else self.base_step

    def get_ROI(self, data):
        roi = self.cfg['roi_info']
        if data is None:
            return None
        else:
            temp = data.copy()
            return temp[:, roi['roi_x'] : roi['roi_x'] + roi['roi_height'], roi['roi_y'] : roi['roi_y'] + roi['roi_width']]

    def _build_data_handler_config(self):
        align_paras = self.cfg.get('align_paras', {})
        base_data_path = self.cfg.get('top_projections_folder_name')
        if base_data_path is None:
            raise KeyError('Config missing top_projections_folder_name')
        ob_list = self.cfg.get('ob_local_path', [])  # assumed absolute paths now

        return {
            'out_path': self.cfg.get('out_path', self.out_path),
            'proj_path': base_data_path,
            'ob_list': ob_list,
            'use_clean_data': self.cfg.get('use_clean_data', False),
            'num_workers': self.cfg.get('num_workers', 4),
            'use_neunorm': self.cfg.get('use_neunorm', False),
            'swap_axes': self.cfg.get('swap_axes', False),
            'correct_radius': self.cfg.get('correct_radius', align_paras.get('neighbor_pix_num', 3)),
            'x_offset': self.cfg.get('x_offset', align_paras.get('x_off', 0)),
            'y_offset': self.cfg.get('y_offset', align_paras.get('y_off', 0)),
            'cent_x': self.cfg.get('cent_x', align_paras.get('cent_x', 256)),
            'cent_y': self.cfg.get('cent_y', align_paras.get('cent_y', 256)),
        }

    def _ensure_data_handler(self):
        from AInCT import DataHandler
        if self.data_handler is None:
            handler_cfg = self._build_data_handler_config()
            self.data_handler = DataHandler(handler_cfg)
        return self.data_handler

    def _cleanup_processed_data(self, st, end):
        """Remove processed OB/projection artifacts for a wavelength block when force reloading."""
        targets = []
        norm_dir = os.path.join(self.out_path, 'norm_sino')
        targets.extend(glob.glob(os.path.join(norm_dir, f'normalized_sino_wav_{st}_{end}_n*.h5')))

        ob_path = os.path.join(self.out_path, 'OBs', f'OB_wav_{st}_{end}.tiff')
        proj_dir = os.path.join(self.out_path, 'Projs', f'wav_{st}_{end}')
        targets.append(ob_path)
        targets.append(proj_dir)

        for path in targets:
            if not os.path.exists(path):
                continue
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path, ignore_errors=True)
            else:
                try:
                    os.remove(path)
                except OSError:
                    pass

    def proj_load(self, st, end, force_reload=False):
        # Load or generate normalized sinograms and angles using DataHandler; DataHandler handles caching internally.
        if force_reload:
            self._cleanup_processed_data(st, end)

        handler = self._ensure_data_handler()
        ob_data = handler.process_ob(st, end)
        norm_data, angle_list = handler.process_projections(st, end, ob_data)
        return norm_data, angle_list

    def _read_norm_from_h5(self, st, end):
        norm_dir = os.path.join(self.out_path, 'norm_sino')
        pattern = os.path.join(norm_dir, f'normalized_sino_wav_{st}_{end}_n*.h5')
        matches = sorted(glob.glob(pattern))
        if not matches:
            raise FileNotFoundError(f'No normalized_sino file found for wav_{st}_{end} under {norm_dir}')

        h5_path = matches[0]
        with h5py.File(h5_path, 'r') as f:
            norm_data = f['norm_data'][()]
            angle_list = np.array(f['angles_deg'][()], dtype=np.float64).ravel()

        return norm_data, angle_list

    def _crop_sino(self, norm_data, z_start, z_num_slice, crop_start, crop_end):
        # norm_data shape: (num_angles, num_z, num_cols); slice z on axis=1 and cols on axis=2
        return norm_data[:, z_start:z_start + z_num_slice, crop_start:crop_end]

    def Recon(self, norm_data, angle_list, st, end):
        # Reconstruction
        num_tot_ang = len(angle_list)
        self._set_step(num_tot_ang)

        recon_save_path = os.path.join(self.out_path, 'Recons', 'wav_{}_{}'.format(st, end))
        dir_check(recon_save_path)

        pre_recon = self.get_exist_recon(recon_save_path, max(num_tot_ang - self.step, 0))
        recon = self.gen_recon(recon_save_path, norm_data, angle_list,
                               (None if pre_recon is None else pre_recon.copy()))
        return recon

    def EVA(self, st, end):
        from AInCT.Evaluator import CNNEVA
        _, angle_list = self._read_norm_from_h5(st, end)
        num_tot_ang = len(angle_list)
        self._set_step(num_tot_ang)
        res_save_path = os.path.join(self.out_path, 'Results', 'wav_{}_{}'.format(st, end))
        dir_check(res_save_path)
        
        eval_step = 2 if num_tot_ang == 50 else self.step
        recon_save_path = os.path.join(self.out_path, 'Recons', 'wav_{}_{}'.format(st, end))
        pre_recon = self.get_exist_recon(recon_save_path, max(num_tot_ang - eval_step, 0))
        current_recon = self.get_exist_recon(recon_save_path, max(num_tot_ang, 0))

        pre_roi, rec_roi = self.get_ROI(pre_recon), self.get_ROI(current_recon)

        quality = CNNEVA(pre_roi,
                         rec_roi,
                         num_tot_ang,
                         self.Z_NUM,
                         eval_step,
                         self.cfg['eva_paras'],
                         model_pth=self.cfg.get('trained_model_path', ''),
                         res_save_path=res_save_path,
                         )
        return quality

    def get_exist_recon(self, recon_save_path, num_angles):
        _recon_name = os.path.join(recon_save_path, 'Ang_num_{:03d}.tiff'.format(num_angles))
        if not os.path.exists(_recon_name):
            print("Recon {} is not exist!".format(_recon_name))
            pre_recon = None
        else:
            print("Load existed recon from {}...".format(_recon_name))
            pre_recon = imread(_recon_name)
        return pre_recon

    def gen_recon(self, recon_save_path, norm_data, angle_list, pre_recon):
        recon_name = os.path.join(recon_save_path, 'Ang_num_{:03d}.tiff'.format(len(angle_list)))

        # Support both list/tuple crop ranges and int window sizes
        crop_cfg = self.cfg['crop_cols']
        if isinstance(crop_cfg, (list, tuple)) and len(crop_cfg) == 2:
            crop_start, crop_end = crop_cfg
        elif isinstance(crop_cfg, (int, float)):
            half = int(crop_cfg) // 2
            center = norm_data.shape[2] // 2
            crop_start = max(center - half, 0)
            crop_end = min(center + half, norm_data.shape[2])
        else:
            raise ValueError('crop_cols must be a length-2 sequence or an int')

        tot_cols = crop_end - crop_start

        if os.path.exists(recon_name):
            recon = imread(recon_name)
            print('load recon from {}'.format(recon_name))
            return recon

        block_recons = []
        offsets = [0]
        for z_num in self.Z_NUM:
            offsets.append(offsets[-1] + z_num)

        recon_method = self.cfg.get('recon_method', 'svmbir').lower()
        print(f'>reconstruction method is {recon_method}')

        for idx, (z_start, z_num_slice) in enumerate(zip(self.Z_START, self.Z_NUM)):
            crop_data = self._crop_sino(norm_data, z_start=z_start, z_num_slice=z_num_slice, crop_start=crop_start, crop_end=crop_end)
            print(f'cropped data size: {crop_data.shape}')

            init_img = 0.0
            if pre_recon is not None:
                init_img = pre_recon[offsets[idx]:offsets[idx+1],]

            _list_of_angles_rad = np.deg2rad(angle_list)

            if recon_method == 'mbirjax':
                _recon_block = self._mbirjax_recon(crop_data, _list_of_angles_rad, init_img).swapaxes(0, 2)
            else:
                _recon_block = self._svmbir_recon(crop_data, _list_of_angles_rad, init_img)  # swap z and x axes to get (z, x, y) order

            block_recons.append(_recon_block.astype('float32', copy=False))

        recon = np.concatenate(block_recons, axis=0) if block_recons else np.empty((0, tot_cols, tot_cols), 'float32')
        dxchange.write_tiff(recon, fname=recon_name, overwrite=True)
        print('>saving current recon to {}'.format(recon_name))
        return recon
    
    def _svmbir_recon(self, sino, angles_rad, init_img):
        import svmbir
        recon = svmbir.recon(sino=sino,
                             angles=angles_rad,
                             num_rows=sino.shape[2],
                             num_cols=sino.shape[2],
                             center_offset=self.cfg['center_offset'],
                             sharpness=self.cfg['sharpness'],
                             snr_db=self.cfg['snr_db'],
                             init_image=init_img,
                             positivity=True,
                             max_iterations=200,
                             num_threads=self.cfg['num_threads'],
                             verbose=1,
                             svmbir_lib_path='/tmp',
                             )
        return recon.astype('float32', copy=False)

    def _mbirjax_recon(self, sino, angles_rad, init_img): # optional JAX-based recon for future use; currently using svmbir for consistency with past results and speed on CPU
        import mbirjax as mj
        ct_model_for_recon = mj.ParallelBeamModel(sino.shape, angles_rad)
        ct_model_for_recon.set_params(sharpness=self.cfg['sharpness'], 
                                      det_channel_offset=self.cfg['center_offset'], 
                                      snr_db=self.cfg['snr_db'],
                                      verbose=1,
                                      )

        reconstruction_array, recond_dict = ct_model_for_recon.recon(sino, print_logs=False, weights=None)
        return reconstruction_array.astype('float32', copy=False)

    def _run_vcls(self, w_pairs, angle_list):
        # Edge alignment proposals per wavelength; merged and deduped across wavelengths
        proposals = []  # (angle, score)
        for st, end in w_pairs:
            _next_angles, _vcl_val = self._mbir_vcls_propose_angle(angle_list, st, end)
            if _next_angles.all():
                proposals.append((_next_angles, _vcl_val))
            else:
                print(f'{datetime.datetime.now()}\n >>>>>>ERROR!! null angle proposed! <<<<<<')

        # Sort all proposals across wavelengths by score desc and pick top unique angles
        proposals.sort(key=lambda x: x[1], reverse=True)
    
        return proposals[0][0]

    def _run_ea2s(self, w_pairs, angle_list):
        # Edge alignment proposals per wavelength; merged and deduped across wavelengths
        proposals = []  # (angle, score)
        for st, end in w_pairs:
            _next_angles, _scores = self._ea2s_propose_angle(angle_list, st, end)
            if _next_angles:
                proposals.extend(zip(_next_angles, _scores))
            else:
                print(f'{datetime.datetime.now()}\n >>>>>>ERROR!! null angle proposed! <<<<<<')

        # Sort all proposals across wavelengths by score desc and pick top unique angles
        proposals.sort(key=lambda x: x[1], reverse=True)

        # Select top angles while ensuring they are not too close to existing angles or each other (within 0.5 degree)
        selected_angles = []
        existing = list(angle_list)
        for ang, _ in proposals:
            close_existing = next((a for a in existing if abs(ang - a) < 0.5), None)
            if close_existing is not None:
                print(f"Angle {ang} too close to existing angle {close_existing}, skip")
                continue
            if any(abs(ang - a) < 0.5 for a in selected_angles):
                continue
            selected_angles.append(ang)
            if len(selected_angles) >= self.step:
                break
       
        return selected_angles    

    def _mbir_vcls_propose_angle(self, angle_list, st, end):
        import jax.numpy as jnp
        import mbirjax as mj
        from mbirjax.vcls import get_opt_views

        seed = 42  # Change this value to control randomness across runs
        # Set geometry parameters
        num_selected_views = len(angle_list)
        self._set_step(num_selected_views)
        recon_save_path = os.path.join(self.out_path, 'Recons', 'wav_{}_{}'.format(st, end))
        current_recon = self.get_exist_recon(recon_save_path, max(num_selected_views, 0))

        rec_roi = self.get_ROI(current_recon).swapaxes(0, 2)  # swap z and x axes to get (x, z, y) order for recon; rec_roi shape: (x, z, y)


        _init_angles = jnp.array([generate_gs_angle(i, max_angle=180.0) for i in range(self.num_ini_ang)]) # in degrees
        _angle_pool = jnp.linspace(0.0, 180.0, 
                                   self.cfg['vcls_paras']['num_candidate_views'], 
                                   endpoint=False)[1:]
        angle_candidates = jnp.deg2rad(jnp.concatenate((_init_angles, _angle_pool)))

        # Set parameters for the problem size - you can vary these, but if you make num_det_rows very small relative to
        # channels, then the generated phantom may not have an interior.
        num_views = len(angle_candidates)
        num_det_rows = rec_roi.shape[2]
        num_det_channels = rec_roi.shape[0]
        sinogram_shape = (num_views, num_det_rows, num_det_channels)

        # Create the model to contain all the geometry information
        ct_model = mj.ParallelBeamModel(sinogram_shape, angle_candidates)

        prev_selected_view_inds = np.where(np.isin(angle_candidates, jnp.deg2rad(angle_list)))[0]

        # use MBIR-VCLS method
        optimal_angle_inds, vcl_value = get_opt_views(ct_model, rec_roi, self.step, 
                                                      r_1=self.cfg['vcls_paras']['r_1'], 
                                                      r_2=self.cfg['vcls_paras']['r_2'], 
                                                      prev_selected_view_inds=prev_selected_view_inds, 
                                                      priority_order=True, verbose=0, seed=seed)
        optimal_angles = np.rad2deg(angle_candidates[optimal_angle_inds])
        
        return optimal_angles, vcl_value
    
    def _ea2s_propose_angle(self, angle_list, st, end):
        from AInCT.EA2S import angle_selection
        num_tot_ang = len(angle_list)
  
        recon_save_path = os.path.join(self.out_path, 'Recons', 'wav_{}_{}'.format(st, end))
        current_recon = self.get_exist_recon(recon_save_path, max(num_tot_ang, 0))

        rec_roi = self.get_ROI(current_recon)

        angle_list_temp = angle_list.copy()
        
        # use edge alignment method
        proposals = []  # (angle, score)
        for _ in range(self.step):
            _new_ang, _score = angle_selection(
                rec_roi,
                np.deg2rad(angle_list_temp),
                self.cfg['ea2s_paras']['hough_paras'],
                beta=1,
                gamma=1,
                angle_bin_size=1.0,
                n_jobs=-1,
                rescale_percentiles=(0.5, 99.5)
            )
            angle_list_temp = np.append(angle_list_temp, _new_ang)
            proposals.append((_new_ang, _score))

        _next_angles = [a for a, _ in proposals]
        _scores = [s for _, s in proposals]
        return _next_angles, _scores

    def _send_angles(self, next_angles, cnt):
         ## Use EIC to send out table scan 
        _simulate_only = False # to test the command
        _print_results= True
        _ipts = self.cfg['EIC_vals']['ipts']
        _eic_token = self.cfg['EIC_vals']['eic_token']
        _pv_motor = self.cfg['EIC_vals']['motor_pv']
        _p_charge = self.cfg['EIC_vals']['proton_charge']
        _exp_name = self.cfg['EIC_vals']['experiment_title']
        _usr_desc =self.cfg['EIC_vals']['scan_description']

        # pvs define
        _pv_file_name = 'BL10:Exp:IM:FileName'
        _pv_sub_dir = 'BL10:Exp:IM:SubDir'
        _pv_num_dataset = 'BL10:Exp:NumDataSets'
        _pv_set_p_charge = 'BL10:Exp:AcquirePCharge'
        _pv_scan_trig = 'ScanRDRunNq'
        
        rows = []
        _header = [_pv_motor, _pv_file_name, _pv_sub_dir, _pv_num_dataset, _pv_set_p_charge, _pv_scan_trig]
        _p_charge_1, _p_charge_2 = str(_p_charge).split('.')
        desc = f'{_usr_desc}: MCP TPX {len(next_angles)} Radiographs : {next_angles} deg'
        for ang in next_angles:
            cnt+=1
            _ang_1, _ang_2 = str(ang).split('.')
            _name = f'{_exp_name}_{_p_charge_1:0>2}_{_p_charge_2:0<2}C_Angle_{_ang_1:0>3}_{_ang_2:0<3}deg'
            rows.append([ang, _name, _name, 1, _p_charge, 0])

        eic_submit_table_scan(_ipts, _eic_token, desc, _header, rows, _simulate_only, _print_results)
