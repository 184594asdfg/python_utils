import re
import json
import requests
import os
import time
from datetime import datetime

# 配置参数
API_KEY = "4aNqSDcISSmuf6DFaOc5JG4Zf5"  # 请替换为实际的API密钥
#API_URL = "https://api.wxshares.com/api/qsy/as"  # 去水印接次的 200次的
API_URL = "https://api.wxshares.com/api/qsy/plus"  # 去水印接次的 100次的

# 读取content.txt文件
def read_content_file():
    with open('content.txt', 'r', encoding='utf-8') as f:
        return f.read()

# 提取抖音和小红书链接
def extract_links(content):
    # 提取抖音链接，能够匹配包含连字符和下划线的链接，并且末尾可以有斜杠或没有斜杠
    douyin_pattern = r'https://v\.douyin\.com/[a-zA-Z0-9\-_]+/?'
    douyin_links = re.findall(douyin_pattern, content)
    
    # 提取小红书链接
    xiaohongshu_pattern = r'https://www\.xiaohongshu\.com/[\w\-\./\?=&#]+'
    xiaohongshu_links = re.findall(xiaohongshu_pattern, content)
    
    # 合并所有链接
    all_links = douyin_links + xiaohongshu_links
    return all_links

# 读取总的链接记录
def read_all_links_record():
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    record_file = os.path.join(script_dir, 'all_links.json')
    if os.path.exists(record_file):
        try:
            with open(record_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('processed_links', [])
        except Exception as e:
            print(f"读取链接记录文件失败: {e}")
            return []
    else:
        return []

# 更新总的链接记录
def update_all_links_record(new_links):
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    record_file = os.path.join(script_dir, 'all_links.json')
    existing_links = read_all_links_record()
    
    # 合并新链接，去重
    all_links = list(set(existing_links + new_links))
    
    # 保存记录
    data = {
        'processed_links': all_links,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"更新链接记录成功，共记录 {len(all_links)} 个链接")
        print(f"链接记录文件位置: {record_file}")
    except Exception as e:
        print(f"更新链接记录文件失败: {e}")

# 生成JSON文件
def generate_json_file(links, folder):
    data = []
    for i, link in enumerate(links):
        data.append({
            "id": i + 1,
            "original_link": link,
            "status": "pending"
        })
    
    json_path = os.path.join(folder, 'douyin_links.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"生成了包含 {len(links)} 个链接的JSON文件: {json_path}")
    return data

# 创建下载文件夹
def create_download_folder():
    # 使用更清晰的文件夹名称格式，不包含年份
    timestamp = datetime.now().strftime('%m月%d日_%H时%M分%S秒')
    folder_name = f"抖音下载_{timestamp}"
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

# 调用去水印接口
def get_no_watermark_url(original_url):
    # 使用用户提供的去水印接口
    try:
        response = requests.get(API_URL, params={"key": API_KEY, "url": original_url}, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # 根据实际API返回格式处理
        if result.get("code") == 200:
            data = result.get("data", {})
            # 检查是否有视频链接
            video_url = data.get("url")
            if video_url:
                # 清理视频链接中的空格和反引号
                clean_video_url = video_url.strip().strip('`')
                return {"type": "video", "url": clean_video_url}
            # 检查是否有图片数组
            pics = data.get("pics", [])
            if pics:
                # 清理图片链接中的空格和反引号
                clean_pics = []
                for pic in pics:
                    clean_pic = pic.strip().strip('`')
                    clean_pics.append(clean_pic)
                return {"type": "images", "urls": clean_pics}
            # 检查是否有单个图片链接
            photo = data.get("photo")
            if photo:
                clean_photo = photo.strip().strip('`')
                return {"type": "image", "url": clean_photo}
            # 没有找到有效的链接
            print("API返回成功，但未找到有效的链接")
            return None
        else:
            print(f"API返回错误: {result.get('msg')}")
            return None
    except Exception as e:
        print(f"获取去水印链接失败: {e}")
        return None

# 下载文件
def download_file(url, folder, filename):
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        # 获取文件类型
        content_type = response.headers.get('Content-Type', '')
        if 'image' in content_type:
            # 图片文件
            if not filename.endswith('.jpg') and not filename.endswith('.png') and not filename.endswith('.jpeg'):
                filename = filename.replace('.mp4', '.jpg')
        elif 'video' in content_type:
            # 视频文件
            if not filename.endswith('.mp4'):
                filename = filename.replace('.jpg', '.mp4')
        
        file_path = os.path.join(folder, filename)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"下载成功: {filename}")
        return file_path
    except Exception as e:
        print(f"下载失败: {e}")
        return None

# 主函数
def main():
    # 步骤1：读取文件内容
    content = read_content_file()
    
    # 步骤2：提取链接（抖音和小红书）
    links = extract_links(content)
    print(f"提取到 {len(links)} 个链接")
    
    # 步骤3：读取现有的链接记录，过滤掉已处理的链接
    existing_links = read_all_links_record()
    new_links = [link for link in links if link not in existing_links]
    duplicate_links = [link for link in links if link in existing_links]
    
    if duplicate_links:
        print(f"发现 {len(duplicate_links)} 个重复链接，将跳过处理")
        print(f"重复链接: {duplicate_links}")
    
    if not new_links:
        print("没有新链接需要处理，程序将退出")
        return
    
    print(f"需要处理的新链接数: {len(new_links)}")
    
    # 步骤4：创建下载文件夹
    download_folder = create_download_folder()
    print(f"创建下载文件夹: {download_folder}")
    
    # 在下载文件夹中创建子文件夹存放下载的文件
    files_folder = os.path.join(download_folder, "下载文件")
    os.makedirs(files_folder, exist_ok=True)
    print(f"创建文件存放文件夹: {files_folder}")
    
    # 步骤5：生成JSON文件
    links_data = generate_json_file(new_links, download_folder)
    
    # 步骤5：处理每个链接
    for i, item in enumerate(links_data):
        original_link = item['original_link']
        print(f"\n处理链接 {i+1}/{len(links_data)}: {original_link}")
        
        # 获取去水印链接
        result = get_no_watermark_url(original_link)
        if not result:
            links_data[i]['status'] = 'failed'
            continue
        
        links_data[i]['result'] = result
        
        # 根据返回的数据类型处理
        if result['type'] == 'video':
            # 下载视频
            filename = f"video_{i+1}.mp4"
            download_path = download_file(result['url'], files_folder, filename)
            if download_path:
                links_data[i]['status'] = 'success'
                links_data[i]['download_path'] = download_path
            else:
                links_data[i]['status'] = 'failed'
        elif result['type'] == 'image':
            # 下载单个图片
            filename = f"image_{i+1}.jpg"
            download_path = download_file(result['url'], files_folder, filename)
            if download_path:
                links_data[i]['status'] = 'success'
                links_data[i]['download_path'] = download_path
            else:
                links_data[i]['status'] = 'failed'
        elif result['type'] == 'images':
            # 下载图片数组
            download_paths = []
            for j, pic_url in enumerate(result['urls']):
                filename = f"image_{i+1}_{j+1}.jpg"
                download_path = download_file(pic_url, files_folder, filename)
                if download_path:
                    download_paths.append(download_path)
                # 每张图片之间也添加小延迟
                print("等待1秒后下载下一张图片...")
                time.sleep(1)
            if download_paths:
                links_data[i]['status'] = 'success'
                links_data[i]['download_paths'] = download_paths
            else:
                links_data[i]['status'] = 'failed'
        
        # 添加延迟，避免对API服务器造成过大压力
        print("等待2秒后处理下一个链接...")
        time.sleep(2)
    
    # 更新JSON文件，添加处理结果
    json_path = os.path.join(download_folder, 'douyin_links.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(links_data, f, ensure_ascii=False, indent=2)
    
    # 统计处理信息
    total_links = len(links_data)
    success_links = 0
    total_files = 0
    
    for item in links_data:
        if item.get('status') == 'success':
            success_links += 1
            # 统计下载的文件数量
            if 'download_path' in item:
                total_files += 1
            elif 'download_paths' in item:
                total_files += len(item['download_paths'])
    
    print(f"\n处理完成！")
    print(f"下载文件夹: {download_folder}")
    print(f"JSON文件: {json_path}")
    print(f"\n统计信息:")
    print(f"- 处理链接总数: {total_links}")
    print(f"- 成功处理链接数: {success_links}")
    print(f"- 下载文件总数: {total_files}")
    
    # 步骤6：更新总的链接记录，只添加处理成功的链接
    successful_links = [item['original_link'] for item in links_data if item.get('status') == 'success']
    if successful_links:
        update_all_links_record(successful_links)
    else:
        print("没有成功处理的链接，跳过更新链接记录")

if __name__ == "__main__":
    main()
