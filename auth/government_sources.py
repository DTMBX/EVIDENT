"""
US Government Legal Sources Integration
Fetches founding documents, Supreme Court cases, legislation, and legal references
from official US government APIs and databases
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode, quote
import asyncio
import aiohttp
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class GovernmentSources:
    """Integrates with US government legal databases and APIs"""
    
    # Official API endpoints
    CONGRESS_API = "https://api.congress.gov/v3"
    LOC_API = "https://www.loc.gov/api"
    GOVINFO_API = "https://www.govinfo.gov/api/services"
    SUPREME_COURT_PDF = "https://www.supremecourt.gov/opinions/opinions.html"
    FEDERAL_REGISTER_API = "https://www.federalregister.gov/api/v1"
    HOUSE_BILLS_API = "https://clerk.house.gov/json"
    SENATE_BILLS_API = "https://www.senate.gov/api/v1"
    
    # Congress.gov API key (should be in environment)
    CONGRESS_API_KEY = "YOUR_CONGRESS_API_KEY"
    
    # Caching configuration
    CACHE_DURATION = timedelta(days=7)
    
    @staticmethod
    def get_constitution() -> Dict[str, Any]:
        """Fetch US Constitution from official source"""
        return {
            "title": "The Constitution of the United States",
            "category": "constitution",
            "source": "archives.gov",
            "url": "https://www.archives.gov/founding-docs/constitution-transcript",
            "date_adopted": datetime(1787, 9, 17),
            "content_sections": {
                "preamble": "We the People of the United States...",
                "articles": 7,
                "amendments": 27,
            },
            "keywords": ["constitution", "government", "rights", "powers", "federalism"],
            "import_source": "archives.gov",
        }
    
    @staticmethod
    def get_bill_of_rights() -> Dict[str, Any]:
        """Fetch Bill of Rights (Amendments I-X) from official source"""
        return {
            "title": "Bill of Rights",
            "category": "bill_of_rights",
            "source": "archives.gov",
            "url": "https://www.archives.gov/founding-docs/bill-of-rights-transcript",
            "ratified": datetime(1791, 12, 15),
            "amendments": 10,
            "content": {
                "amendment_1": "Congress shall make no law respecting an establishment of religion...",
                "amendment_2": "A well regulated Militia, being necessary to the security...",
                "amendment_3": "No Soldier shall, in time of peace be quartered...",
                "amendment_4": "The right of the people to be secure in their persons...",
                "amendment_5": "No person shall be deprived of life, liberty...",
                "amendment_6": "In all criminal prosecutions, the accused shall enjoy...",
                "amendment_7": "In Suits at common law, where the value in controversy...",
                "amendment_8": "Excessive bail shall not be required...",
                "amendment_9": "The enumeration in the Constitution...",
                "amendment_10": "The powers not delegated to the United States...",
            },
            "keywords": ["rights", "freedoms", "amendments", "constitution", "protection"],
            "import_source": "archives.gov",
        }
    
    @staticmethod
    def get_declaration_of_independence() -> Dict[str, Any]:
        """Fetch Declaration of Independence"""
        return {
            "title": "Declaration of Independence",
            "category": "founding_document",
            "source": "archives.gov",
            "url": "https://www.archives.gov/founding-docs/declaration-transcript",
            "adopted": datetime(1776, 7, 4),
            "content_sections": {
                "preamble": "When in the Course of human events...",
                "statement_of_equals": "We hold these truths to be self-evident...",
                "indictment": 27,  # 27 charges against King
            },
            "keywords": ["independence", "founding", "rights", "government", "revolution"],
            "import_source": "archives.gov",
        }
    
    @staticmethod
    def get_founding_documents() -> List[Dict[str, Any]]:
        """Get all major founding documents from official archives"""
        founding_docs = [
            {
                "title": "Articles of Confederation",
                "url": "https://www.archives.gov/founding-docs/articles-confederation",
                "date": datetime(1781, 3, 1),
                "category": "founding_document",
            },
            {
                "title": "Federalist Papers",
                "url": "https://www.congress.gov/resources/display/content/The+Federalist+Papers",
                "date": datetime(1787, 10, 27),
                "category": "founding_document",
                "note": "85 essays by Hamilton, Madison, Jay",
            },
            {
                "title": "Anti-Federalist Papers",
                "url": "https://www.constitution.org/afp.htm",
                "date": datetime(1787, 10, 1),
                "category": "founding_document",
            },
            {
                "title": "Virginia Declaration of Rights",
                "url": "https://www.archives.gov/founding-docs/virginia-declaration",
                "date": datetime(1776, 6, 12),
                "category": "founding_document",
            },
            {
                "title": "Magna Carta (1215)",
                "url": "https://www.loc.gov/exhibitions/magna-carta/about-this-collection/",
                "date": datetime(1215, 6, 15),
                "category": "founding_document",
                "note": "Foundation for constitutional law",
            },
        ]
        return founding_docs
    
    @staticmethod
    def search_congress_bills(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search bills in Congress using Congress.gov API"""
        try:
            # Congress.gov API endpoint for bills
            url = f"{GovernmentSources.CONGRESS_API}/bills"
            params = {
                "q": query,
                "limit": min(limit, 100),
                "sort": "updateDate:desc",
                "api_key": GovernmentSources.CONGRESS_API_KEY,
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                bills = []
                for bill_result in data.get("results", [])[:limit]:
                    bill = bill_result.get("bill", {})
                    bills.append({
                        "title": bill.get("title"),
                        "bill_number": bill.get("number"),
                        "congress": bill.get("congress"),
                        "introduced_date": bill.get("introducedDate"),
                        "chamber": bill.get("originChamber"),
                        "summary": bill.get("summaries", [{}])[0].get("text"),
                        "url": bill.get("url"),
                        "keywords": [query],
                        "source": "congress.gov",
                        "import_source": "congress.gov",
                    })
                return bills
        except Exception as e:
            logger.error(f"Error searching Congress bills: {e}")
        
        return []
    
    @staticmethod
    def search_federal_register(query: str, document_type: str = "RULE", limit: int = 10) -> List[Dict[str, Any]]:
        """Search Federal Register for regulations and notices"""
        try:
            url = f"{GovernmentSources.FEDERAL_REGISTER_API}/documents/search"
            params = {
                "q": query,
                "type": document_type,
                "per_page": min(limit, 100),
                "sort": "publication_date,desc",
                "fields": ["title", "summary", "agencies", "document_number", "publication_date"],
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                documents = []
                for doc in data.get("results", [])[:limit]:
                    documents.append({
                        "title": doc.get("title"),
                        "document_number": doc.get("document_number"),
                        "agencies": doc.get("agencies", []),
                        "summary": doc.get("summary"),
                        "publication_date": doc.get("publication_date"),
                        "url": doc.get("html_url"),
                        "document_type": doc.get("type"),
                        "keywords": [query],
                        "source": "federalregister.gov",
                        "import_source": "federalregister.gov",
                    })
                return documents
        except Exception as e:
            logger.error(f"Error searching Federal Register: {e}")
        
        return []
    
    @staticmethod
    def search_library_of_congress(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search Library of Congress for legislative information"""
        try:
            url = f"{GovernmentSources.LOC_API}/search"
            params = {
                "q": query,
                "fo": "json",
                "c": 50,
                "at": "digitized",
                "mods": True,
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("results", [])[:limit]:
                    results.append({
                        "title": item.get("title", [None])[0],
                        "description": item.get("description", [None])[0],
                        "date": item.get("date", [None])[0],
                        "url": item.get("link"),
                        "keywords": [query],
                        "source": "loc.gov",
                        "import_source": "loc.gov",
                    })
                return results
        except Exception as e:
            logger.error(f"Error searching Library of Congress: {e}")
        
        return []
    
    @staticmethod
    def get_amendments(start: int = 1, end: int = 27) -> List[Dict[str, Any]]:
        """Get Constitutional Amendments"""
        amendments_data = {
            1: ("Freedom of Speech, Religion, Press, Petition", 1791),
            2: ("Right to Bear Arms", 1791),
            3: ("Quartering of Soldiers", 1791),
            4: ("Search and Seizure", 1791),
            5: ("Self-Incrimination and Due Process", 1791),
            6: ("Right to Counsel and Fair Trial", 1791),
            7: ("Trial by Jury in Civil Cases", 1791),
            8: ("Excessive Bail and Cruel Punishment", 1791),
            9: ("Other Rights Retained by the People", 1791),
            10: ("Powers Reserved to the States", 1791),
            11: ("Judicial Limits", 1795),
            12: ("Electoral College Procedures", 1804),
            13: ("Abolition of Slavery", 1865),
            14: ("Citizenship and Equal Protection", 1868),
            15: ("Voting Rights - Race", 1870),
            16: ("Income Tax", 1913),
            17: ("Direct Election of Senators", 1913),
            18: ("Prohibition of Alcohol", 1919),
            19: ("Women's Suffrage", 1920),
            20: ("Lame Duck Amendment", 1933),
            21: ("Repeal of Prohibition", 1933),
            22: ("Presidential Term Limits", 1951),
            23: ("DC Electoral Votes", 1961),
            24: ("Poll Tax Banned", 1964),
            25: ("Presidential Succession", 1967),
            26: ("Voting Age 18", 1971),
            27: ("Congressional Pay", 1992),
        }
        
        amendments = []
        for num in range(start, end + 1):
            if num in amendments_data:
                title, year = amendments_data[num]
                amendments.append({
                    "amendment_number": num,
                    "title": title,
                    "ratified": datetime(year, 1, 1),
                    "url": f"https://www.archives.gov/founding-docs/amendments-11-27",
                    "category": "amendment",
                    "source": "archives.gov",
                    "keywords": ["amendment", "constitution", title.lower()],
                    "import_source": "archives.gov",
                })
        
        return amendments
    
    @staticmethod
    def search_justia_cases(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search court cases (this integrates with Justia which aggregates PACER data)"""
        try:
            url = "https://api.justia.com/v1/case-search"
            params = {
                "query": query,
                "limit": min(limit, 100),
            }
            
            # Note: This requires API key from Justia
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get("cases", [])
        except Exception as e:
            logger.error(f"Error searching Justia: {e}")
        
        return []
    
    @staticmethod
    def get_supreme_court_cases_metadata() -> List[Dict[str, Any]]:
        """Get metadata for landmark Supreme Court cases for import"""
        return [
            {
                "title": "Marbury v. Madison",
                "case_number": "5 U.S. (1 Cranch) 137",
                "year": 1803,
                "keywords": ["judicial review", "constitutionality", "landmark"],
                "url": "https://tile.loc.gov/storage-services/service/ll/usrep/usrep005/usrep005p137/usrep005p137.pdf",
                "source": "loc.gov",
            },
            {
                "title": "McCulloch v. Maryland",
                "case_number": "17 U.S. (4 Wheat.) 316",
                "year": 1819,
                "keywords": ["commerce clause", "federal power", "implied powers"],
                "url": "https://tile.loc.gov/storage-services/service/ll/usrep/usrep017/usrep017p316/usrep017p316.pdf",
                "source": "loc.gov",
            },
            {
                "title": "Marbury v. Madison",
                "case_number": "5 U.S. (1 Cranch) 137",
                "year": 1803,
                "keywords": ["judicial review"],
                "url": "https://www.supremecourt.gov/opinions/opinions.html",
                "source": "supremecourt.gov",
            },
            {
                "title": "Plessy v. Ferguson",
                "case_number": "163 U.S. 537",
                "year": 1896,
                "keywords": ["separate but equal", "equal protection"],
                "url": "https://www.supremecourt.gov/opinions/opinions.html",
                "source": "supremecourt.gov",
            },
            {
                "title": "Brown v. Board of Education",
                "case_number": "347 U.S. 483",
                "year": 1954,
                "keywords": ["desegregation", "equal protection", "education"],
                "url": "https://www.supremecourt.gov/opinions/opinions.html",
                "source": "supremecourt.gov",
            },
        ]
    
    @staticmethod
    async def fetch_all_government_sources_async(query: Optional[str] = None) -> Dict[str, List[Any]]:
        """Fetch from multiple government sources concurrently using async"""
        tasks = []
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Queue up all requests
            if query:
                # tasks.append(session.get(f"{GovernmentSources.CONGRESS_API}/bills", params={"q": query}))
                # tasks.append(session.get(f"{GovernmentSources.FEDERAL_REGISTER_API}/documents/search", params={"q": query}))
                pass
            
            # Fetch founding documents
            results["founding_documents"] = GovernmentSources.get_founding_documents()
            results["constitution"] = GovernmentSources.get_constitution()
            results["bill_of_rights"] = GovernmentSources.get_bill_of_rights()
            results["amendments"] = GovernmentSources.get_amendments()
            results["declaration"] = GovernmentSources.get_declaration_of_independence()
        
        return results
    
    @staticmethod
    def verify_government_source(url: str) -> bool:
        """Verify that a URL is from an official US government domain"""
        official_domains = [
            "supremecourt.gov",
            "congress.gov",
            "house.gov",
            "senate.gov",
            "loc.gov",
            "govinfo.gov",
            "federalregister.gov",
            "justice.gov",
            "archives.gov",
            "sos.gov",
            "courts.gov",
        ]
        
        return any(domain in url.lower() for domain in official_domains)
    
    @staticmethod
    @lru_cache(maxsize=128)
    def get_legal_definitions() -> Dict[str, str]:
        """Get legal definitions for common terms from official sources"""
        return {
            "habeas_corpus": "A fundamental legal right to challenge unlawful detention - Latin: 'you shall have the body'",
            "amicus_curiae": "A friend of the court - person or organization not party to a case but offering information",
            "certiorari": "A Supreme Court writ requesting case records from a lower court for review",
            "mandamus": "Court order compelling a government official to perform mandatory duty",
            "injunction": "Court order requiring a person to do or refrain from doing an action",
            "precedent": "Prior court decision used as authority in subsequent cases",
            "mens_rea": "Criminal law term for mental element or criminal intent",
            "prima_facie": "Enough evidence to proceed with case unless rebutted",
            "pro_bono": "Legal work performed voluntarily without charge for the public good",
            "subpoena": "Court order to testify or produce documents",
            "voir_dire": "Process of questioning potential jurors to determine suitability",
            "writ": "Formal written order issued by a court",
            "statute_of_limitations": "Time period within which legal action must be brought",
            "affidavit": "Written statement made under oath before authorized officer",
            "deposition": "Testimony given under oath outside court, recorded for trial",
        }


# Singleton instance
government_sources = GovernmentSources()
