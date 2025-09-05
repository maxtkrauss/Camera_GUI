from abc import ABC, abstractmethod
import os
import platform
import time

from pylablib.devices import Thorlabs as tl
import polanalyser as pa
import numpy as np
import tifffile
import cuvis

class Camera (ABC):
    def setup(self):
        pass
    @abstractmethod
    def set_exposure (self, time_ms):
        pass
    def get_exposure (self):
        pass
    def auto_exposure (self):
        pass
    def take_image (self):
        pass

class ThorlabsCam (Camera):
    def setup(self, base_exposure, roi, do_dark_sub: bool, dark_cal, output_dir='./'):
        self.tl_cam = tl.ThorlabsTLCamera()
        self.set_exposure(base_exposure)
        self.tl_cam.set_roi(*roi, hbin=1, vbin=1)
        self.do_dark_sub = do_dark_sub
        self.dark_cal = dark_cal
        self.output_dir = output_dir
    
    def set_exposure(self, time_ms):
        self.tl_cam.set_exposure(time_ms * 1e-3)

    def get_exposure(self):
        return self.tl_cam.get_exposure()

    def take_image (self, img_name):
        imaging_failed_counter = 0
        success = False

        while imaging_failed_counter < 15:
            print(f"TL: Taking exposure with TL cam...")

            try:
                # Capture Image
                img_tl = self.tl_cam.snap() - self.dark_cal[0] if self.do_dark_sub and self.dark_cal is not None else self.tl_cam.snap()
                img_tl = np.maximum(img_tl, 0)

                # Convert to multi-channel polarized image
                img_tl_pol = pa.demosaicing(img_raw=img_tl, code=pa.COLOR_PolarMono)
                img_tl_pol = np.append(img_tl_pol, [img_tl], axis=0)

                img_tl_pol_cropped = img_tl_pol
                chan = 0
                success = True

            except:
                imaging_failed_counter += 1
                print(f"TL: Imaging failed. Restarting cam. Counter {imaging_failed_counter}")
                self.tl_cam = self.setup(self.tl_cam.get_roi(), self.do_dark_sub, self.dark_cal)

        if success:
            path = os.path.join(self.output_dir, f"{img_name}_thorlabs.tif")
            tifffile.imwrite(path, img_tl_pol_cropped, photometric='minisblack')
            # exposure_time_tl = 1200
            print(f"TL: Saved image as TIFF. Shape: {img_tl_pol_cropped.shape}, Max: {np.max(img_tl_pol_cropped[chan])}, Min: {np.min(img_tl_pol_cropped[chan])}, Avg: {np.average(img_tl_pol_cropped[chan])}, SNR: {snr(img_tl_pol_cropped)}")
        else:
            print("TL: No image to save.")

        return success

    def auto_exposure_thorlabs(self, target_level=0.95, min_exposure=10, max_exposure=10000):
        """
        Simple function to adjust Thorlabs camera exposure for 12-bit images until
        image is just under saturation.
        
        Parameters:
        cam (ThorlabsTLCamera): The camera object
        target_level (float): Target brightness level (0.0-1.0) relative to saturation
        min_exposure (int): Minimum exposure time in ms
        max_exposure (int): Maximum exposure time in ms
        
        Returns:
        int: Final exposure time in ms
        """
        # Start with minimum exposure
        current_exposure = min_exposure
        self.set_exposure(current_exposure / 1000.0)  # Convert to seconds
        
        # Take initial image
        img = self.tl_cam.snap()
        
        # Get the maximum pixel value
        max_val = np.max(img)
        
        # Use 12-bit saturation value (2^12 - 1)
        saturation = 4095
        
        # Calculate how close we are to saturation (0.0-1.0)
        current_level = max_val / saturation
        
        print(f"Starting: Exposure={current_exposure}ms, Max pixel={max_val}, Level={current_level:.2f}, Saturation={saturation}")
        
        # Simple iterative approach
        max_iterations = 10
        for i in range(max_iterations):
            # If we're at target level, we're done
            if abs(current_level - target_level) < 0.05:
                print(f"Target reached: Exposure={current_exposure}ms, Level={current_level:.2f}")
                return current_exposure
                
            # If too dark, increase exposure; if too bright, decrease exposure
            if current_level < target_level:
                # Too dark: increase exposure
                if current_level > 0:
                    # Scale based on how far we are from target
                    factor = min(2.0, target_level / current_level)  # Limit to 2x increase
                    current_exposure = int(current_exposure * factor)
                else:
                    # If current level is zero, double the exposure
                    current_exposure *= 2
            else:
                # Too bright: decrease exposure
                factor = target_level / current_level
                current_exposure = int(current_exposure * factor)
                
            # Ensure exposure stays within limits
            current_exposure = max(min_exposure, min(max_exposure, current_exposure))
            
            # Update camera
            self.tl_cam.set_exposure(current_exposure / 1000.0)
            
            # Take new image and measure
            img = self.tl_cam.snap()
            max_val = np.max(img)
            current_level = max_val / saturation
            
            print(f"Iteration {i+1}: Exposure={current_exposure}ms, Max pixel={max_val}, Level={current_level:.2f}")
        
        print(f"Finished after {max_iterations} iterations: Exposure={current_exposure}ms, Level={current_level:.2f}")
        return current_exposure


