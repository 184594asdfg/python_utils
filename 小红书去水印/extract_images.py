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

print(f"提取到 {len(links)} 个小红书链接")
for i, link in enumerate(links):
    print(f"链接 {i+1}: {link}")

# 读取现有的总链接记录（记录网页地址）
total_links_file = "总链接记录.json"
if os.path.exists(total_links_file):
    with open(total_links_file, 'r', encoding='utf-8') as f:
        total_webpage_links = json.load(f)
else:
    total_webpage_links = []

# 访问每个小红书链接
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://www.xiaohongshu.com/'
}

# 创建文件夹结构，添加日期时间戳
current_time = datetime.now().strftime("%m月%d日_%H时%M分%S秒")
output_dir = f"小红书图片_{current_time}"
download_dir = os.path.join(output_dir, "下载图片")

if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# 用于存储每个网页链接对应的图片链接
webpage_image_map = {}
processed_links = []
existing_links = []
new_links = []

# 处理每个链接
for link_index, xiaohongshu_link in enumerate(links):
    print(f"\n正在处理链接 {link_index+1}: {xiaohongshu_link}")
    
    # 检查网页地址是否已经存在
    webpage_exists = xiaohongshu_link in total_webpage_links
    
    # 访问小红书链接
    response = requests.get(xiaohongshu_link, headers=headers)
    if response.status_code != 200:
        print(f"访问链接失败，状态码: {response.status_code}")
        continue
    
    # 提取所有以http://sns-webpic-qc.xhscdn.com开头的图片链接
    # 从meta标签中提取og:image
    image_patterns = [
        r'<meta name="og:image" content="(http://sns-webpic-qc\.xhscdn\.com/[^"]+)"',
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
            # 清理链接中的额外内容
            if ');background-repeat' in link:
                link = link.split(');background-repeat')[0]
            valid_image_links.append(link)
    
    image_links = valid_image_links
    
    # 去重
    unique_image_links = list(set(image_links))
    
    print(f"提取到 {len(unique_image_links)} 个图片链接")
    for link in unique_image_links:
        print(link)
    
    # 存储网页链接和对应的图片链接
    # 如果链接已存在，将图片链接设为空数组
    if webpage_exists:
        webpage_image_map[xiaohongshu_link] = []
    else:
        webpage_image_map[xiaohongshu_link] = unique_image_links
    
    processed_links.append(xiaohongshu_link)
    
    if webpage_exists:
        print("该网页地址已经存在于总链接记录中，跳过下载步骤")
        existing_links.append(xiaohongshu_link)
    else:
        # 仅当网页地址不存在时，才添加到总链接记录中
        total_webpage_links.append(xiaohongshu_link)
        total_webpage_links = list(set(total_webpage_links))
        
        # 保存到总的链接记录文件
        with open(total_links_file, 'w', encoding='utf-8') as f:
            json.dump(total_webpage_links, f, ensure_ascii=False, indent=2)
        
        print(f"网页地址已添加到总链接记录.json 文件，当前共有 {len(total_webpage_links)} 个网页链接")
        new_links.append(xiaohongshu_link)

# 收集所有图片链接用于下载
total_image_links = []
for links_list in webpage_image_map.values():
    total_image_links.extend(links_list)

# 去重
total_unique_image_links = list(set(total_image_links))

# 保存所有图片链接为json文件
json_file = os.path.join(output_dir, "image_links.json")

# 构建链接数据，调整为对象+数组+对象的形式
data_array = []
for webpage_link, image_links in webpage_image_map.items():
    # 检查链接是否在总链接记录中存在
    is_existing = webpage_link in existing_links
    status = "在总链接中存在" if is_existing else "新链接"
    data_array.append({
        "webpage_link": webpage_link,
        "image_links": image_links,
        "status": status
    })

links_data = {
    "data": data_array,
    "total_links_processed": len(processed_links),
    "total_images_extracted": len(total_unique_image_links),
    "existing_links": [] if existing_links else existing_links,
    "new_links": new_links
}

with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(links_data, f, ensure_ascii=False, indent=2)

print(f"\n所有图片链接已保存到 {json_file} 文件")

# 下载图片（只下载新链接的图片）
if new_links and total_unique_image_links:
    print(f"开始下载 {len(total_unique_image_links)} 张图片...")
    
    for i, link in enumerate(total_unique_image_links):
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
            image_headers['Referer'] = processed_links[0] if processed_links else 'https://www.xiaohongshu.com/'
            
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
elif new_links:
    print("\n没有图片链接需要下载")
else:
    print("\n所有链接都已存在，跳过下载步骤")

print("\n所有链接处理完成！")