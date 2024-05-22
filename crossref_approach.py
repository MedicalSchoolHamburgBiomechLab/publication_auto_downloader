from crossref.restful import Works
from dataclasses import dataclass, field


@dataclass
class Author:
    given_name: str
    family_name: str
    affiliation: str = None
    orcid: str = None


@dataclass
class Publication:
    title: str
    doi: str
    pub_date: str
    authors: list[Author] = field(default_factory=list)
    journal: str = None
    volume: str = None
    issue: str = None
    pages: str = None
    publisher: str = None
    abstract: str = None
    keywords: list = field(default_factory=list)
    references: list = field(default_factory=list)

    def get_publication(self, doi):
        pub = Works().doi(doi)
        self.title = pub.get('title')[0]
        self.doi = pub.get('DOI')
        self.pub_date = pub.get('created').get('date-time')
        self.authors = pub.get('author')
        self.journal = pub.get('container-title')[0]
        self.volume = pub.get('volume')
        self.issue = pub.get('issue')
        self.pages = pub.get('page')
        self.publisher = pub.get('publisher')
        self.abstract = pub.get('abstract')
        self.keywords = pub.get('subject')
        self.references = pub.get('reference')
        return self


@dataclass
class IIESMember:
    first_name: str
    last_name: str
    start_date_msh: str
    publications: list = field(default_factory=list)

    def get_publications(self):
        iterator = Works().query(author="Dominik+Fohrmann").filter(from_pub_date="2021")
        n = iterator.count()
        for p, pub in enumerate(iterator):
            print(f'{p}/{n}')
            fname = pub.get('author')[0].get('given')
            if fname != self.first_name:
                continue
            lname = pub.get('author')[0].get('family')
            if lname != self.last_name:
                continue
            self.publications.append(pub)
        return self.publications


dominik = IIESMember(first_name='Dominik',
                     last_name='Fohrmann',
                     start_date_msh='2019-10-01')

pubs = dominik.get_publications()
print(pubs)

dummy = 1
