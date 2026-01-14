#!/usr/bin/env python3


import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
import aiohttp
from bs4 import BeautifulSoup
import httpx

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
            timeout = 30.0,
            headers = {
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
            print(f"GET {self.language or 'all'} FAILED: {e}")
            return ""
    
    async def scrape(self) -> List[GitHubRepo]:
        """MAIN SCRAPE Method"""
        html = await self.fetch_page()
        if not html:
            return []
        
        soup = BeautifulSoup(html, "html.parser")
        repos = []
        repo_elements = soup.find_all("article", class_="Box-row")
        
        for repo_element in repo_elements:
            try:
                # fetch repo name
                title_element = repo_element.find("h2", class_="h3")
                if not title_element:
                    continue
                    
                link = title_element.find("a")
                if not link:
                    continue
                    
                repo_name = link.get_text(strip=True).replace(" ", "")
                repo_url = f"https://github.com{link['href']}"
                
                # get description
                desc_element = repo_element.find("p", class_="col-9")
                description = desc_element.get_text(strip=True) if desc_element else None
                
                # get programming language
                lang_element = repo_element.find("span", itemprop="programmingLanguage")
                language = lang_element.get_text(strip=True) if lang_element else None
                
                # get starts and forks
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
                            # get number
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
    """get single language trend"""
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
    
    # create all scrape tasks
    tasks = [scrape_single_language(lang, since) for lang in languages]
    
    # concurrency tasks
    results = await asyncio.gather(*tasks, return_exceptions=False)
    

    all_results = {}
    successful = 0
    
    for language, repos in results:
        if repos: 
            successful += 1
            all_results[language] = repos
            print(f"  ✓ {language}: scrape {len(repos)} repos")
        else:
            print(f"  ✗ {language}: failed or no data")
    
    print(f"Finished! Get {successful}/{len(languages)} languages")
    return all_results

def save_results_to_json(results: dict, filename: str = "github_trending_all.json"):
    """save all results to json file"""
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
    
    print(f"all data saved to {filename}")

def print_summary(results: dict, top_n: int = 5):
    print("\n" + "="*60)
    print("GitHub Trending multi-languages")
    print("="*60)
    
    for language, repos in results.items():
        if not repos:
            continue
            
        print(f"\n【{language.upper()}】")
        # Rank by Stars
        repos_with_today = [r for r in repos if r.today_stars]
        if repos_with_today:
            sorted_repos = sorted(repos_with_today, key=lambda x: x.today_stars or 0, reverse=True)[:top_n]
            sort_by = "new stars today"
        else:
            sorted_repos = sorted(repos, key=lambda x: x.stars, reverse=True)[:top_n]
            sort_by = "all stars"
        
        print(f"rank method: {sort_by}")
        for i, repo in enumerate(sorted_repos, 1):
            today_text = f"(tday +{repo.today_stars})" if repo.today_stars else ""
            print(f"  {i:2d}. {repo.name:40} ⭐ {repo.stars:>6} {today_text:10}")

async def main():
    print("GitHub Trending multi-language")
    print("-" * 40)
    
    # configure the languages to scrape
    languages = ["python", "javascript", "go", "rust", "java", "typescript"]
    
    # example 1：get single language（Python）
    print("\n1.  Python trend:")
    async with GitHubTrendingScraper(language="python", since="daily") as scraper:
        python_repos = await scraper.scrape()
        print(f"  get {len(python_repos)} Python repos")
        
        # show first 3
        for i, repo in enumerate(python_repos[:3], 1):
            print(f"     {i}. {repo.name} - {repo.stars} stars")
    
    # example 2：multiple language
    print(f"\n2. get {len(languages)} languages:")
    all_results = await concurrent_scrape(languages, since="daily")
    
    # save results
    save_results_to_json(all_results)
    
    # print summary
    print_summary(all_results)
    

    total_repos = sum(len(repos) for repos in all_results.values())
    print(f"\nTotal: {total_repos} repos ")

if __name__ == "__main__":
    asyncio.run(main())