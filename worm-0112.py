


from dataclasses import dataclass
from typing import List, Optional
from bs4 import BeautifulSoup
import httpx


@dataclass
class GithubRepo:
    name:str
    url:str
    description:Optional[str]
    starts: int
    forks: int
    today_starts: Optional[int]
    language: Optional[str]
    
    

class Scraper:
    Base_Url:str="https://github.com/trending"
    
    
    def __init__(self,language:str,since:str="daily"):
        self.session: Optional[httpx.AsyncClient]=None
        self.language:str = language
        self.since: str = ""
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout = 30,
            headers = {
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; 64) AppleWebKit/537.36 ",
                "Accept":"Application/vnd.github.v3+json"
            },
            follow_redirects=True
        )
        return self

    async def __aexit__(self):
        self.session.aclose()
        
        
    def build_url(self)->str:
        url = self.Base_Url
        return f"{url}/{self.language}?since={self.since}"
    
    async def fetch_page(self)->str:
        if not self.session:
            raise RuntimeError("session not initiated, please check the code!")
        
        fetchUrl = self.build_url()
        
        try:
            response = await self.session.get(fetchUrl)
            response.raise_for_status()
            return response.text       
        except Exception as e:
            print(f"Failed to fetch page{fetchUrl},please check the code or network connection!")
            return ""
        
    async def scraper(self)->List[GithubRepo]:
        
        html = self.fetch_page()
        if not html: 
            print(f"The fetched page({self.build_url()}) is empty, please check")
            return []
        
        soup = BeautifulSoup(html,"html.parser")
        
        repos=[]
        
        targetElements = soup.find_all("article",class_="Box-row")
        
        for ele in targetElements:
            title_Element = ele.find("h2",class_="h3")
            
            title_link= title_Element.find("a",class_="Link")
            
            url=f"https://github.com/{title_link["href"]}"
            
            name = title_link.getText()
            
            
        
        
        
        
        
        
            
    
        
            
                
        
        
        
        
        
        
            
        
        
        
        
        
        
        
        
        

     
        
    
    
    

    
    
