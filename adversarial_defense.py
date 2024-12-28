import torch
from torchvision import models, transforms, datasets
from torch.utils.data import DataLoader
import torch.nn.functional as F
import logging
import numpy as np

# 配置日志记录
logging.basicConfig(filename='accuracy_attack.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 加载预训练的ResNet50模型
model = models.resnet50(pretrained=True)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)  # 将模型移动到设备上
model.eval()  # 设置为评估模式

# 定义数据转换，包含对抗防御步骤
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# 对抗防御函数 - 添加随机高斯噪声
def add_gaussian_noise(tensor, mean=0., std=0.02):
    noise = torch.randn(tensor.size()) * std + mean
    noisy_tensor = tensor + noise.to(device)
    return torch.clamp(noisy_tensor, 0., 1.)  # 确保像素值仍在[0,1]范围内

# 加载ImageNet验证集
val_dataset = datasets.ImageFolder(root='adversarial_samples', transform=transform)
val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

# 定义函数来计算准确率
def calculate_accuracy(model, dataloader):
    correct = 0
    total = 0
    with torch.no_grad():
        for i, (data, target) in enumerate(dataloader):
            data, target = data.to(device), target.to(device)  # 将数据移动到设备上

            # 应用对抗防御
            data = add_gaussian_noise(data)

            output = model(data)
            _, predicted = torch.max(output.data, 1)
            total += target.size(0)
            correct += (predicted == target).sum().item()
            print(f"batch {i+1}, Accuracy: {correct / total * 100:.2f}%")
            logging.info(f"batch {i+1}, Accuracy: {correct / total * 100:.2f}%")
    return correct / total

# 计算准确率
accuracy = calculate_accuracy(model, val_loader)
print(f"ResNet50在ImageNet验证集上的准确率为: {accuracy * 100:.2f}%")