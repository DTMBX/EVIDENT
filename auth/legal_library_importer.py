"""
Legal Library Data Importer
Bulk import of Supreme Court cases, founding documents, amendments, etc.
"""

from auth.legal_library_service import LegalLibraryService
from auth.legal_library_models import DocumentCategory, DocumentCollection, LegalDocument
from auth.models import db
from datetime import datetime
import json
import csv
from pathlib import Path


class LegalLibraryImporter:
    """Import legal documents from various sources"""
    
    # Pre-built collections
    FOUNDING_DOCUMENTS = {
        'US Constitution': {
            'category': 'constitution',
            'description': 'The Constitution of the United States',
        },
        'Declaration of Independence': {
            'category': 'founding_document',
            'description': 'Declaration of Independence (1776)',
        },
        'Federalist Papers': {
            'category': 'founding_document',
            'description': 'The Federalist Papers',
        },
        'Bill of Rights': {
            'category': 'bill_of_rights',
            'description': 'The Bill of Rights (Amendments I-X)',
        },
    }
    
    AMENDMENT_RANGES = {
        'bill_of_rights': (1, 10),
        'reconstruction': (13, 15),
        'progressive_era': (16, 24),
        'modern': (25, 27),
    }
    
    SUPREME_COURT_COLLECTIONS = [
        'Free Speech & First Amendment',
        'Equal Protection & Due Process',
        'Criminal Procedure & Rights',
        '4th Amendment Search & Seizure',
        '5th Amendment Self-Incrimination',
        '6th Amendment Right to Counsel',
        'Voting Rights',
        'Immigration Law',
        'Commerce Clause',
        'Federalism',
    ]
    
    @staticmethod
    def import_constitution():
        """Import US Constitution"""
        constitution_text = """
        PREAMBLE
        We the People of the United States, in Order to form a more perfect Union, 
        establish Justice, insure domestic Tranquility, provide for the common Defence, 
        promote the general Welfare, and secure the Blessings of Liberty to ourselves 
        and our Posterity, do ordain and establish this Constitution for the United States of America.
        
        ARTICLE I: LEGISLATIVE DEPARTMENT
        Section 1. All legislative Powers herein granted shall be vested in a Congress 
        of the United States, which shall consist of a Senate and House of Representatives.
        
        [Full Constitution text would go here...]
        """
        
        doc = LegalLibraryService.add_document(
            title='The Constitution of the United States',
            category=DocumentCategory.CONSTITUTION.value,
            content_dict={
                'full_text': constitution_text,
                'summary': 'The supreme law of the United States of America',
                'date_filed': datetime(1787, 9, 17),
                'date_decided': datetime(1788, 6, 21),
                'court': 'Constitutional Convention',
                'keywords': ['constitution', 'government', 'rights', 'powers'],
                'issues': [
                    {'topic': 'Separation of Powers', 'details': 'Division of federal power'},
                    {'topic': 'Federalism', 'details': 'Division of power between federal and state'},
                ],
                'import_source': 'archives.gov',
                'url_supremecourt': 'https://www.supremecourt.gov/about/constitution.pdf',
            }
        )
        
        return doc
    
    @staticmethod
    def import_bill_of_rights():
        """Import Bill of Rights"""
        amendments = {
            1: 'Freedom of Speech, Religion, Press, Petition',
            2: 'Right to Bear Arms',
            3: 'Quartering of Troops',
            4: 'Search and Seizure',
            5: 'Self-Incrimination and Due Process',
            6: 'Right to Counsel and Fair Trial',
            7: 'Right to Jury Trial in Civil Cases',
            8: 'Cruel and Unusual Punishment',
            9: 'Rights Retained by People',
            10: 'Powers Reserved to States',
        }
        
        docs = []
        for num, title in amendments.items():
            doc = LegalLibraryService.add_document(
                title=f'Amendment {num}: {title}',
                category=DocumentCategory.AMENDMENT.value,
                content_dict={
                    'summary': f'The {num} Amendment to the US Constitution',
                    'date_decided': datetime(1791, 12, 15),
                    'court': 'US Congress - James Madison',
                    'keywords': [f'amendment {num}', 'rights', 'constitution'],
                    'issues': [{'topic': title, 'details': ''}],
                    'import_source': 'congress.gov',
                }
            )
            docs.append(doc)
        
        return docs
    
    @staticmethod
    def import_all_amendments():
        """Import all 27 amendments"""
        amendments = {
            1: 'Freedom of Speech, Religion, Press, and Petition',
            2: 'Right to Bear Arms',
            3: 'Quartering of Soldiers',
            4: 'Protection from Unreasonable Search and Seizure',
            5: 'Due Process and Protection Against Self-Incrimination',
            6: 'Right to Speedy Trial and Legal Counsel',
            7: 'Right to Trial by Jury in Civil Cases',
            8: 'Protection Against Cruel and Unusual Punishment',
            9: 'Rights Retained by the People',
            10: 'Powers Reserved to the States',
            11: 'Limitation of Judicial Power',
            12: 'Electoral College Procedures',
            13: 'Abolition of Slavery',
            14: 'Equal Protection and Due Process',
            15: 'Prohibition of Race-Based Voting Discrimination',
            16: 'Income Tax',
            17: 'Direct Election of Senators',
            18: 'Prohibition of Alcohol',
            19: 'Women\'s Suffrage',
            20: 'Lame Duck Amendment',
            21: 'Repeal of Prohibition',
            22: 'Presidential Term Limits',
            23: 'Electoral Votes for Washington D.C.',
            24: 'Prohibition of Poll Tax',
            25: 'Presidential Succession',
            26: 'Voting Age Lowered to 18',
            27: 'Congressional Pay Amendment',
        }
        
        docs = []
        for num, title in amendments.items():
            doc = LegalLibraryService.add_document(
                title=f'Amendment {num}: {title}',
                category=DocumentCategory.AMENDMENT.value,
                content_dict={
                    'summary': f'The {num}{["st", "nd", "rd"][0 if num % 10 == 1 and num != 11 else (1 if num % 10 == 2 and num != 12 else (2 if num % 10 == 3 and num != 13 else 3))]} Amendment to the US Constitution',
                    'date_decided': datetime(1791 + (num - 1) // 3, 1, 1),  # Rough date
                    'keywords': [f'amendment {num}', 'constitution'],
                    'import_source': 'congress.gov',
                }
            )
            docs.append(doc)
        
        return docs
    
    @staticmethod
    def create_default_collections():
        """Create default document collections"""
        collections = []
        
        # Founding Documents Collection
        founding = LegalLibraryService.create_collection(
            name='Founding Documents of the United States',
            category='founding',
            description='Original founding documents including the Constitution, Declaration, and Federalist Papers'
        )
        collections.append(founding)
        
        # Bill of Rights & Amendments
        amendments = LegalLibraryService.create_collection(
            name='Bill of Rights & All Amendments',
            category='amendments',
            description='All 27 Amendments to the US Constitution'
        )
        collections.append(amendments)
        
        # Create collections for each Supreme Court topic
        for topic in LegalLibraryImporter.SUPREME_COURT_COLLECTIONS:
            collection = LegalLibraryService.create_collection(
                name=topic,
                category='supreme_court',
                description=f'Supreme Court cases related to {topic.lower()}'
            )
            collections.append(collection)
        
        return collections
    
    @staticmethod
    def import_landmark_cases():
        """Import landmark Supreme Court cases"""
        landmark_cases = [
            {
                'title': 'Marbury v. Madison',
                'case_number': '5 U.S. 137 (1803)',
                'citation_supreme': '5 U.S. 137',
                'date_decided': datetime(1803, 2, 24),
                'petitioner': 'William Marbury',
                'respondent': 'James Madison',
                'summary': 'Established the doctrine of judicial review',
                'keywords': ['judicial review', 'constitutional law', 'separation of powers'],
                'court': 'U.S. Supreme Court',
            },
            {
                'title': 'McCulloch v. Maryland',
                'case_number': '17 U.S. 316 (1819)',
                'citation_supreme': '17 U.S. 316',
                'date_decided': datetime(1819, 3, 6),
                'petitioner': 'McCulloch',
                'respondent': 'Maryland',
                'summary': 'Established implied powers of federal government and supremacy of federal law',
                'keywords': ['implied powers', 'commerce clause', 'federalism'],
                'court': 'U.S. Supreme Court',
            },
            {
                'title': 'Plessy v. Ferguson',
                'case_number': '163 U.S. 537 (1896)',
                'citation_supreme': '163 U.S. 537',
                'date_decided': datetime(1896, 5, 18),
                'petitioner': 'Homer Adolf Plessy',
                'respondent': 'John H. Ferguson',
                'summary': 'Upheld "separate but equal" doctrine (later overruled)',
                'keywords': ['equal protection', 'race discrimination', 'civil rights'],
                'court': 'U.S. Supreme Court',
            },
            {
                'title': 'Brown v. Board of Education',
                'case_number': '347 U.S. 483 (1954)',
                'citation_supreme': '347 U.S. 483',
                'date_decided': datetime(1954, 5, 17),
                'petitioner': 'Linda Brown',
                'respondent': 'Board of Education',
                'summary': 'Overturned Plessy v. Ferguson; declared segregation unconstitutional',
                'keywords': ['equal protection', 'education', 'desegregation', 'civil rights'],
                'court': 'U.S. Supreme Court',
            },
            {
                'title': 'Miranda v. Arizona',
                'case_number': '384 U.S. 436 (1966)',
                'citation_supreme': '384 U.S. 436',
                'date_decided': datetime(1966, 6, 13),
                'petitioner': 'Ernesto Miranda',
                'respondent': 'Arizona',
                'summary': 'Established requirement for police to inform suspects of their rights',
                'keywords': ['5th amendment', 'criminal procedure', 'self-incrimination', 'due process'],
                'court': 'U.S. Supreme Court',
            },
            {
                'title': 'Roe v. Wade',
                'case_number': '410 U.S. 113 (1973)',
                'citation_supreme': '410 U.S. 113',
                'date_decided': datetime(1973, 1, 22),
                'petitioner': 'Jane Roe',
                'respondent': 'Henry Wade',
                'summary': 'Established constitutional right to privacy regarding abortion',
                'keywords': ['due process', 'privacy', 'abortion', 'reproductive rights'],
                'court': 'U.S. Supreme Court',
            },
            {
                'title': 'New York Times Co. v. Sullivan',
                'case_number': '376 U.S. 254 (1964)',
                'citation_supreme': '376 U.S. 254',
                'date_decided': datetime(1964, 3, 9),
                'petitioner': 'New York Times Co.',
                'respondent': 'L. B. Sullivan',
                'summary': 'Established standard for press freedom and defamation law',
                'keywords': ['1st amendment', 'free press', 'free speech', 'defamation'],
                'court': 'U.S. Supreme Court',
            },
            {
                'title': 'McCulloch v. Maryland',
                'case_number': 'Gideon v. Wainwright 372 U.S. 335 (1963)',
                'citation_supreme': '372 U.S. 335',
                'date_decided': datetime(1963, 3, 18),
                'petitioner': 'Clarence Earl Gideon',
                'respondent': 'Louie L. Wainwright',
                'summary': 'Established right to counsel in criminal cases',
                'keywords': ['6th amendment', 'right to counsel', 'criminal procedure', 'due process'],
                'court': 'U.S. Supreme Court',
            },
        ]
        
        docs = []
        for case_data in landmark_cases:
            doc = LegalLibraryService.add_document(
                title=case_data['title'],
                category=DocumentCategory.SUPREME_COURT.value,
                content_dict={
                    **case_data,
                    'status': 'published',
                    'import_source': 'supremecourt.gov',
                }
            )
            docs.append(doc)
        
        return docs
    
    @staticmethod
    def import_from_csv(csv_file):
        """Import documents from CSV file"""
        docs = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                doc = LegalLibraryService.add_document(
                    title=row.get('title'),
                    category=row.get('category', 'supreme_court'),
                    content_dict={
                        'full_text': row.get('full_text'),
                        'summary': row.get('summary'),
                        'case_number': row.get('case_number'),
                        'citation_supreme': row.get('citation'),
                        'date_decided': datetime.fromisoformat(row['date']) if row.get('date') else None,
                        'keywords': row.get('keywords', '').split(';'),
                        'import_source': 'csv_import',
                    }
                )
                docs.append(doc)
        
        return docs


def init_legal_library():
    """Initialize legal library with default data"""
    from auth.models import db
    
    # Check if already initialized
    count = LegalDocument.query.count()
    if count > 0:
        print(f"Legal library already has {count} documents")
        return
    
    print("Initializing legal library...")
    
    # Create collections
    print("Creating collections...")
    LegalLibraryImporter.create_default_collections()
    
    # Import founding documents
    print("Importing Constitution...")
    LegalLibraryImporter.import_constitution()
    
    print("Importing Bill of Rights...")
    LegalLibraryImporter.import_bill_of_rights()
    
    print("Importing all amendments...")
    LegalLibraryImporter.import_all_amendments()
    
    # Import landmark cases
    print("Importing landmark Supreme Court cases...")
    LegalLibraryImporter.import_landmark_cases()
    
    stats = LegalLibraryService.get_statistics()
    print(f"\nLegal library initialized:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Supreme Court cases: {stats['supreme_court_cases']}")
    print(f"  Founding documents: {stats['founding_documents']}")
    print(f"  Amendments: {stats['amendments']}")
    print(f"  Collections: {stats['collections']}")
