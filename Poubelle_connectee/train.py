from model import *  
from loader import *  
import matplotlib.pyplot as plt 
import argparse  
import torch  
import torch.nn as nn  
import torchvision.models as models  
import torch.optim as optim 
import torchvision.transforms as transforms  
import numpy as np
import sys

if sys.version_info[0] == 2:
    import cPickle as pickle
else:
    import pickle
import math
from skimage.transform import resize
import scipy
from scipy import interpolate

np.random.seed(111)
torch.cuda.manual_seed_all(111)
torch.manual_seed(111)

NUM_EPOCHS = 25  
LEARNING_RATE = 0.001  
BATCH_SIZE = 10  
RESNET_LAST_ONLY = False  

def train(dataloaders, dataset_sizes, class_names, weightlist, model, optimizer, criterion, epoch, num_epochs):
    model.train()
    epoch_loss = 0.0
    epoch_acc = 0.0
    
    for batch_idx, (images, labels) in enumerate(dataloaders['train']):
        optimizer.zero_grad()
        if torch.cuda.is_available():
            images, labels = images.cuda(), labels.cuda()
        outputs = model.forward(images)
        loss = criterion(outputs, labels)
        _, preds = torch.max(outputs.data, 1)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
        epoch_acc += torch.sum(preds == labels).item()
    
    epoch_loss /= dataset_sizes['train']
    epoch_acc /= dataset_sizes['train']
    
    print('TRAINING Epoch %d/%d Loss %.4f Accuracy %.4f' % (epoch, num_epochs, epoch_loss, epoch_acc))
    return epoch_loss, epoch_acc

import sklearn.metrics as metric

def test(dataloaders, dataset_sizes, class_names, weightlist, criterion, model, repeats=2):
    model.eval()
    test_loss = 0.0
    test_acc = 0.0
    f1_score = 0.0
    f1_score_w = 0.0
    conf_mat = np.zeros([len(class_names),len(class_names)])
    
    with torch.no_grad():
        for itr in range(repeats):
            for batch_idx, (images, labels) in enumerate(dataloaders['test']):
                if torch.cuda.is_available():
                    images, labels = images.cuda(), labels.cuda()
                outputs = model.forward(images)
                _, preds = torch.max(outputs.data, 1)
                predlabels = preds.cpu().numpy()
                labels_num = labels.cpu().numpy()
                for ind,label in enumerate(labels_num):
                    conf_mat[label,predlabels[ind]] += 1
                loss = criterion(outputs, labels)
                test_loss += loss.item()
                test_acc += torch.sum(preds == labels).item()
                f1_score += metric.f1_score(labels_num, predlabels,labels=[0,1,2,3,4,5], average='weighted', zero_division='warn')
                f1_score_w += metric.f1_score(labels_num, predlabels,labels=[0,1,2,3,4,5], average='macro', zero_division='warn')

        test_loss /= (dataset_sizes['test']*repeats)
        test_acc /= (dataset_sizes['test']*repeats)
        f1_score /= (dataset_sizes['test']*repeats)

        print('Test Loss: %.4f Test Accuracy %.4f Weighted: %.4f Macro: %.4f' % (test_loss, test_acc, f1_score, f1_score_w))
        return test_loss, test_acc, conf_mat

def val(dataloaders, dataset_sizes, class_names, weightlist, criterion, model, repeats=2):
    model.eval()
    test_loss = 0.0
    test_acc = 0.0
    
    with torch.no_grad():
        for itr in range(repeats):
            for batch_idx, (images, labels) in enumerate(dataloaders['val']):
                if torch.cuda.is_available():
                    images, labels = images.cuda(), labels.cuda()
                outputs = model.forward(images)
                loss = criterion(outputs, labels)
                _, preds = torch.max(outputs.data, 1)
                test_loss += loss.item()
                test_acc += torch.sum(preds == labels).item()

        test_loss /= (dataset_sizes['val']*repeats)
        test_acc /= (dataset_sizes['val']*repeats)
        print('Val Loss: %.4f Val Accuracy %.4f' % (test_loss, test_acc))
        return test_loss, test_acc

def imshow(inp, title=None):
    inp = inp.numpy().transpose((1, 2, 0))
    inp = np.clip(inp, 0, 1)
    plt.axis("off")
    plt.imshow(inp)
    if title is not None:
        plt.title(title)
    plt.pause(1)

