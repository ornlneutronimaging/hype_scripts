import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
import torch.optim as optim

class CNN3D(nn.Module):
    def __init__(self, num_classes):
        super(CNN3D, self).__init__()
        
        self.conv1 = nn.Conv3d(1, 32, kernel_size=(3,3,3), padding = (1,0,0), padding_mode='reflect')
        self.conv1_bn = nn.BatchNorm3d(32)
        self.pool1 = nn.MaxPool3d(kernel_size=(1,2,2), stride=1)
        
        self.conv2 = nn.Conv3d(32, 64, kernel_size=(3,3,3), padding = (1,1,1), padding_mode='reflect')
        self.conv2_bn = nn.BatchNorm3d(64)
        self.pool2 = nn.MaxPool3d(kernel_size=(1,2,2), stride=(1,2,2))
        
        self.conv3 = nn.Conv3d(64, 128, kernel_size=(2,2,2), padding = (0,1,1), padding_mode='reflect')
        self.conv3_bn = nn.BatchNorm3d(128)
        self.pool3 = nn.MaxPool3d(kernel_size=(1,2,2), stride=(1,2,2))
        
        self.conv4 = nn.Conv3d(128, 256, kernel_size=(2,2,2), padding = (1,1,1), padding_mode='reflect')
        self.conv4_bn = nn.BatchNorm3d(256)
        self.pool4 = nn.MaxPool3d(kernel_size=(1,2,2), stride=(1,2,2))
        
        self.fc5 = nn.Linear(294912, 1024)# 12*12*8*256 = 294912 12*12*8*64 = 73728
        self.fc6 = nn.Linear(1024, 512)
        self.fc7 = nn.Linear(512, num_classes)
        
        self.relu = nn.ReLU()
        self.drop = nn.Dropout(p = 0.5)

        self.sigmoid = nn.Sigmoid()
        
        # Weights initialization
        for m in self.modules():
            if isinstance(m, nn.Conv3d):
                nn.init.normal_(m.weight)
            elif isinstance(m, nn.BatchNorm3d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                m.weight.data.normal_(0, 0.02)
                m.bias.data.zero_()
        
    def forward(self, x):
        x = self.relu(self.conv1_bn(self.conv1(x)))
        x = self.pool1(x)
        
        x = self.relu(self.conv2_bn(self.conv2(x)))
        x = self.pool2(x)
        
        x = self.relu(self.conv3_bn(self.conv3(x)))
        x = self.pool3(x)
        
        x = self.relu(self.conv4_bn(self.conv4(x)))
        x = self.pool4(x)
        
        x = x.view(-1, 294912)
        
        x = self.relu(self.fc5(x))
        x = self.drop(x)

        x = self.relu(self.fc6(x))
        x = self.drop(x)

        y = self.fc7(x)
        
        return y