import yaml, datetime, svmbir, dxchange
import pandas as pd
from skimage.io import imread
# %%
# Need install ctqa and AInCT first
from AInCT.DataLoader import ProjLoader
from AInCT.Calibrator import NICalibrator
from AInCT.Evaluator import CNNEVA
from AInCT.EA2S import angle_selection
from AInCT.utils import *
from AInCT.dataload_utils import crop
# %%
class AIRobo(object):
    def __init__(self, cfg_file, mode = "Run", wavIdx = 100, angle_mode = 'golden'):
        self.mode = mode
        self.angle_mode = angle_mode
        self.cfg = yaml.safe_load(open(cfg_file, 'r', encoding = 'utf-8'))
        
        _exp_name = self.cfg['experiment_title']
        self.proj_str = f'*{_exp_name}*'
        self.out_path = os.path.join(self.cfg['OutPath'], self.proj_str[1:-1])
        dir_check(self.out_path)

        self.data_path = self.cfg['DataPath']

        self.center_offset =  self.cfg['center_offset']
        self.step = self.cfg['step']
        self.Z_START = self.cfg['Z_START']
        self.Z_NUM = self.cfg['Z_NUM']

        self.angle_propose_flag = self.cfg['angle_propose_flag']

        _w_st = self.cfg['wav_idx_start']
        if wavIdx < len(_w_st):
            self.w_st = [self.cfg['wav_idx_start'][wavIdx]]
            self.w_end = [self.cfg['wav_idx_end'][wavIdx]]
            print("Processing data from {}th to {}th wavelength".format(self.w_st[0], self.w_end[0]))
        else:
            self.w_st = self.cfg['wav_idx_start']
            self.w_end = self.cfg['wav_idx_end']
        
        if self.mode == 'cali':
            self.calibrator = NICalibrator(self.cfg['DataPath'], self.cfg['cali_str'], 0, 1200)
        elif self.mode == 'recon':  
            self.norm_data, self.recon = [], []
            for st, end in zip(self.w_st, self.w_end):
                _norm_data, self.angle_list = self.proj_load(st, end)
                _recon = self.Recon(_norm_data, st, end)
                self.norm_data.append(_norm_data.copy())
                self.recon.append(_recon.copy())
            
            file_name = os.path.join(self.out_path, 'angle_list_real.csv')
            df = pd.DataFrame({'Index': np.arange(1, len(self.angle_list)+1).tolist(),'Angle': self.angle_list})
            df.to_csv(file_name)
        elif self.mode == 'evaluate':
            ResQueues = [[], [], []] #RecScore_Queue, SubseqScore_Queue, QI_Queue
            for st, end in zip(self.w_st, self.w_end):
                _qi = self.EVA(st, end)
                ResQueues = Enqueue(ResQueues, [_qi.recon_score, _qi.subseq_score, _qi.QI])
            
            num_tot_ang = _qi.num_tot_ang
            self.recon_score = np.mean(ResQueues[0])
            self.subseq_score = np.mean(ResQueues[1]) if any(ResQueues[1]) else None
            self.QI = np.mean(ResQueues[2]) if any(ResQueues[2]) else None

            print('Recon Ang_num_{:03d} score is {:.3f}'.format(num_tot_ang, self.recon_score))
            print('Subsequent improvement from Ang_num_{:03d} is {}'.format(num_tot_ang-self.step, self.subseq_score))
            print('Comprehensive QI of Ang_num_{:03d} is {}'.format(num_tot_ang, self.QI))

            if self.QI is not None and self.QI > self.cfg['QIthresh']:
                self.cfg['angle_propose_flag'] = False
                with open(cfg_file, 'w') as file:
                    yaml.dump(self.cfg, file, default_flow_style=False)
                print(f'{datetime.datetime.now()}\n >>>>>> Reach expected quality, Experiment is stopped <<<<<<')
            elif num_tot_ang >= self.cfg['Max_ang_num']:
                self.cfg['angle_propose_flag'] = False
                with open(cfg_file, 'w') as file:
                    yaml.dump(self.cfg, file, default_flow_style=False)
                print(f'{datetime.datetime.now()}\n >>>>>> Reach pre-set maximum scans, Experiment is stopped <<<<<<')
            else:
                print(f'{datetime.datetime.now()}\n >>>>>> Need new angles proposing <<<<<<')
            
        elif self.mode == 'angle':
            if self.angle_propose_flag:
                Angles = []
                for st, end in zip(self.w_st, self.w_end):
                    _next_angles, num_tot_ang = self.propose_angle(st, end)
                    Angles.append(_next_angles)
                self.next_angles = np.mean(Angles, axis = 0)
                print(self.next_angles)

                print(f'{datetime.datetime.now()}\n >>>>>> Sending new angles [{self.angle_mode}]<<<<<<')
                file_name = os.path.join(self.out_path, 'angle_list_setting.csv')
                self.save_data(file_name, np.arange(num_tot_ang + 1, 
                                                    num_tot_ang + 1 + len(_next_angles)).tolist(),
                                                    self.next_angles)                
                print(f'{datetime.datetime.now()} > {self.next_angles =}')
                
                ## Use EIC to send out table scan 
                simulate_only = True # to test the command
                print_results= True
                _run_title = self.cfg['scan_description']
                _p_charge = self.cfg['proton_charge']
                _motor_pv = self.cfg['EIC_vals']['motor_pv']
                _exp_name = self.cfg['experiment_title']
                _ipts = self.cfg['ipts']

                header = [['MCPFile', _motor_pv, 'Delay', 'MCPAcquire', 'Wait For', 'Value', 'MCPAcquire', 'BL10:Exp:Scan:ForceTrig', 'Delay']]

                p_charge_1, p_charge_2 = str(_p_charge).split('.')
                
                for _ang in self.next_angles:
                    _ang_1, _ang_2 =f'{_ang:.3f}'.split('.')
                    _name = f'{_exp_name}_{p_charge_1:0>2}_{p_charge_2:0<2}C_Angle_{_ang_1:0>3}_{_ang_2:0<3}deg'
                    _mcp_path =(f'E:\\data\\IPTS-{_ipts}\\{_name}\\{_name}')    
                    _row = [[[_mcp_path, _ang, 15, 1, 'pCharge', _p_charge, 0, 1, 20]]]
                    desc =[f'MCP TPX Radiograph: angle {_ang}˚']
                    # send out init scans
                    eic_submit_table_scan(desc, header, _row, simulate_only, print_results)        
            else: 
                print(f'{datetime.datetime.now()} > No need propse angles')
        else:
            print('ERROR, no proper mode settings!!!')

    def save_data(self, file_name, index, data):
        ct = datetime.datetime.now()
        time_str = ct.isoformat(timespec='seconds')
        if not os.path.exists(file_name):
            df = pd.DataFrame({'Time': [time_str]*self.step, 
                               'Index':index,'Angle/deg': data})
            df.to_csv(file_name)
        else:
            new_df = pd.DataFrame({'Time': [time_str]*self.step,
                                   'Index': index, 'Angle/deg': data})
            final_df = pd.concat([pd.read_csv(file_name, index_col=0), new_df], 
                                 axis = 0)
            final_df.to_csv(file_name)

    def get_ROI(self, data):
        roi = self.cfg['roi_info']
        if data is None:
            return None
        else:
            temp = data.copy()
            return temp[:, roi['roi_x'] : roi['roi_x'] + roi['roi_height'], roi['roi_y'] : roi['roi_y'] + roi['roi_width']]
        
    def proj_load(self, st, end):
        # Load Data
        # ToF mode
        norm_data, angle_list = ProjLoader(self.data_path, self.cfg['ob_local_path'], self.proj_str, self.cfg['load_paras'], 
                                           self.cfg['background_cali_paras'], st, end,
                                           self.out_path, save = True)
        
        # resonance mode with normlized data
        """
        fl_list = glob.glob(os.path.join(self.data_path, '*.tiff'))
        fl_list.sort()
        norm_data = np.array([imread(fl).astype(np.float32) for fl in fl_list], dtype = np.float32)
        
        angle_list = []
        for fl in fl_list:
            temp_list = os.path.split(fl)[-1].split('_')
            pt = temp_list.index('Angle')
            angle_list.append(np.float_('.'.join([temp_list[pt+1], temp_list[pt+2][:-5]])))
        angle_list = np.array(angle_list)
        """
        print(angle_list)

        return norm_data, angle_list

    def Recon(self, norm_data, st, end):
        # Reconstruction
        num_tot_ang = len(self.angle_list)

        recon_save_path = os.path.join(self.out_path, 'Recons', 'wav_{}_{}'.format(st, end))
        dir_check(recon_save_path)

        pre_recon = self.get_exist_recon(recon_save_path, max(num_tot_ang - self.step, 0))
        recon = self.gen_recon(recon_save_path, norm_data, 180 - self.angle_list,
                            (None if pre_recon is None else pre_recon.copy()))
        return recon

    def EVA(self, st, end):
        _, self.angle_list = self.proj_load(st, end)
        num_tot_ang = len(self.angle_list)
        res_save_path = os.path.join(self.out_path, 'Results', 'wav_{}_{}'.format(st, end))
        dir_check(res_save_path)
        
        if num_tot_ang==50: 
            self.step = 2
        recon_save_path = os.path.join(self.out_path, 'Recons', 'wav_{}_{}'.format(st, end))
        pre_recon = self.get_exist_recon(recon_save_path, max(num_tot_ang - self.step, 0))
        current_recon = self.get_exist_recon(recon_save_path, max(num_tot_ang, 0))

        pre_roi, rec_roi = self.get_ROI(pre_recon), self.get_ROI(current_recon)

        quality = CNNEVA(pre_roi, rec_roi, num_tot_ang, self.Z_NUM,
                         self.step, self.cfg['eva_paras'], res_save_path)
                
        return quality
    
    def propose_angle(self, st, end):
        _, self.angle_list = self.proj_load(st, end)
        num_tot_ang = len(self.angle_list )
        res_save_path = os.path.join(self.out_path, 'Results', 'wav_{}_{}'.format(st, end))
        dir_check(res_save_path)

        recon_save_path = os.path.join(self.out_path, 'Recons', 'wav_{}_{}'.format(st, end))
        current_recon = self.get_exist_recon(recon_save_path, max(num_tot_ang, 0))

        rec_roi = self.get_ROI(current_recon)

        angle_list_temp = self.angle_list.copy()
        _next_angles = []
        if self.angle_mode == 'golden':
            for i in range(self.step):
                _new_ang = generate_gs_angle(num_tot_ang+i, 180)
                _next_angles.append(_new_ang)
 
        if self.angle_mode == 'preset':
            _pre_set_angle_list = [7.71082381, 242.5702746, 360, 15.42080578, 237.9102855, 355.3400109, 
                          20.08079488, 230.2003035, 347.6300289, 27.79077685, 217.8303325, 342.9700398, 
                          40.16074792, 210.1203505, 335.2600579, 47.87072989, 205.4603614, 327.5500759, 
                          52.530719, 197.7503794, 322.8900868, 60.24070097, 190.0403974, 315.1801048, 
                          67.95068294, 185.3804083, 302.8101337, 72.61067204, 177.6704264, 295.1001518, 
                          80.32065401, 165.3004553, 290.4401627, 92.69062509, 157.5904733, 282.7301807, 
                          100.4006071, 152.9304842, 275.0201987, 105.0605962, 145.2205023, 270.3602096, 
                          112.7705781, 137.5105203, 262.6502277, 120.4805601, 132.8505312, 257.9902385, 
                          125.1405492, 250.2802566]
            _next_angles = _pre_set_angle_list[num_tot_ang:num_tot_ang+self.step]

        if self.angle_mode == 'edge':
            for i in range(self.step):
                _new_ang = angle_selection(rec_roi, np.deg2rad(angle_list_temp),
                                           self.cfg['canny_paras'], self.cfg['hough_paras'],
                                           mode='fix', gamma = 2)
                angle_list_temp = np.append(angle_list_temp, _new_ang)
                _next_angles.append(_new_ang)
        
        return _next_angles, num_tot_ang

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
        crop_cols = self.cfg['crop_cols']
        tot_cols = crop_cols[1] - crop_cols[0]

        if os.path.exists(recon_name):
            recon = imread(recon_name)
            print('load recon from {}'.format(recon_name))
        else:
            recon = np.empty((0, tot_cols, tot_cols), 'float32')
            index = [0] + (self.Z_NUM)
            for idx, z_start, z_numSlice in zip(range(len(self.Z_START)), self.Z_START, self.Z_NUM):
                crop_data = crop(norm_data, z_start=z_start, crop_cols=crop_cols, z_numSlice=z_numSlice )
                print(f'cropped data size: {crop_data.shape}')
                cnt = sum(index[:idx+1])
                init_img = 0.0 if pre_recon is None else pre_recon[cnt:cnt+z_numSlice,]
                _recon_temp = svmbir.recon(sino = crop_data, angles=np.deg2rad(angle_list),
                                           num_rows = crop_data.shape[2], num_cols = crop_data.shape[2],
                                           center_offset = self.cfg['center_offset'], sharpness=self.cfg['sharpness'],
                                           snr_db = self.cfg['snr_db'], init_image = init_img, 
                                           positivity= False, max_iterations = 200,
                                           num_threads= self.cfg['num_threads'], verbose=0,
                                           svmbir_lib_path = '/tmp',)
                recon = np.append(recon, _recon_temp, axis = 0)
            dxchange.write_tiff(recon, fname = recon_name, overwrite=True)
            print('saving current recon to {}'.format(recon_name))
        return recon