class CubertCam (Camera):
    def setup(self, base_exposure, do_dark_sub: bool, distance, output_dir='./'):
        data_dir = os.getenv("CUVIS") if platform.system() == "Windows" else os.getenv("CUVIS_DATA")
        factory_dir = os.path.join(data_dir, "factory")
        userSettingsDir = os.path.join(data_dir, os.pardir, "settings")

        settings = cuvis.General(userSettingsDir)
        settings.set_log_level("info")

        calibration = cuvis.Calibration(factory_dir)
        self.processingContext = cuvis.ProcessingContext(calibration)
        self.acquisitionContext = cuvis.AcquisitionContext(calibration)

        saveArgs = cuvis.SaveArgs(export_dir=output_dir, allow_overwrite=True, allow_session_file=True)
        self.cuberExporter = cuvis.CubeExporter(saveArgs)

        while self.acquisitionContext.state == cuvis.HardwareState.Offline:
            print(".", end="")
            time.sleep(1)
        print("\nCubert camera is online.")

        self.acquisitionContext.operation_mode = cuvis.OperationMode.Software
        self.set_exposure(base_exposure)
        self.processingContext.calc_distance(distance)

## Take Cubert image, apply dark calibration, and save as TIFF
def take_and_save_cubert_image(img_name, dark_cal, acquContext, procContext):
    imaging_failed_counter = 0
    saved = False

    while imaging_failed_counter < 15:
        time.sleep(0.5)
        print(f"CB: Taking exposure with CB cam...")
        try:
            am = acquContext.capture()
            mesu, res = am.get(timedelta(milliseconds=3000))
        except:
            mesu = None
            imaging_failed_counter += 1
            print(f"CB: Imaging failed. Counter: {imaging_failed_counter}")

        if mesu is not None:
            mesu.set_name(f"{img_name}_cubert")
            procContext.apply(mesu)
            data_array = np.array(mesu.data['cube'].array)
            data_array = data_array.transpose(2, 0, 1)
            if do_dark_subtract_cb and dark_cal is not None:
                data_array = np.maximum(data_array.astype(float) - dark_cal.astype(float), 0)
            if snr(data_array) > 0.05:
                path = os.path.join(cubert_image_folder, f"{img_name}_cubert.tif")
                # Crop region for Cubert image
                y1, y2 = 75, 195
                x1, x2 = 116, 236
                # data_array_cropped = data_array[:, y1:y2, x1:x2]  # Crop spatial dimensions
                data_array_cropped = data_array
                tifffile.imwrite(path, data_array_cropped, photometric='minisblack')
                print(f"CB: Saved image as TIFF. Shape: {data_array_cropped.shape}, Max: {np.max(data_array_cropped)}, Min: {np.min(data_array_cropped)}, Avg: {np.average(data_array_cropped)}, SNR: {snr(data_array_cropped)}")
                saved = True
                break
            else:
                imaging_failed_counter += 1
                print(f"CB: Image saving failed. Counter: {imaging_failed_counter}")
        else:
            imaging_failed_counter += 1
            print(f"CB: Image saving failed. Counter: {imaging_failed_counter}")

    return saved

def auto_exposure_cubert(acq_ctx, proc_ctx, target_level=0.95, min_exposure=10, max_exposure=10000):
    max_possible = 4095  # 12-bit camera
    current_exposure = acq_ctx.integration_time
    max_iterations = 7

    for i in range(max_iterations):
        print(f"\n[Auto Exposure] Iteration {i+1} - Trying exposure: {current_exposure} ms")
        acq_ctx.integration_time = current_exposure

        success = False
        attempt = 0

        while attempt < 5:  # try 5 times like in take_and_save
            time.sleep(0.5)
            try:
                am = acq_ctx.capture()
                mesu, res = am.get(timedelta(milliseconds=3000))
                if mesu is not None:
                    proc_ctx.apply(mesu)
                    data_array = np.array(mesu.data['cube'].array).transpose(2, 0, 1)
                    max_val = np.max(data_array)
                    current_level = max_val / max_possible
                    print(f"  Success on try {attempt+1}: Max={max_val}, Level={current_level:.2f}")

                    if max_val == 4095:
                        print("Detected saturation. Cooling down...")
                        time.sleep(1.0)
                        for _ in range(2):
                            try:
                                flush_am = acq_ctx.capture()
                                flush_am.get(timedelta(milliseconds=2000))
                            except:
                                pass
                            
                    # Update exposure logic
                    if abs(current_level - target_level) < 0.05:
                        print(f"Target reached: Exposure={current_exposure} ms")
                        return int(current_exposure), True

                    if current_level < target_level:
                        factor = min(2.0, target_level / max(current_level, 0.01))
                        current_exposure = int(current_exposure * factor)
                    else:
                        factor = target_level / max(current_level, 0.01)
                        current_exposure = int(current_exposure * factor)

                    # Keep in bounds
                    current_exposure = max(min_exposure, min(max_exposure, current_exposure))
                    success = True
                    break
                else:
                    print(f"(WARNING) Attempt {attempt+1}: mesu is None")
            except Exception as e:
                print(f"(WARNING) Attempt {attempt+1} failed: {e}")

            attempt += 1

        if not success:
            print("Failed to get valid image after retries.")
            break

    print(f"(ERROR) Auto exposure incomplete. Final exposure: {current_exposure} ms")
    return current_exposure, False

## Calculate SNR
def snr(img, axis=None, ddof=0):
    img = np.asanyarray(img)
    m = img.mean(axis)
    sd = img.std(axis=axis, ddof=ddof)
    return np.where(sd == 0, 0, m/sd)