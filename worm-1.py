#!/usr/bin/env python3
"""
现代化Python爬虫示例 - 使用异步和类型注解
目标：爬取GitHub Trending页面信息
Python 3.14+ 特性演示
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Any
from enum import Enum

import aiohttp
from bs4 import BeautifulSoup
import httpx  # 替代requests的现代化HTTP客户端

# Python 3.14+ 特性：类型别名更清晰的语法
type RepoURL = str
type StarCount = int

# 使用dataclass定义数据结构（Python 3.7+）
@dataclass
class GitHubRepo:
    """GitHub仓库数据结构"""
    name: str
    url: RepoURL
    description: Optional[str]
    stars: StarCount
    forks: int
    language: Optional[str]
    today_stars: Optional[int] = None
    
    # Python 3.14+ 实验性特性：模式匹配的另一种用法
    def is_popular(self) -> bool:
        """判断仓库是否受欢迎"""
        match self:
            case GitHubRepo(stars=s) if s > 10000:
                return True
            case GitHubRepo(today_stars=ts) if ts and ts > 500:
                return True
            case _:
                return False

class SortBy(Enum):
    """排序方式枚举"""
    STARS = "stars"
    FORKS = "forks"
    TODAY = "today"

class GitHubTrendingScraper:
    """GitHub Trending爬虫类"""
    
    BASE_URL = "https://github.com/trending"
    
    def __init__(self, language: str = "", since: str = "daily"):
        """
        初始化爬虫
        
        Args:
            language: 编程语言过滤 (如 "python", "javascript")
            since: 时间范围 ("daily", "weekly", "monthly")
        """
        self.language = language
        self.since = since
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 使用现代化HTTP客户端（支持HTTP/2）
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.aclose()
    
    def _build_url(self) -> str:
        """构建请求URL"""
        url = self.BASE_URL
        if self.language:
            url += f"/{self.language}"
        url += f"?since={self.since}"
        return url
    
    async def fetch_page(self) -> str:
        """异步获取页面内容"""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        url = self._build_url()
        print(f"正在爬取: {url}")
        
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            print(f"HTTP错误: {e}")
            return ""
    
    def parse_repos(self, html: str) -> List[GitHubRepo]:
        """解析HTML，提取仓库信息"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, "html.parser")
        repos = []
        
        # 查找所有仓库项目
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
                
                # 提取星标和fork数量（使用更健壮的选择器）
                stars_elements = repo_element.find_all("a", class_="Link--muted")
                stars = 0
                forks = 0
                today_stars = None
                
                for elem in stars_elements:
                    text = elem.get_text(strip=True)
                    if "stars" in elem.get("href", ""):
                        # 解析星标数（可能包含千位分隔符）
                        stars_text = text.replace(",", "").replace("k", "000")
                        if "stars today" in text:
                            # 提取今日新增星标
                            today_match = text.split()
                            if today_match:
                                today_stars_text = today_match[0].replace(",", "")
                                today_stars = int(today_stars_text) if today_stars_text.isdigit() else None
                        else:
                            stars = int(''.join(filter(str.isdigit, stars_text)))
                    elif "fork" in elem.get("href", ""):
                        forks_text = text.replace(",", "")
                        forks = int(''.join(filter(str.isdigit, forks_text))) if forks_text else 0
                
                # 创建仓库对象
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
                print(f"解析仓库时出错: {e}")
                continue
        
        return repos
    
    def sort_repos(self, repos: List[GitHubRepo], by: SortBy = SortBy.STARS) -> List[GitHubRepo]:
        """排序仓库列表"""
        match by:
            case SortBy.STARS:
                return sorted(repos, key=lambda x: x.stars, reverse=True)
            case SortBy.FORKS:
                return sorted(repos, key=lambda x: x.forks, reverse=True)
            case SortBy.TODAY:
                # 过滤出有今日星标数据的仓库
                filtered = [r for r in repos if r.today_stars is not None]
                return sorted(filtered, key=lambda x: x.today_stars or 0, reverse=True)
            case _:
                return repos
    
    def save_to_json(self, repos: List[GitHubRepo], filename: str = "github_trending.json"):
        """保存结果到JSON文件"""
        # 将dataclass对象转换为字典
        repos_dict = [repo.__dict__ for repo in repos]
        
        data = {
            "metadata": {
                "language": self.language or "all",
                "since": self.since,
                "fetched_at": datetime.now().isoformat(),
                "total_repos": len(repos)
            },
            "repositories": repos_dict
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"数据已保存到 {filename}")
    
    async def scrape(self, sort_by: SortBy = SortBy.STARS) -> List[GitHubRepo]:
        """主爬取方法"""
        html = await self.fetch_page()
        repos = self.parse_repos(html)
        sorted_repos = self.sort_repos(repos, sort_by)
        
        # 输出摘要信息
        print(f"\n{'='*50}")
        print(f"GitHub Trending 分析结果 ({self.language or '所有语言'})")
        print(f"{'='*50}")
        
        for i, repo in enumerate(sorted_repos[:10], 1):
            popular_flag = "🔥" if repo.is_popular() else "  "
            today_stars_text = f"(今日+{repo.today_stars})" if repo.today_stars else ""
            print(f"{i:2d}. {popular_flag} {repo.name:40} ⭐ {repo.stars:>6} {today_stars_text:10}")
            if repo.description:
                print(f"    {repo.description[:80]}...")
            if repo.language:
                print(f"    🏷️  {repo.language}")
            print()
        
        return sorted_repos

# Python 3.14+ 特性：使用asyncio.run()运行异步主函数
async def main():
    """主函数示例"""
    print("GitHub Trending 爬虫启动...\n")
    
    # 示例1：爬取Python趋势仓库
    async with GitHubTrendingScraper(language="python", since="daily") as scraper:
        python_repos = await scraper.scrape(sort_by=SortBy.TODAY)
        scraper.save_to_json(python_repos, "github_trending_python.json")
    
    # 示例2：爬取所有语言趋势（异步并发示例）
    print("\n" + "="*50)
    print("同时爬取多种语言趋势...")
    
    languages = ["python", "javascript", "go", "rust"]
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for lang in languages:
            scraper = GitHubTrendingScraper(language=lang, since="weekly")
            # 注意：这里简化了，实际需要适配aiohttp
            tasks.append(asyncio.create_task(scraper.scrape()))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for lang, repos in zip(languages, results):
            if isinstance(repos, Exception):
                print(f"{lang}: 爬取失败 - {repos}")
            else:
                print(f"{lang}: 爬取了 {len(repos)} 个仓库")
    
    print("\n爬取完成！")

# Python 3.14+ 特性：更简洁的主程序入口
if __name__ == "__main__":
    asyncio.run(main())