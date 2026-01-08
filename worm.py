#!/usr/bin/env python3
"""
修复并发问题的GitHub Trending爬虫
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
import aiohttp
from bs4 import BeautifulSoup
import httpx

# 数据结构和之前的定义保持不变
@dataclass
class GitHubRepo:
    name: str
    url: str
    description: Optional[str]
    stars: int
    forks: int
    language: Optional[str]
    today_stars: Optional[int] = None

class GitHubTrendingScraper:
    BASE_URL = "https://github.com/trending"
    
    def __init__(self, language: str = "", since: str = "daily"):
        self.language = language
        self.since = since
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/vnd.github.v3+json"
            },
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def _build_url(self) -> str:
        url = self.BASE_URL
        if self.language:
            url += f"/{self.language}"
        url += f"?since={self.since}"
        return url
    
    async def fetch_page(self) -> str:
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        url = self._build_url()
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"爬取 {self.language or 'all'} 失败: {e}")
            return ""
    
    async def scrape(self) -> List[GitHubRepo]:
        """主爬取方法，返回仓库列表"""
        html = await self.fetch_page()
        if not html:
            return []
        
        soup = BeautifulSoup(html, "html.parser")
        repos = []
        repo_elements = soup.find_all("article", class_="Box-row")
        
        for repo_element in repo_elements:
            try:
                # 提取仓库名称和URL
                title_element = repo_element.find("h2", class_="h3")
                if not title_element:
                    continue
                    
                link = title_element.find("a")
                if not link:
                    continue
                    
                repo_name = link.get_text(strip=True).replace(" ", "")
                repo_url = f"https://github.com{link['href']}"
                
                # 提取描述
                desc_element = repo_element.find("p", class_="col-9")
                description = desc_element.get_text(strip=True) if desc_element else None
                
                # 提取编程语言
                lang_element = repo_element.find("span", itemprop="programmingLanguage")
                language = lang_element.get_text(strip=True) if lang_element else None
                
                # 提取星标和fork数量
                stars_elements = repo_element.find_all("a", class_="Link--muted")
                stars = 0
                forks = 0
                today_stars = None
                
                for elem in stars_elements:
                    text = elem.get_text(strip=True)
                    href = elem.get("href", "")
                    
                    if "stargazers" in href:
                        stars_text = text.replace(",", "").replace("k", "000")
                        if "stars today" in text:
                            today_match = text.split()
                            if today_match:
                                today_stars_text = today_match[0].replace(",", "")
                                today_stars = int(today_stars_text) if today_stars_text.isdigit() else None
                        else:
                            # 提取数字部分
                            import re
                            numbers = re.findall(r'\d+', stars_text)
                            if numbers:
                                stars = int(''.join(numbers))
                    
                    elif "forks" in href:
                        forks_text = text.replace(",", "")
                        import re
                        numbers = re.findall(r'\d+', forks_text)
                        if numbers:
                            forks = int(''.join(numbers))
                
                repo = GitHubRepo(
                    name=repo_name,
                    url=repo_url,
                    description=description,
                    stars=stars,
                    forks=forks,
                    language=language,
                    today_stars=today_stars
                )
                
                repos.append(repo)
                
            except Exception as e:
                continue
        
        return repos

async def scrape_single_language(language: str, since: str = "daily") -> Tuple[str, List[GitHubRepo]]:
    """爬取单个语言的趋势仓库"""
    try:
        async with GitHubTrendingScraper(language=language, since=since) as scraper:
            repos = await scraper.scrape()
            return language, repos
    except Exception as e:
        print(f"爬取 {language} 时出错: {e}")
        return language, []

async def concurrent_scrape(languages: List[str], since: str = "daily") -> dict:
    """
    并发爬取多种语言趋势
    
    Args:
        languages: 语言列表，如 ["python", "javascript", "go", "rust"]
        since: 时间范围，可选 "daily", "weekly", "monthly"
    
    Returns:
        字典格式: {语言: [仓库列表]}
    """
    print(f"开始并发爬取 {len(languages)} 种语言趋势...")
    
    # 创建所有语言的爬取任务
    tasks = [scrape_single_language(lang, since) for lang in languages]
    
    # 并发执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=False)
    
    # 整理结果
    all_results = {}
    successful = 0
    
    for language, repos in results:
        if repos:  # 有结果才算成功
            successful += 1
            all_results[language] = repos
            print(f"  ✓ {language}: 爬取到 {len(repos)} 个仓库")
        else:
            print(f"  ✗ {language}: 爬取失败或没有数据")
    
    print(f"完成！成功爬取 {successful}/{len(languages)} 种语言")
    return all_results

def save_results_to_json(results: dict, filename: str = "github_trending_all.json"):
    """保存所有结果到JSON文件"""
    output_data = {
        "metadata": {
            "fetched_at": datetime.now().isoformat(),
            "total_languages": len(results),
            "total_repos": sum(len(repos) for repos in results.values())
        },
        "data": {}
    }
    
    for language, repos in results.items():
        output_data["data"][language] = [
            {
                "name": repo.name,
                "url": repo.url,
                "description": repo.description,
                "stars": repo.stars,
                "forks": repo.forks,
                "language": repo.language,
                "today_stars": repo.today_stars
            }
            for repo in repos
        ]
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"所有数据已保存到 {filename}")

def print_summary(results: dict, top_n: int = 5):
    """打印摘要信息"""
    print("\n" + "="*60)
    print("GitHub Trending 多语言趋势摘要")
    print("="*60)
    
    for language, repos in results.items():
        if not repos:
            continue
            
        print(f"\n【{language.upper()}】")
        # 按今日星标排序（如果有的话）
        repos_with_today = [r for r in repos if r.today_stars]
        if repos_with_today:
            sorted_repos = sorted(repos_with_today, key=lambda x: x.today_stars or 0, reverse=True)[:top_n]
            sort_by = "今日新增星标"
        else:
            sorted_repos = sorted(repos, key=lambda x: x.stars, reverse=True)[:top_n]
            sort_by = "总星标数"
        
        print(f"排序方式: {sort_by}")
        for i, repo in enumerate(sorted_repos, 1):
            today_text = f"(今日+{repo.today_stars})" if repo.today_stars else ""
            print(f"  {i:2d}. {repo.name:40} ⭐ {repo.stars:>6} {today_text:10}")

async def main():
    """主函数"""
    print("GitHub Trending 多语言爬虫")
    print("-" * 40)
    
    # 配置要爬取的语言
    languages = ["python", "javascript", "go", "rust", "java", "typescript"]
    
    # 示例1：爬取单个语言（Python）
    print("\n1. 单独爬取 Python 趋势:")
    async with GitHubTrendingScraper(language="python", since="daily") as scraper:
        python_repos = await scraper.scrape()
        print(f"   爬取到 {len(python_repos)} 个Python仓库")
        
        # 显示前3个
        for i, repo in enumerate(python_repos[:3], 1):
            print(f"     {i}. {repo.name} - {repo.stars} stars")
    
    # 示例2：并发爬取多种语言
    print(f"\n2. 并发爬取 {len(languages)} 种语言:")
    all_results = await concurrent_scrape(languages, since="daily")
    
    # 保存结果
    save_results_to_json(all_results)
    
    # 打印摘要
    print_summary(all_results)
    
    # 统计信息
    total_repos = sum(len(repos) for repos in all_results.values())
    print(f"\n总计: {total_repos} 个仓库")

# 运行主程序
if __name__ == "__main__":
    asyncio.run(main())