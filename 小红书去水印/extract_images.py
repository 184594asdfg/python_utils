import requests
import re
import json
import os
import time
from datetime import datetime

# 读取content.txt文件，提取小红书链接
with open('content.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取小红书链接
link_pattern = r'https://www\.xiaohongshu\.com/[^\s]+'
links = re.findall(link_pattern, content)

if not links:
    print("未找到小红书链接")
    exit()

xiaohongshu_link = links[0]
print(f"提取到的小红书链接: {xiaohongshu_link}")

# 访问小红书链接
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://www.xiaohongshu.com/'
}

response = requests.get(xiaohongshu_link, headers=headers)
if response.status_code != 200:
    print(f"访问链接失败，状态码: {response.status_code}")
    exit()

# 保存页面源代码到文件，以便分析
with open('page_source.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("页面源代码已保存到 page_source.html 文件")

# 提取所有以http://sns-webpic-qc.xhscdn.com开头的图片链接
# 从meta标签中提取og:image
image_patterns = [
    r'<meta name="og:image" content="(http://sns-webpic-qc\.xhscdn\.com/[^"\']+)"',
    r'http://sns-webpic-qc\.xhscdn\.com/[^"\'\s]+'
]

image_links = []
for pattern in image_patterns:
    matches = re.findall(pattern, response.text)
    # 如果是meta标签的匹配，取第一个捕获组
    if pattern.startswith('<meta'):
        image_links.extend(matches)
    else:
        image_links.extend(matches)

# 过滤出有效的图片链接
valid_image_links = []
for link in image_links:
    # 确保链接以图片格式结尾或包含图片相关后缀
    if any(ext in link.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', 'webp']):
        valid_image_links.append(link)

image_links = valid_image_links

# 读取现有的总链接记录（记录网页地址）
total_links_file = "总链接记录.json"
if os.path.exists(total_links_file):
    with open(total_links_file, 'r', encoding='utf-8') as f:
        total_webpage_links = json.load(f)
else:
    total_webpage_links = []

# 检查网页地址是否已经存在
webpage_exists = xiaohongshu_link in total_webpage_links
if webpage_exists:
    print("该网页地址已经存在于总链接记录中，跳过下载步骤，但仍然创建记录文件")

# 去重
unique_image_links = list(set(image_links))

print(f"提取到 {len(unique_image_links)} 个图片链接")
for link in unique_image_links:
    print(link)

# 创建文件夹结构，添加日期时间戳
current_time = datetime.now().strftime("%m月%d日_%H时%M分%S秒")
output_dir = f"小红书图片_{current_time}"
download_dir = os.path.join(output_dir, "下载图片")

if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# 保存为json文件，包含网页链接和解析的图片地址
json_file = os.path.join(output_dir, "image_links.json")
# 当网页链接存在时，image_links设为空数组
if webpage_exists:
    links_data = {
        "webpage_link": xiaohongshu_link,
        "image_links": [],
        "exists_in_total_records": "链接已存在"
    }
else:
    links_data = {
        "webpage_link": xiaohongshu_link,
        "image_links": unique_image_links,
        "exists_in_total_records": "链接不存在"
    }
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(links_data, f, ensure_ascii=False, indent=2)

print(f"图片链接已保存到 {json_file} 文件")

# 仅当网页地址不存在时，才添加到总链接记录中
if not webpage_exists:
    total_webpage_links.append(xiaohongshu_link)
    total_webpage_links = list(set(total_webpage_links))
    
    # 保存到总的链接记录文件
    with open(total_links_file, 'w', encoding='utf-8') as f:
        json.dump(total_webpage_links, f, ensure_ascii=False, indent=2)
    
    print(f"网页地址已添加到总链接记录.json 文件，当前共有 {len(total_webpage_links)} 个网页链接")
else:
    print(f"网页地址已存在于总链接记录中，当前共有 {len(total_webpage_links)} 个网页链接")

# 下载图片，仅当网页地址不存在时下载
if not webpage_exists:
    print(f"开始下载 {len(unique_image_links)} 张图片...")
    
    for i, link in enumerate(unique_image_links):
        try:
            # 生成文件名，根据链接中的扩展名
            if 'webp' in link.lower():
                filename = f"image_{i+1}.webp"
            elif 'jpg' in link.lower() or 'jpeg' in link.lower():
                filename = f"image_{i+1}.jpg"
            elif 'png' in link.lower():
                filename = f"image_{i+1}.png"
            elif 'gif' in link.lower():
                filename = f"image_{i+1}.gif"
            else:
                filename = f"image_{i+1}.jpg"
            
            file_path = os.path.join(download_dir, filename)
            
            # 下载图片，添加headers
            # 为图片下载添加额外的Referer
            image_headers = headers.copy()
            image_headers['Referer'] = xiaohongshu_link
            
            response = requests.get(link, headers=image_headers, timeout=15)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"下载成功: {filename}")
            else:
                print(f"下载失败: {link}, 状态码: {response.status_code}")
        except Exception as e:
            print(f"下载出错: {link}, 错误: {str(e)}")
        
        # 下载后延时1秒，避免请求过快
        print("下载间隔1秒")
        time.sleep(1)
else:
    print("跳过下载步骤，因为该网页地址已经存在于总链接记录中")

print("下载完成！")