def visualize_model(dataloaders, dataset_sizes, class_names, weightlist, criterion, model, num_images=8):
    images_so_far = 0
    fig = plt.figure()

    for batch_idx, (images, labels) in enumerate(dataloaders['test']):
        if torch.cuda.is_available():
            images, labels = images.cuda(), labels.cuda()
        outputs = model(images)
        _, preds = torch.max(outputs.data, 1)
        for j in range(images.size()[0]):
            images_so_far += 1
            print('class: {} predicted: {}'.format(class_names[labels.data[j]], class_names[preds[j]]))
            imshow(images.cpu().data[j])
            if images_so_far == num_images:
                return

def train_test_script(root_path):
    data_transforms = {
        'train': transforms.Compose([
            transforms.Resize((384, 384)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]),
        'test': transforms.Compose([
            transforms.Resize((384, 384)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    }

    image_datasets_train = Dataset_Souf(root_path, fold="train", transform=data_transforms['train'], target_transform=None)
    image_datasets_val = Dataset_Souf(root_path, fold="val", transform=data_transforms['test'], target_transform=None)
    image_datasets_test = Dataset_Souf(root_path, fold="test", transform=data_transforms['test'], target_transform=None)

    dataloader_train = torch.utils.data.DataLoader(image_datasets_train, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)
    dataloader_val = torch.utils.data.DataLoader(image_datasets_val, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)
    dataloader_test = torch.utils.data.DataLoader(image_datasets_test, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)

    dataloaders = {'train': dataloader_train, 'test': dataloader_test, 'val':dataloader_val}
    dataset_sizes = {
        'train': len(image_datasets_train),
        'test': len(image_datasets_test),
        'val': len(image_datasets_val)
    }

    class_names = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'rien']
    model = PreTrainedResNet(len(class_names), RESNET_LAST_ONLY)
    if torch.cuda.is_available():
        model = model.cuda()
    optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE, momentum=0.9, weight_decay=1e-3)
    weightlist = [1,1,1,1,1,1]
    weightlist = torch.Tensor(weightlist)
    if torch.cuda.is_available():
        weightlist = weightlist.cuda()
    criterion = nn.CrossEntropyLoss(weight=weightlist)

    train_loss_list = []
    train_acc_list = []
    val_loss_list = []
    val_acc_list = []

    for epoch in range(NUM_EPOCHS):
        t1,t2 = train(dataloaders, dataset_sizes, class_names, weightlist, model, optimizer, criterion, epoch+1, NUM_EPOCHS)
        train_loss_list.append(t1)
        train_acc_list.append(t2)
        if (epoch+1) % 5 == 0:
            t1,t2 = val(dataloaders, dataset_sizes, class_names, weightlist, criterion, model)
            val_loss_list.append(t1)
            val_acc_list.append(t2)

    torch.save(model.state_dict(), "model.pth")
    print("Modèle sauvegardé")
    print("Finished Training")
    print("-"*10)

    x = np.arange(5, 25)
    x_train = np.arange(0,25)
    x1 = [5, 10, 15, 20, 25]
    f_loss = interpolate.interp1d(x1, val_loss_list)
    f_accuracy = interpolate.interp1d(x1, val_acc_list)

    val_acc = f_accuracy(x)
    val_loss = f_loss(x)
    
    print("Loss and Accuracy Plots:")
    plt.figure()
    plt.plot(x_train, train_loss_list)
    plt.plot(x, val_loss)
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'validation'])
    plt.show()
    
    plt.figure()
    plt.plot(x_train, train_acc_list)
    plt.plot(x, val_acc)
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'validation'])
    plt.show()

    print("Now testing")
    t1,t2,conf_mat = test(dataloaders, dataset_sizes, class_names, weightlist, criterion, model)
    print('Conf Mat\n',conf_mat)

    for i in range(6):
        conf_mat[i,:] = conf_mat[i,:]/sum(conf_mat[i,:])

    print("Confusion Matrix Visualization:")
    plt.figure()
    plt.imshow(conf_mat, cmap='hot')
    plt.xticks([0,1,2,3,4,5],class_names)
    plt.yticks([0,1,2,3,4,5],class_names)
    plt.colorbar()
    plt.show()

    print("Visualization of Network's output on random test data:")
    visualize_model(dataloaders, dataset_sizes, class_names, weightlist, criterion, model)
