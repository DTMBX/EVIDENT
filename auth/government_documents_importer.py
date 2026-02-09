"""
Government Legal Sources Importer
Imports founding documents, Supreme Court cases, legislation, and legal references
from US government databases and official sources
"""

import logging
from datetime import datetime
from auth.legal_library_service import LegalLibraryService
from auth.legal_library_models import DocumentCategory
from auth.government_sources import GovernmentSources
from auth.models import db

logger = logging.getLogger(__name__)


class GovernmentSourcesImporter:
    """Import legal documents from US government sources"""
    
    @staticmethod
    def import_founding_documents():
        """Import founding documents from Archives.gov"""
        try:
            logger.info("Starting import of founding documents...")
            
            # 1. Constitution
            constitution_data = GovernmentSources.get_constitution()
            constitution = LegalLibraryService.add_document(
                title="The Constitution of the United States",
                category=DocumentCategory.CONSTITUTION.value,
                content_dict={
                    'full_text': """PREAMBLE
We the People of the United States, in Order to form a more perfect Union, establish Justice, 
insure domestic Tranquility, provide for the common defence, promote the general Welfare, 
and secure the Blessings of Liberty to ourselves and our Posterity, do ordain and establish 
this Constitution for the United States of America.

ARTICLE I: LEGISLATIVE DEPARTMENT
Section 1. All legislative Powers herein granted shall be vested in a Congress of the United States, 
which shall consist of a Senate and House of Representatives.

[Full Constitution text available at archives.gov]""",
                    'summary': constitution_data['content_sections'].get('description', 'The supreme law of the United States'),
                    'date_decided': datetime(1788, 6, 21),
                    'date_filed': datetime(1787, 9, 17),
                    'court': 'Constitutional Convention',
                    'keywords': ['constitution', 'government', 'rights', 'powers', 'federalism', 'separation of powers'],
                    'import_source': 'archives.gov',
                    'url_supremecourt': 'https://www.supremecourt.gov/about/constitution.pdf',
                }
            )
            logger.info(f"✓ Imported Constitution: {constitution.id}")
            
            # 2. Declaration of Independence
            declaration = LegalLibraryService.add_document(
                title="Declaration of Independence",
                category=DocumentCategory.FOUNDING_DOCUMENT.value,
                content_dict={
                    'full_text': """When in the Course of human events, it becomes necessary for one people to dissolve 
the political bands which have connected them with another...

We hold these truths to be self-evident, that all men are created equal, that they are endowed by 
their Creator with certain unalienable Rights, that among these are Life, Liberty and the pursuit of Happiness.

[Full Declaration text available at archives.gov]""",
                    'summary': 'Statement of why the colonies declared independence from British rule',
                    'date_decided': datetime(1776, 7, 4),
                    'court': 'Continental Congress',
                    'keywords': ['independence', 'founding', 'unalienable rights', 'government', 'revolution'],
                    'import_source': 'archives.gov',
                    'url_supremecourt': 'https://www.archives.gov/founding-docs/declaration-transcript',
                }
            )
            logger.info(f"✓ Imported Declaration of Independence: {declaration.id}")
            
            # 3. Bill of Rights
            bill_of_rights = LegalLibraryService.add_document(
                title="Bill of Rights (Amendments I-X)",
                category=DocumentCategory.BILL_OF_RIGHTS.value,
                content_dict={
                    'full_text': """The first ten amendments to the Constitution of the United States:

FIRST AMENDMENT: Congress shall make no law respecting an establishment of religion, or prohibiting 
the free exercise thereof; or abridging the freedom of speech, or of the press...

SECOND AMENDMENT: A well regulated Militia, being necessary to the security of a free State, 
the right of the people to keep and bear Arms, shall not be infringed...

THIRD AMENDMENT: No Soldier shall, in time of peace be quartered in any house...

FOURTH AMENDMENT: The right of the people to be secure in their persons, houses, papers, 
and effects against unreasonable searches and seizures...

FIFTH AMENDMENT: No person shall be deprived of life, liberty, or property, without due process of law...

SIXTH AMENDMENT: In all criminal prosecutions, the accused shall enjoy the right to a speedy and public trial...

SEVENTH AMENDMENT: In Suits at common law, where the value in controversy shall exceed twenty dollars, 
the right of trial by jury shall be preserved...

EIGHTH AMENDMENT: Excessive bail shall not be required, nor excessive fines imposed, 
nor cruel and unusual punishments inflicted...

NINTH AMENDMENT: The enumeration in the Constitution, of certain rights, shall not be construed 
to deny or disparage others retained by the people...

TENTH AMENDMENT: The powers not delegated to the United States by the Constitution, 
nor prohibited by it to the States, are reserved to the States respectively, or to the people...""",
                    'summary': 'First ten amendments protecting fundamental rights and freedoms',
                    'date_decided': datetime(1791, 12, 15),
                    'court': 'First Congress',
                    'keywords': ['rights', 'freedoms', 'speech', 'religion', 'assembly', 'petition', 'press', 'bear arms'],
                    'import_source': 'archives.gov',
                    'url_supremecourt': 'https://www.archives.gov/founding-docs/bill-of-rights-transcript',
                }
            )
            logger.info(f"✓ Imported Bill of Rights: {bill_of_rights.id}")
            
            # 4. Articles of Confederation
            articles = LegalLibraryService.add_document(
                title="Articles of Confederation",
                category=DocumentCategory.FOUNDING_DOCUMENT.value,
                content_dict={
                    'full_text': """To all to whom these Presents shall come, we the under signed Delegates of the States 
affixed to our Names send greeting.

Whereas the Delegates of the United States of America in Congress assembled did on the 15th day of November 
in the Year of our Lord 1777 and in the Second Year of the Independence of America agree to certain articles 
of Confederation and perpetual Union...""",
                    'summary': 'First framework for cooperation among the states (predecessor to Constitution)',
                    'date_decided': datetime(1781, 3, 1),
                    'date_filed': datetime(1777, 11, 15),
                    'court': 'Continental Congress',
                    'keywords': ['articles', 'confederation', 'founding', 'government', 'states'],
                    'import_source': 'archives.gov',
                    'url_supremecourt': 'https://www.archives.gov/founding-docs/articles-confederation',
                }
            )
            logger.info(f"✓ Imported Articles of Confederation: {articles.id}")
            
            return {
                "status": "success",
                "documents_imported": 4,
                "documents": [constitution.id, declaration.id, bill_of_rights.id, articles.id],
            }
        
        except Exception as e:
            logger.error(f"Error importing founding documents: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    @staticmethod
    def import_amendments(start: int = 1, end: int = 27):
        """Import Constitutional Amendments"""
        try:
            logger.info(f"Starting import of amendments {start}-{end}...")
            
            amendments = GovernmentSources.get_amendments(start, end)
            
            imported_ids = []
            for amendment_data in amendments:
                amendment_num = amendment_data['amendment_number']
                
                # Create amendment document
                doc = LegalLibraryService.add_document(
                    title=f"Amendment {amendment_num}: {amendment_data['title']}",
                    category=DocumentCategory.AMENDMENT.value,
                    content_dict={
                        'full_text': f"Amendment {amendment_num}: {amendment_data['title']}",
                        'summary': f"Constitutional Amendment {amendment_num}, ratified {amendment_data['ratified'].year}",
                        'date_decided': amendment_data['ratified'],
                        'keywords': [f'amendment {amendment_num}'] + amendment_data['keywords'],
                        'import_source': 'archives.gov',
                        'url_supremecourt': amendment_data['url'],
                    }
                )
                imported_ids.append(doc.id)
                logger.info(f"✓ Imported Amendment {amendment_num}: {doc.id}")
            
            return {
                "status": "success",
                "amendments_imported": len(amendments),
                "amendment_ids": imported_ids,
            }
        
        except Exception as e:
            logger.error(f"Error importing amendments: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    @staticmethod
    def import_landmark_cases():
        """Import landmark Supreme Court cases"""
        try:
            logger.info("Starting import of landmark Supreme Court cases...")
            
            cases_metadata = GovernmentSources.get_supreme_court_cases_metadata()
            
            imported_ids = []
            for case in cases_metadata:
                doc = LegalLibraryService.add_document(
                    title=case['title'],
                    category=DocumentCategory.SUPREME_COURT.value,
                    content_dict={
                        'full_text': f"Case: {case['title']}\nCitation: {case['case_number']}\nYear: {case['year']}",
                        'summary': f"Landmark Supreme Court case decided in {case['year']}",
                        'case_number': case['case_number'],
                        'date_decided': datetime(case['year'], 1, 1),
                        'court': 'U.S. Supreme Court',
                        'keywords': case['keywords'],
                        'import_source': case['source'],
                        'url_supremecourt': case['url'],
                    }
                )
                imported_ids.append(doc.id)
                logger.info(f"✓ Imported {case['title']}: {doc.id}")
            
            return {
                "status": "success",
                "cases_imported": len(cases_metadata),
                "case_ids": imported_ids,
            }
        
        except Exception as e:
            logger.error(f"Error importing landmark cases: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    @staticmethod
    def initialize_full_library():
        """Initialize complete legal library with all government sources"""
        try:
            logger.info("=== INITIALIZING LEGAL LIBRARY FROM US GOVERNMENT SOURCES ===")
            
            results = {
                "founding_documents": GovernmentSourcesImporter.import_founding_documents(),
                "amendments": GovernmentSourcesImporter.import_amendments(),
                "landmark_cases": GovernmentSourcesImporter.import_landmark_cases(),
            }
            
            total_imported = (
                results["founding_documents"].get("documents_imported", 0) +
                results["amendments"].get("amendments_imported", 0) +
                results["landmark_cases"].get("cases_imported", 0)
            )
            
            logger.info(f"=== LIBRARY INITIALIZATION COMPLETE: {total_imported} documents imported ===")
            
            return {
                "status": "success",
                "total_imported": total_imported,
                "results": results,
            }
        
        except Exception as e:
            logger.error(f"Error initializing library: {e}")
            return {
                "status": "error",
                "message": str(e),
            }


# Export function for easy access
def init_legal_library_from_government_sources():
    """Initialize legal library from government sources"""
    return GovernmentSourcesImporter.initialize_full_library()
