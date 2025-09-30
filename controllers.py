import os
import json

from widgets import ChooseDataSetWidget, DataCollectionWidget, CreateDatasetWidget, MainWindow

class CompuHSIDataset:
    def __init__ (self):
        self.dark_frame_extension: str = "dark_frames"
        self.test_extension: str = "test"
        self.train_extension: str = "train"
        self.gt_cam_name: str = "cubert"
        self.im_cam_name: str = "thorlabs"
        self.gt_crop_size: int = 120
        self.gt_crop_offset: tuple[int, int]= (0,0)
        self.im_crop_size: int = 660
        self.im_crop_offset: tuple[int, int] = (0,0)
        self.test_size: int = 0
        self.train_size: int = 0
        self.test_assignment_probability: int = 20

    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__, 
            sort_keys=True,
            indent=4)
    
    @classmethod
    def fromJson(json: object):
        new_ds = CompuHSIDataset()
        for attr in dir(json):
            setattr(new_ds, attr, getattr(json, attr))
        return new_ds

    @classmethod
    def load (path):
        with open(path, 'r') as file:
            return CompuHSIDataset.fromJson(json.load(file))
        
    def save (self, path):
        with open(path, 'w') as file:
            file.write(self.toJSON())

    @property
    def df_path (self):
        return os.path.join(self.base_dir, self.dark_frame_extension)
    @property
    def ts_path (self):
        return os.path.join(self.base_dir, self.test_extension)
    @property
    def tr_path (self):
        return os.path.join(self.base_dir, self.train_extension)
    
    def initialize (self):
        os.makedirs(self.df_path, exist_ok=True)
        os.makedirs(self.ts_path, exist_ok=True)
        os.makedirs(self.tr_path, exist_ok=True)

        self.save(os.path.join(self.base_dir, "ds.json"))

class DataCollectionController:

    def __init__(self, main_window: MainWindow, file_select: ChooseDataSetWidget, data_collect: DataCollectionWidget, create_dataset: CreateDatasetWidget):
        self.dataset = None

        self.main_window = main_window
        self.file_select = file_select
        self.data_collect = data_collect
        self.create_dataset = create_dataset

        self.file_select.new_dataset_button.clicked.connect(self.create_data_set)
        self.file_select.existing_dataset_button.clicked.connect(self.load_data_set)

        # self.create_dataset.gt_cropper.

    def load_data_set (self):
        tentative_dir = self.file_select.directory_input.text()

        if not os.path.isfile(tentative_dir):
            return
        
        self.dataset = CompuHSIDataset.load(tentative_dir)

        self.main_window.navigate(0)

    def create_data_set (self):
        tentative_dir = self.file_select.directory_input.text()

        if not os.path.isdir(tentative_dir):
            return
        
        self.dataset = CompuHSIDataset()

        self.main_window.navigate(1)
