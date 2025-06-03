import os
import os.path as osp
from torch.utils.data import Dataset
from PIL import Image
import sys
if sys.version_info[0] == 2:
   import cPickle as pickle
else:
   import pickle

class Dataset_Sofiane(Dataset):
   def __init__(self, root, fold="train", transform=None, target_transform=None):        
       fold = fold.lower()
       
       if fold not in ["train", "test", "val"]:
           raise RuntimeError("Not train-val-test")

       self.root = os.path.expanduser(root)
       self.transform = transform
       self.target_transform = target_transform
       
       self.datalist_dir = os.path.join(self.root, f'{fold}_list.txt')
       self.img_label_list = []
       
       with open(self.datalist_dir, 'r') as f:
           for line in f:
               if line[0] == '#' or len(line.strip()) == 0:
                   continue
               img_name, label = line.strip().split()
               self.img_label_list.append((img_name, label))

   def __getitem__(self, index):
       img_name, label = self.img_label_list[index]
       target = 0  
       
       label_map = {
           'cardboard': 0,
           'glass': 1,
           'metal': 2,
           'paper': 3,
           'plastic': 4,
           'rien': 5
       }
       
       target = label_map[label]
       img = Image.open(os.path.join(self.root, label, img_name)).convert('RGB')

       if self.transform:
           img = self.transform(img)
           
       if self.target_transform:
           target = self.target_transform(target)

       return img, target

   def __len__(self):
       return len(self.img_label_list)