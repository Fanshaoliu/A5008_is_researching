#!/usr/bin/env python3
"""
更新 hybrid.tex 正文中的引用，使其与更新后的 hybrid.bib 文件保持一致
"""

import re

def extract_bib_keys():
    """从 hybrid.bib 文件中提取新的引用键映射关系"""
    bib_mapping = {}
    
    with open("hybrid.bib", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 匹配 @misc 条目，提取引用键、作者、年份和 arXiv ID
    misc_pattern = r'@misc\{(\w+),\s*author\s*=\s*{([^}]*)},\s*title\s*=\s*{([^}]*)},\s*year\s*=\s*{(\d+)},\s*eprint\s*=\s*{(\d+\.\d+)}[^}]*}'
    matches = re.findall(misc_pattern, content, re.DOTALL)
    
    for bib_key, author, title, year, arxiv_id in matches:
        # 提取第一作者的姓氏
        first_author = author.split(' and ')[0].strip()
        author_last_name = first_author.split()[-1] if first_author.split() else "unknown"
        
        # 创建映射信息
        bib_mapping[bib_key] = {
            'author': author_last_name.lower(),
            'year': year,
            'arxiv_id': arxiv_id,
            'title_keywords': re.findall(r'\b\w+\b', title.lower())[:3]  # 取标题前3个关键词
        }
        print(f"Found @misc: {bib_key} -> {author_last_name}{year}{arxiv_id.split('.')[-1][:5]}")
    
    return bib_mapping

def analyze_tex_references():
    """分析 hybrid.tex 文件中的引用"""
    with open("hybrid.tex", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 匹配所有 \cite{} 命令
    cite_pattern = r'\\cite\{([^}]+)\}'
    cites = re.findall(cite_pattern, content)
    
    # 提取所有引用键
    all_keys = []
    for cite_group in cites:
        keys = [key.strip() for key in cite_group.split(',')]
        all_keys.extend(keys)
    
    print(f"Found {len(all_keys)} unique citation keys in tex file")
    return list(set(all_keys))

def guess_mapping(tex_key, bib_mapping):
    """根据 tex_key 猜测对应的 bib_key"""
    # 分析 tex_key 的结构
    # 格式通常是: author_year_keyword
    
    # 尝试匹配作者姓氏和年份
    author_year_match = re.match(r'^(\w+)(\d{4})', tex_key)
    if author_year_match:
        author_part = author_year_match.group(1)
        year_part = author_year_match.group(2)
        
        # 在 bib_mapping 中查找匹配项
        for bib_key, bib_info in bib_mapping.items():
            if ((bib_info['author'].startswith(author_part) or 
                 author_part.startswith(bib_info['author'])) and 
                bib_info['year'] == year_part):
                return bib_key
    
    return None

def create_update_mapping():
    """创建引用键更新映射关系"""
    bib_mapping = extract_bib_keys()
    tex_keys = analyze_tex_references()
    
    update_mapping = {}
    
    print("\nAnalyzing mapping:")
    for tex_key in tex_keys:
        if tex_key.startswith("DBLP:"):
            # DBLP 引用保持原样
            print(f"  Keeping DBLP key: {tex_key}")
            continue
        
        # 尝试猜测映射
        guessed_bib_key = guess_mapping(tex_key, bib_mapping)
        if guessed_bib_key:
            update_mapping[tex_key] = guessed_bib_key
            print(f"  Mapping: {tex_key} -> {guessed_bib_key}")
        else:
            print(f"  No mapping found for: {tex_key}")
    
    return update_mapping

def update_tex_file():
    """更新 hybrid.tex 文件中的引用"""
    update_mapping = create_update_mapping()
    
    print("\nFinal update mapping:")
    for old_key, new_key in update_mapping.items():
        print(f"  {old_key} -> {new_key}")
    
    if not update_mapping:
        print("No mappings found to update")
        return
    
    # 读取原始文件
    with open("hybrid.tex", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 更新引用
    updated_content = content
    for old_key, new_key in update_mapping.items():
        # 替换单个引用
        updated_content = re.sub(
            rf'\\cite\{{({re.escape(old_key)})}}',
            rf'\\cite{{{new_key}}}',
            updated_content
        )
        # 替换多个引用中的特定键
        updated_content = re.sub(
            rf'(?<!\w){re.escape(old_key)}(?!\w)',
            new_key,
            updated_content
        )
    
    # 写入更新后的内容
    with open("hybrid.tex", "w", encoding="utf-8") as f:
        f.write(updated_content)
    
    print("\n✓ 正文引用已更新完成！")

if __name__ == "__main__":
    update_tex_file()