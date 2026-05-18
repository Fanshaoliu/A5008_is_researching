import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import time

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"

def clean_text(s):
    return re.sub(r"\s+", " ", s or "").strip()

def cite_key(authors, year, arxiv_id):
    first = authors[0].split()[-1] if authors else "arxiv"
    return re.sub(r"[^A-Za-z0-9]", "", f"{first}{year}{arxiv_id.split('.')[-1]}")

def arxiv_to_preprint(arxiv_id: str) -> str:
    """将 arXiv ID 转换为 @preprint 格式"""
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "id_list": arxiv_id,
        "max_results": 1,
    })

    xml = urllib.request.urlopen(url, timeout=20).read()
    root = ET.fromstring(xml)
    entry = root.find(f"{ATOM}entry")
    if entry is None:
        raise ValueError("No arXiv entry found")

    title = clean_text(entry.findtext(f"{ATOM}title"))
    authors = [
        clean_text(a.findtext(f"{ATOM}name"))
        for a in entry.findall(f"{ATOM}author")
    ]

    published = entry.findtext(f"{ATOM}published") or ""
    year = published[:4] if published else ""

    abs_url = clean_text(entry.findtext(f"{ATOM}id"))
    eprint = abs_url.rsplit("/", 1)[-1]
    eprint_no_version = re.sub(r"v\d+$", "", eprint)

    primary = entry.find(f"{ARXIV}primary_category")
    primary_class = primary.attrib.get("term", "") if primary is not None else ""

    doi = clean_text(entry.findtext(f"{ARXIV}doi"))
    journal_ref = clean_text(entry.findtext(f"{ARXIV}journal_ref"))

    # 使用与 hybrid.bib 中相同的引用键格式
    key = cite_key(authors, year, eprint_no_version)

    fields = {
        "author": " and ".join(authors),
        "title": title,
        "year": year,
        "eprint": eprint_no_version,
        "primaryClass": primary_class,
        "url": f"https://arxiv.org/abs/{eprint_no_version}",
    }

    if doi:
        fields["doi"] = doi
    if journal_ref:
        fields["journal"] = journal_ref

    body = "\n".join(
        f"  {k:<12} = {{{v}}},"
        for k, v in fields.items()
        if v
    )

    return f"@preprint{{{key},\n{body}\n}}"

def get_all_arxiv_ids():
    """从 hybrid.bib 文件中提取所有 arXiv ID"""
    arxiv_ids = []
    try:
        with open("hybrid.bib", "r", encoding="utf-8") as f:
            content = f.read()
            # 匹配 eprint = {数字.数字} 格式
            matches = re.findall(r'eprint\s*=\s*{(\d+\.\d+)}', content)
            arxiv_ids = list(set(matches))  # 去重
    except FileNotFoundError:
        print("错误: hybrid.bib 文件未找到")
        return []
    return arxiv_ids

def find_preprint_entry(content, arxiv_id):
    """查找包含指定 arXiv ID 的 @preprint 条目"""
    # 使用更简单的匹配方法：找到包含该 arXiv ID 的 @preprint 块
    pattern = rf'@preprint{{[^}}]+eprint\s*=\s*{{{arxiv_id}}}[^}}]*}}'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(0)
    
    # 如果上面的方法失败，尝试逐行查找
    lines = content.split('\n')
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if line.strip().startswith('@preprint{'):
            start_idx = i
        elif start_idx != -1 and line.strip() == '}':
            end_idx = i
            # 检查这个块是否包含目标 arXiv ID
            block = '\n'.join(lines[start_idx:end_idx+1])
            if f'eprint        = {{{arxiv_id}}}' in block:
                return block
            start_idx = -1
            end_idx = -1
    
    return None

def update_bib_file():
    """更新 hybrid.bib 文件中的 @preprint 条目"""
    arxiv_ids = get_all_arxiv_ids()
    if not arxiv_ids:
        print("未找到 arXiv ID")
        return

    print(f"找到 {len(arxiv_ids)} 个 arXiv ID，开始更新...")
    
    # 读取原始文件内容
    with open("hybrid.bib", "r", encoding="utf-8") as f:
        original_content = f.read()
    
    updated_content = original_content
    
    for i, arxiv_id in enumerate(arxiv_ids):
        try:
            print(f"处理第 {i+1}/{len(arxiv_ids)} 个: {arxiv_id}")
            
            # 获取新的 @preprint 条目
            new_entry = arxiv_to_preprint(arxiv_id)
            
            # 查找旧的 @preprint 条目
            old_entry = find_preprint_entry(original_content, arxiv_id)
            
            if old_entry:
                # 替换旧条目
                updated_content = updated_content.replace(old_entry, new_entry)
                print(f"✓ 已更新 {arxiv_id}")
            else:
                print(f"⚠ 未找到 {arxiv_id} 的旧条目")
            
            # 如果不是最后一个，等待5秒
            if i < len(arxiv_ids) - 1:
                print("等待5秒...")
                time.sleep(5)
                
        except Exception as e:
            print(f"处理 {arxiv_id} 时出错: {e}")
            print("继续处理下一个...")
    
    # 写入更新后的内容
    with open("hybrid.bib", "w", encoding="utf-8") as f:
        f.write(updated_content)
    
    print("\n✓ 所有条目已更新完成！")

if __name__ == "__main__":
    update_bib_file()