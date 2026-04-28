import glob
import os
from functools import partial
from multiprocessing import Pool
import numpy as np
import dxchange
from .utils import dir_check, extract_angle_from_name
import h5py
from .preprocessing_utils import replace_bad_pixels, correct_alignment
import svmbir  # Required for sinogram sorting


"""
Note:
the projection dir is directly provided, not using searching anymore. 
because the data saving structure is currently fixed.
"""
class DataHandler:
    def __init__(self, config, use_clean_data=False, num_workers=4, use_neunorm=False):
        """
        Handles OB and projection pipelines with optional pre-processing.

        Args:
            out_path (str): Directory for saving output data.
            config (dict): Configuration dictionary (from YAML file).
            use_clean_data (bool): Whether to preprocess the data before normalization.
            num_workers (int): Number of processes for multiprocessing.
            use_neunorm (bool): Flag to enable NeuNorm library integration for preprocessing (if available).
        """
        self.out_path = config['out_path']
        #config.get("out_path", out_path)  # Prioritize value from config, fallback to argument
        self.use_clean_data = config.get("use_clean_data", use_clean_data)
        self.num_workers = config.get("num_workers", num_workers)
        self.use_neunorm = config.get("use_neunorm", use_neunorm)
        self.swap_axes = config.get("swap_axes", False)
        self.config = config  # Keep the full config for accessing other options

        # Ensure the output directory exists
        dir_check(self.out_path)

    @staticmethod
    def _as_bool(val):
        if isinstance(val, str):
            return val.strip().lower() in {"1", "true", "yes", "y", "on"}
        return bool(val)

    ###
    ### NeuNorm Preprocessing Integration
    ###
    def preprocess_with_neunorm(self, frame):
        """
        Optional wrapper for using NeuNorm for preprocessing.
        This placeholder can easily be updated to integrate NeuNorm functionality in the future.

        Args:
            frame (np.ndarray): Input image frame.

        Returns:
            np.ndarray: Preprocessed frame.
        """
        if self.use_neunorm:
            # Replace this with actual NeuNorm preprocessing logic (when it becomes available)
            raise NotImplementedError("NeuNorm preprocessing is not yet implemented.")
        else:
            return self.preprocess_frame(frame)

    ###
    ### Open Beam (OB) Data Processing
    ###
    def process_ob(self, wav_start, wav_end):
        """
        Process all Open Beam (OB) data from the provided config["ob_list"].

        Args:
            wav_start (int): Start wavelength index.
            wav_end (int): End wavelength index.

        Returns:
            np.ndarray: Averaged OB data across OB folders.
        """
        ob_save_path = os.path.join(self.out_path, f"OBs/OB_wav_{wav_start}_{wav_end}.tiff")
        if os.path.exists(ob_save_path):
            print(f"OB already exists: {ob_save_path}")
            return dxchange.read_tiff(ob_save_path)

        clean_path = None
        if self.use_clean_data:
            clean_path = os.path.join(
                self.out_path,
                "clean_data",
                f"ob_sets_wav_{wav_start}_{wav_end}",
            )
            dir_check(clean_path)

        ob_list = self.config["ob_list"]
        ob_data = []

        for ob_folder in ob_list:
            print(f"> Processing OB folder: {ob_folder}")
            raw_data = self.load_hyper_spectral(ob_folder, wav_start, wav_end)

            if self.use_clean_data:
                # Preprocess raw data using NeuNorm (if enabled)
                clean_data = [self.preprocess_with_neunorm(im) for im in raw_data]
                self.save_clean_frames(
                    clean_data,
                    clean_path,
                    os.path.basename(ob_folder),
                )
                summed_ob = np.sum(clean_data, axis=0)  # Collapse cleaned bands into 512x512
            else:
                # Direct summation of raw data
                summed_ob = np.sum(raw_data, axis=0)

            ob_data.append(summed_ob)

        # Average OBs together to create the final OB dataset
        final_ob = np.mean(ob_data, axis=0)
        dxchange.write_tiff(final_ob, dtype=np.float32, fname=ob_save_path, overwrite=True)
        print(f"Saved averaged OB data to: {ob_save_path}")
        return final_ob

    ###
    ### Projection Data Processing
    ###
    def process_projections(self, wav_start, wav_end, ob_data):
        """
        Process projection data, handle normalization with OB, and sort sinograms.

        Args:
            proj_path (str): Path to the base directory for projections.
            #proj_search_pattern (str): Pattern for filtering projection folders.
            wav_start (int): Start wavelength index.
            wav_end (int): End wavelength index.
            ob_data (np.ndarray): Processed OB data for normalization.

        Returns:
            tuple: Normalized projection data and sorted angle list in degrees.
        """
        proj_path = self.config.get("proj_path")
        proj_folders = glob.glob(os.path.join(proj_path, "*"))
        #[f for f in glob.glob(os.path.join(self.data_path, "*")) if proj_search_pattern in f]
        proj_save_path = os.path.join(self.out_path, f"Projs/wav_{wav_start}_{wav_end}")
        dir_check(proj_save_path)

        clean_path = None
        if self.use_clean_data:
            clean_path = os.path.join(
                self.out_path,
                "clean_data",
                f"proj_sets_wav_{wav_start}_{wav_end}",
            )
            dir_check(clean_path)

        angle_list = []  # Collect angles for reconstruction 
        norm_data = np.empty((0, ob_data.shape[0], ob_data.shape[1]), "float32")

        for proj_folder in proj_folders:
            proj_name = os.path.basename(proj_folder)
            save_file = os.path.join(proj_save_path, f"{proj_name}.tiff")

            # Skip already processed projections; rely on existing norm_sino merge later
            if os.path.exists(save_file):
                print(f"Skipping already processed projection: {proj_name}")
                continue

            # Extract angle from folder name for new projections only
            angle = extract_angle_from_name(proj_name)
            print(f"> Processing projection folder: {proj_folder} at angle: {angle}")
            angle_list.append(angle)

            raw_proj = self.load_hyper_spectral(proj_folder, wav_start, wav_end)

            if self.use_clean_data:
                clean_data = [self.preprocess_with_neunorm(im) for im in raw_proj]
                self.save_clean_frames(
                    clean_data,
                    clean_path,
                    proj_name,
                )
                summed_proj = np.sum(clean_data, axis=0)
            else:
                summed_proj = np.sum(raw_proj, axis=0)

            norm_proj = -np.log(summed_proj / ob_data)
            norm_proj = np.nan_to_num(norm_proj, nan=0, posinf=0, neginf=0)

            dxchange.write_tiff(norm_proj, dtype=np.float32, fname=save_file, overwrite=True)
            norm_data = np.append(norm_data, [norm_proj], axis=0)

        # If no new projections, just return the merged existing set
        if len(angle_list) == 0:
            norm_sino_dir = os.path.join(self.out_path, "norm_sino")
            dir_check(norm_sino_dir)
            existing_norm, existing_angles = self._load_existing_norm(norm_sino_dir, wav_start, wav_end)
            if existing_norm is None:
                return norm_data, np.array([])
            return existing_norm, existing_angles

        # Sort current batch by angle
        angle_list = np.array(angle_list)
        norm_data, angle_list_rad = svmbir.sino_sort(norm_data, np.deg2rad(angle_list))

        # Merge with any existing normalized data (incremental saving)
        norm_sino_dir = os.path.join(self.out_path, "norm_sino")
        dir_check(norm_sino_dir)
        existing_norm, existing_angles = self._load_existing_norm(norm_sino_dir, wav_start, wav_end)

        if existing_norm is not None:
            combined_norm = np.concatenate([existing_norm, norm_data], axis=0)
            combined_angles_deg = np.concatenate([existing_angles, np.rad2deg(angle_list_rad)], axis=0)
            combined_norm, combined_angles_rad = svmbir.sino_sort(combined_norm, np.deg2rad(combined_angles_deg))
            norm_data, angle_list_rad = combined_norm, combined_angles_rad

        # Persist normalized data and angles for reuse in a central folder, filename records count
        num_proj = norm_data.shape[0]
        h5_path = os.path.join(
            norm_sino_dir,
            f"normalized_sino_wav_{wav_start}_{wav_end}_n{num_proj}.h5",
        )

        if os.path.exists(h5_path):
            os.remove(h5_path)

        with h5py.File(h5_path, "w") as hf:
            hf.create_dataset(
                "norm_data",
                data=norm_data.astype(np.float32, copy=False),
                compression="gzip",
            )
            hf.create_dataset(
                "angles_deg",
                data=np.rad2deg(angle_list_rad).astype(np.float32, copy=False),
                compression="gzip",
            )

        # Remove legacy norm files for this wavelength window; keep only the latest
        pattern = os.path.join(
            norm_sino_dir,
            f"normalized_sino_wav_{wav_start}_{wav_end}_n*.h5",
        )
        for old in glob.glob(pattern):
            if old != h5_path:
                try:
                    os.remove(old)
                except OSError:
                    print(f"Warning: could not remove old norm file: {old}")

        return norm_data, np.rad2deg(angle_list_rad)

    ###
    ### Helper Functions
    ###
    def load_hyper_spectral(self, folder, wav_start, wav_end, chunk_size=500):
        """
        Load hyperspectral data using multiprocessing if the range exceeds chunk_size bands.

        Args:
            folder (str): Folder path containing TIFF files.
            wav_start (int): Start wavelength index.
            wav_end (int): End wavelength index.
            chunk_size (int): Number of bands to load per chunk.

        Returns:
            np.ndarray: A concatenated 3D hyperspectral image stack [Z x H x W].
        """
        
        load_batches = sorted(glob.glob(f"{folder}/*.tif*"))[wav_start:wav_end]
        
        if len(load_batches) > chunk_size:
            stack = []
            with Pool(processes=self.num_workers) as pool:
                chunks = [load_batches[i:i + chunk_size] for i in range(0, len(load_batches), chunk_size)]
                for chunk in chunks:
                    worker = partial(self._load_stack_worker, swap_axes=self.swap_axes)
                    stack.extend(pool.map(worker, chunk))
        else:
            worker = partial(self._load_stack_worker, swap_axes=self.swap_axes)
            stack = [worker(f) for f in load_batches]

        return np.stack(stack, axis=0)

    @staticmethod
    def _load_stack_worker(file, swap_axes=True):
        img = dxchange.read_tiff(file)
        return np.swapaxes(img, 0, 1) if swap_axes else img

    def preprocess_frame(self, frame):
        frame = replace_bad_pixels(frame, self.config.get("correct_radius", 3))
        frame = correct_alignment(
            frame,
            self.config.get("x_offset", 0),
            self.config.get("y_offset", 0),
            self.config.get("cent_x", frame.shape[1] // 2),
            self.config.get("cent_y", frame.shape[0] // 2),
        )
        return frame

    def _load_existing_norm(self, norm_sino_dir, wav_start, wav_end):
        """Load the latest existing norm/angle file if present."""
        pattern = os.path.join(norm_sino_dir, f"normalized_sino_wav_{wav_start}_{wav_end}_n*.h5")
        files = sorted(glob.glob(pattern))
        if not files:
            return None, None

        latest = files[-1]
        with h5py.File(latest, "r") as hf:
            norm = hf["norm_data"][:]
            angles_deg = hf["angles_deg"][:]
        return norm, angles_deg

    def save_clean_frames(self, clean_data, save_path, data_type):
        # Keep each stack in its own subfolder; name files using the stack's data_type
        stack_dir = os.path.join(save_path, data_type)
        dir_check(stack_dir)
        for i, frame in enumerate(clean_data):
            file_label = f"{data_type}_clean_{i:04d}"
            file_path = os.path.join(stack_dir, f"{file_label}.tiff")
            dxchange.write_tiff(frame, dtype=np.float32, fname=file_path, overwrite=True)
