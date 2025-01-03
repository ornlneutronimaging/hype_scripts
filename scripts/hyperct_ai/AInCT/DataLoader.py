from .dataload_utils import *

#OB module
def get_ob(ob_base_folders, paras, clean_path, wav_st, wav_end, level = False):
    ob_paths = gen_paths(ob_base_folders) if level else ob_base_folders
    print(ob_paths)
    ob_sets = HyperData(ob_paths, paras, clean_path, wav_st, wav_end).get_sum_data()
    return np.array(ob_sets).mean(axis=0)

def OBLoader(ob_paths, paras, wav_st, wav_end, out_path, save = True): # data_path, ob_str
    #ob_base_folders = glob.glob(os.path.join(data_path, ob_str))
    ob_base_folders = ob_paths
    print(ob_base_folders)
    ob_save_path = os.path.join(out_path, 'OBs')
    dir_check(ob_save_path)
    ob_fname = os.path.join(ob_save_path, 'OB_wav_{}_{}.tiff'.format(wav_st, wav_end))
    if os.path.exists(ob_fname):
        ob = imread(ob_fname)
        print('OB exists, load {}'.format(ob_fname))
        return ob
    else:
        clean_path = os.path.join(out_path, 'clean_data', 'ob_sets')
        dir_check(clean_path)
        ob = get_ob(ob_base_folders, paras, clean_path, wav_st, wav_end)
        if save:
            dxchange.write_tiff(ob, dtype=np.float32, fname = ob_fname, overwrite=True)
            print('saving OB to {}'.format(ob_fname))
        return ob

def ProjLoader(data_path, ob_paths, proj_str, paras, cali_paras, wav_st, wav_end, out_path, save = True):
    proj_save_path = os.path.join(out_path, 'Projs', 'wav_{}_{}'.format(wav_st, wav_end))
    dir_check(proj_save_path)

    proj_base_folders = glob.glob(os.path.join(data_path, proj_str)) # get new list
    proj_paths = gen_paths(proj_base_folders)
    angle_list = info_get(proj_paths, -2, 'Angle')

    ob = OBLoader(ob_paths, paras, wav_st, wav_end, out_path, save)
    norm_data = np.empty((0, ob.shape[0], ob.shape[1]), 'float32')
    for p in proj_paths:
        _fname = os.path.join(proj_save_path, '{}.tiff'.format(p.split('/')[-2]))
        if os.path.exists(_fname):
            print('Load {}'.format(_fname))
            norm_data = np.append(norm_data, imread(_fname), axis = 0)
        else:
            clean_path = os.path.join(out_path, 'clean_data', 'projections')
            dir_check(clean_path)
            _norm_temp = ProjData([p], paras, clean_path, wav_st, wav_end, ob).get_normal_data()
            if cali_paras['if_cali']:
                cali_boxes= [[x, y, cali_paras['height'], cali_paras['width']] for x, y in zip (cali_paras['box_x'], cali_paras['box_y'])]
                _norm_temp = calibrate_background(_norm_temp, cali_boxes)
                
            norm_data = np.append(norm_data, _norm_temp, axis = 0)
            
            if save:
                dxchange.write_tiff(_norm_temp, dtype=np.float32, fname = _fname, overwrite=True)
                print('>>>>>> Save project data to {} <<<<<<'.format(_fname))

    norm_data, angle_list_rad = svmbir.sino_sort(norm_data, np.deg2rad(angle_list))

    return norm_data, np.rad2deg(angle_list_rad)


