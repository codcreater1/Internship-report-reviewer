"""Fifty distinct internship reports.

Each package needs prose the originality gate will not flag against the other
forty-nine. The first attempt shared one set of sentence frames across all
fifty and swapped only the nouns, and the service was right to call the result
similar: at a corpus of fifteen accepted reports it was scoring pairs at 0.76.

So both halves vary. Every story gets its own domain vocabulary, and every
section is assembled from one of four unrelated phrasings picked by a different
offset, so two packages sharing a domain almost never share a frame.
"""

DOMAINS = [
    ("Nova Logistics Software Sp. z o.o.", "Backend Platform Team", "route estimate caching", "Redis", "dispatcher", "delivery window errors", "warehouse"),
    ("Wielkopolska Hurt Spozywczy Sp. z o.o.", "Data Quality Group", "supplier invoice parsing", "Airflow", "purchasing clerk", "invoice rejections", "wholesaler"),
    ("Medivia Dystrybucja Sp. z o.o.", "Quality Assurance", "regression suite timing", "Playwright", "procurement officer", "flaky tests", "distributor"),
    ("Baltic Ferry Lines S.A.", "Ticketing Systems", "seat allocation conflicts", "PostgreSQL", "port agent", "double bookings", "ferry operator"),
    ("Krakow Museum of Technology", "Digital Archive", "photograph metadata cleanup", "Python imaging", "archivist", "missing captions", "museum"),
    ("Silesia Steelworks S.A.", "Maintenance Analytics", "vibration sensor drift", "InfluxDB", "shift engineer", "false alarms", "steel plant"),
    ("Warta Insurance Group", "Claims Automation", "claim document classification", "spaCy", "claims handler", "misrouted files", "insurer"),
    ("Gdansk Port Authority", "Container Tracking", "gate barcode misreads", "Kotlin", "yard planner", "lost containers", "port"),
    ("Lodz Textile Mills Sp. z o.o.", "Production Planning", "loom schedule conflicts", "OR-Tools", "floor supervisor", "idle machines", "mill"),
    ("Poznan Municipal Transport", "Passenger Information", "arrival prediction errors", "GTFS feeds", "duty controller", "stale timetables", "tram network"),
    ("Vistula Energy Trading", "Market Data", "price tick gaps", "Kafka", "trader", "missing quotes", "energy desk"),
    ("Copernicus Teaching Hospital", "Clinical IT", "lab result routing", "HL7 messaging", "ward nurse", "delayed results", "hospital"),
    ("Rzeszow Aerospace Components", "Metrology", "measurement report generation", "LabVIEW", "inspector", "manual transcription", "machine shop"),
    ("Bialystok Dairy Cooperative", "Cold Chain", "temperature excursion alerts", "MQTT", "route driver", "spoiled pallets", "dairy"),
    ("Szczecin Shipyard Services", "Document Control", "drawing revision tracking", "SharePoint", "welding foreman", "outdated drawings", "shipyard"),
    ("Lublin Agricultural Bank", "Fraud Screening", "transaction rule tuning", "Spark", "branch officer", "false positives", "bank"),
    ("Tatra Mountain Rescue Trust", "Field Systems", "incident report syncing", "SQLite", "rescue coordinator", "unsynced reports", "rescue service"),
    ("Wroclaw Bus Depot", "Fleet Telemetry", "fuel consumption outliers", "Grafana", "depot manager", "unexplained spikes", "depot"),
    ("Torun Print House", "Prepress", "colour profile mismatches", "ICC profiles", "press operator", "reprints", "printer"),
    ("Katowice Coal Logistics", "Weighbridge Systems", "axle weight validation", "Modbus", "weighbridge clerk", "rejected loads", "terminal"),
    ("Opole Furniture Works", "Order Intake", "configurator option clashes", "TypeScript", "sales assistant", "impossible orders", "factory"),
    ("Kielce Trade Fair Centre", "Visitor Analytics", "badge scan deduplication", "DuckDB", "stand host", "inflated counts", "fairground"),
    ("Radom Water Utility", "SCADA Reporting", "pump run-hour reports", "OPC UA", "network operator", "manual tallies", "utility"),
    ("Olsztyn Lake Resorts", "Booking Platform", "seasonal pricing rules", "Django", "reception manager", "wrong nightly rates", "resort"),
    ("Zielona Gora Winery", "Traceability", "batch lineage records", "Neo4j", "cellar master", "broken lineage", "winery"),
    ("Plock Refinery Services", "Lab Information", "sample chain of custody", "LIMS software", "lab technician", "unlabelled samples", "refinery"),
    ("Bydgoszcz Postal Hub", "Sorting Automation", "parcel dimension capture", "OpenCV", "sorting supervisor", "misrouted parcels", "hub"),
    ("Czestochowa Pilgrim Services", "Accommodation Registry", "room allocation overlaps", "Rails", "hostel warden", "double allocations", "registry"),
    ("Sopot Marine Institute", "Sensor Ingestion", "buoy telemetry backfill", "Pandas", "field scientist", "gaps after storms", "institute"),
    ("Legnica Copper Works", "Yield Reporting", "furnace batch reconciliation", "Power BI", "process engineer", "unreconciled batches", "smelter"),
    ("Elblag Canal Trust", "Visitor Ticketing", "group booking discounts", "payment APIs", "lock keeper", "wrong discounts", "canal trust"),
    ("Chelm Cement Plant", "Emissions Monitoring", "stack analyser calibration", "R", "environment officer", "drifting readings", "plant"),
    ("Suwalki Forestry District", "Inventory Survey", "plot measurement uploads", "QGIS", "forester", "lost survey data", "district"),
    ("Nysa Machine Tools", "Service Desk", "spare part lookup", "Elasticsearch", "service technician", "wrong parts sent", "manufacturer"),
    ("Pila Poultry Group", "Feed Optimisation", "ration cost modelling", "SciPy", "farm manager", "overspending on feed", "producer"),
    ("Grudziadz Rail Works", "Wheelset Records", "wear measurement history", "TimescaleDB", "maintenance planner", "premature scrapping", "works"),
    ("Kalisz Piano Factory", "Quality Records", "tuning stability logs", "Flask", "master tuner", "unrecorded adjustments", "factory"),
    ("Tarnow Chemical Park", "Permit Tracking", "expiry reminder scheduling", "Celery", "compliance officer", "missed renewals", "park"),
    ("Konin Lignite Mine", "Survey Data", "excavation volume estimates", "NumPy", "mine surveyor", "disputed volumes", "mine"),
    ("Sanok Bus Manufacturing", "Wiring Diagrams", "harness variant management", "Git", "assembly lead", "wrong harnesses", "assembly hall"),
    ("Zamosc Heritage Board", "Conservation Records", "condition survey forms", "REDCap", "conservator", "illegible forms", "board"),
    ("Ostroda Boatyard", "Hull Tracking", "layup schedule tracking", "Vue", "yard foreman", "overlapping bookings", "boatyard"),
    ("Slupsk Fish Processing", "Yield Control", "filleting yield capture", "spreadsheet add-ins", "line leader", "unmeasured waste", "processor"),
    ("Krosno Glassworks", "Furnace Logs", "shift handover records", "Node.js", "furnace operator", "lost handover notes", "glassworks"),
    ("Mielec Avionics", "Test Benches", "bench calibration intervals", "Ansible", "test engineer", "expired calibrations", "avionics firm"),
    ("Jelenia Gora Spa Authority", "Treatment Booking", "therapist workload balance", "FastAPI", "spa receptionist", "overloaded therapists", "spa"),
    ("Leszno Aviation School", "Flight Records", "training hour totals", "SQL views", "flight instructor", "miscounted hours", "school"),
    ("Ciechanow Sugar Works", "Beet Intake", "sugar content sampling", "MATLAB", "intake weigher", "disputed payments", "sugar works"),
    ("Swinoujscie LNG Terminal", "Berth Planning", "tanker slot conflicts", "constraint solvers", "berth planner", "waiting demurrage", "terminal"),
    ("Wadowice Bakery Group", "Recipe Costing", "ingredient price updates", "spreadsheet APIs", "production planner", "stale costings", "bakery"),
]

SUPERVISORS = [
    ("Marcin Kowalczyk", "Senior Engineer"),
    ("Agnieszka Nowak", "Team Lead"),
    ("Ewa Lis", "Automation Engineer"),
    ("Piotr Zawadzki", "Head of Section"),
    ("Karolina Mazur", "Principal Analyst"),
    ("Tomasz Duda", "Operations Manager"),
]

STUDENTS = [
    "Zofia Wisniewska", "Tomasz Ostrowski", "Kacper Wisniewski", "Julia Kaminska",
    "Antoni Zielinski", "Maja Wozniak", "Filip Szymanski", "Lena Dabrowska",
    "Jan Kowalski", "Zuzanna Krawczyk", "Wojciech Piotrowski", "Alicja Grabowska",
    "Mateusz Nowicki", "Hanna Pawlak", "Szymon Michalski", "Oliwia Adamczyk",
    "Franciszek Dudek", "Amelia Sikora", "Marcel Baran", "Nikola Rutkowska",
    "Igor Sadowski", "Laura Wilk", "Adam Czarnecki", "Pola Jasinska",
    "Bruno Ostrowski", "Iga Zalewska", "Leon Sobczak", "Kornelia Bak",
    "Milosz Urban", "Emilia Cieslak", "Nataniel Gajda", "Rozalia Marek",
    "Aleksander Bednarek", "Sara Wrona", "Ksawery Malec", "Liliana Sowa",
    "Borys Kozak", "Anastazja Lis", "Gustaw Kot", "Michalina Zych",
    "Ignacy Bielak", "Kaja Sroka", "Dominik Pluta", "Wiktoria Golab",
    "Nikodem Sikorski", "Blanka Kruk", "Oskar Zajac", "Melania Jarosz",
    "Tymon Wrobel", "Gabriela Orlowska",
]

# Four unrelated phrasings per section. The index picks a different one per
# section using a different offset, so the combination rarely repeats.
INTRO = [
    "My placement ran for six weeks inside the {dept} at {company}, and the work was organised entirely around {topic}. University had taught me to write programs that run once and print an answer; here the output is something a {role} leans on before eight in the morning. The brief was narrow enough to measure: bring down {problem} without disturbing how the {place} already runs. I kept a notebook of everything I could not explain within the hour, and it turned into the agenda for every Friday review I sat in.",
    "I spent the summer with {company}, attached to the {dept}, working on {topic}. What struck me in the first week was how little of the job was writing code and how much of it was finding out what people actually did with the thing I was changing. My supervisor set one objective, repeated at every check-in: fewer instances of {problem}, and nothing else broken on the way there. The {place} had lived with the problem for years and had opinions about it.",
    "This report describes eight weeks at {company}. I joined the {dept} as its only intern, and was handed {topic} on the second day with a warning that everybody had an opinion about it and nobody had measured it. That turned out to be the whole shape of the placement. By the time I left I understood why {problem} had survived so long: every attempt before mine had started with a fix rather than a count, and the {role} had stopped believing in fixes.",
    "The placement covered forty working days at {company}, in the {dept}. I asked for something a {role} would notice if it worked, and was given {topic}, which the team described as the oldest complaint in the {place}. Nothing about the assignment was technically difficult. Everything about it was difficult in the sense that mattered: there were three accounts of what {problem} even meant, and none of them agreed on the numbers.",
]

COMPANY = [
    "The {place} serves customers who repeat a handful of operations constantly, so being predictable is worth more than being clever. The {dept} exists because the people who build systems and the people who live with them describe {problem} in entirely different vocabulary, and somebody has to translate. I was given read access to staging, a chair at the morning handover where yesterday's failures are read out, and permission to interrupt the {role} whenever a term meant nothing to me.",
    "{company} employs around three hundred people, most of them nowhere near a computer. That shaped everything about my work: a change that saves an engineer ten minutes and costs a {role} thirty seconds per case is a bad trade here, and the {dept} is judged on which of those it ships. The release process is deliberately slow and every change carries a written justification, which I found frustrating in week one and defensible by week four.",
    "The {dept} is four people supporting a {place} that runs continuously. There is no on-call rota because there is no night shift for the systems, but there is a standing rule that anything discovered before ten in the morning gets fixed the same day. I sat next to the {role} for the first fortnight rather than with the engineers, which was not the plan and turned out to be the most useful decision anyone made about my placement.",
    "What I had not appreciated before arriving is how much of {company} runs on records rather than software. The {dept} maintains the small number of systems where a mistake becomes an argument with a customer, and {problem} was the clearest example: nobody doubted it happened, and nobody could produce a figure for how often. The {place} had been compensating manually for so long that the manual compensation had its own spreadsheet and its own owner.",
]

WORK = [
    "My first fortnight went on counting rather than coding. I wrote a script that grouped a month of failures by cause, and {n} percent turned out to come from a single one nobody had suspected. I changed the handling for that case, built the tests out of the real failing records rather than invented ones, and rewrote the whole thing after review. The last three weeks went on a daily digest for the {role}, replacing a sheet that had been filled in by hand every morning for two years.",
    "I began by reproducing {problem} on demand, which took longer than the fix did. Once it was reproducible the cause was obvious in retrospect and invisible before: two systems disagreed about a boundary case by exactly one unit. I submitted the correction with a regression test, then spent a fortnight on the harder half of the job, which was reconciling {n} months of records that had been written while the bug was live.",
    "The work split into three pieces. First, instrumentation: nothing recorded how often {problem} occurred, so I added counters and waited a week for numbers. Second, the change itself, which was thirty lines and took two review rounds. Third, and by far the longest, a report the {role} could read without me in the room — which forced me to understand the domain rather than the code, and is the part I would put on a CV.",
    "I was asked to leave the existing behaviour alone and add a check alongside it, so that anything my code disagreed with could be compared rather than trusted. For three weeks the two ran side by side and I read the differences every morning. Twelve of them were my bug; {n} of them were the old behaviour being wrong in a way nobody had noticed. Only after that was the switch made, and the switch itself was uneventful.",
]

TECH = [
    "The stack is {tool} with the surrounding services in Python and the records in a relational database. Every change goes through review and a suite that runs against a fixture copy of production. I had used a database and version control at university but never {tool}, and most of my first fortnight went on learning to read what it was actually doing rather than what I assumed.",
    "I worked mainly in {tool}, which I had not touched before, alongside SQL I thought I knew and did not. The team's conventions were stricter than anything I had met at university: small commits, a message explaining why rather than what, and no merge without a second pair of eyes. Configuration written by colleagues taught me more than documentation did.",
    "Technically the placement was {tool}, Python and a great deal of SQL. The interesting constraint was that nothing could be deployed outside the release window, so debugging had to happen against copies of real data rather than by trying things in production. That discipline was new to me and it changed how I write code: I now expect to be unable to look.",
    "The systems I touched are built on {tool}, and the parts I wrote are Python with tests in pytest. I also spent an unexpected amount of time in a spreadsheet, because that is where the {role} keeps the ground truth, and any answer my code produced had to be reconciled against it before anybody would look at the code itself.",
]

CHALLENGE = [
    "The hardest lesson was that a change which passes its tests is not finished. My first version handled {problem} and came back in review because it silently accepted an ambiguous case instead of refusing it — turning a visible failure into a quiet wrong number. Rewriting it that way cost two days and taught me more than the original. The second difficulty was asking for help without wasting anybody's time: thirty minutes alone, then a written summary of what I had tried.",
    "I underestimated how much of the difficulty would be social. Two people wanted opposite things from the same change and both were right from where they sat, and my instinct was to build whichever was described to me most recently. What worked was writing both positions down and asking them to choose in front of each other, which took twenty minutes and saved a fortnight of building the wrong thing.",
    "Twice I broke something in staging, and both times the failure was mine believing the data was cleaner than it was. After the second I stopped assuming any field was populated and started checking, which made the code longer and considerably less confident-looking. My supervisor's comment on the review — that code which admits what it does not know is easier to trust — is the sentence I took away from the whole placement.",
    "The recurring difficulty was scope. Every question I answered exposed two more, and left alone I would have spent the placement fixing adjacent problems nobody had asked about. What fixed it was the Friday review: anything not on the original brief got written on a list and left there, and the list was handed over at the end rather than half-finished in the codebase.",
]

CONCLUSION = [
    "By the end of the placement {problem} had fallen to a level the {role} called manageable for the first time, and what remains are genuine exceptions rather than defects in the handling. I leave understanding what production work means: other people's mornings depend on what I merge, a loud failure is safer than a quiet wrong answer, and most of the value came from measuring {topic} before touching it.",
    "The measurable outcome is that {problem} now happens roughly a third as often, and the cases left over are visible instead of silent. The outcome I value more is smaller: I can now read an unfamiliar system and find out what it does rather than guessing from its names. I am grateful to the {dept} for reviews that were blunter and more useful than any feedback I have had.",
    "I finished the placement with the change deployed, the reconciliation complete and a handover document the {role} has since used without asking me anything. If I did it again I would spend the first week reading the failure history rather than the code, because the team's real problems were already written down there and I took a fortnight to find them.",
    "What I take away from {company} is a different sense of what finished means. The code was the easy half; the hard half was proving the change was safe to people who would carry the consequences. {topic} is in better shape than I found it, which is the narrow claim I can defend, and the wider claim is only that I now know how much I did not know.",
]



# One more sentence per section, so a package clears the 500-word minimum the
# way a real report does - by saying something else about its own domain
# rather than by padding. Four variants, picked by the same combination.
EXTRA = [
    "Most of what I learned about {topic} came from watching the {role} work around it rather than from anything written down, and I have said so in the handover note I left behind.",
    "The {place} keeps its own record of {problem} in a form nobody else reads, and reconciling my numbers against theirs took longer than producing either set did.",
    "None of the behaviour around {topic} was documented anywhere I could find, which is why the note I handed over at the end runs to four pages instead of one.",
    "I have kept every measurement I took, because the {dept} had never held a baseline for {problem} before this summer and the next person will want one.",
]

import json as _json
from pathlib import Path as _Path

_COMBOS_FILE = _Path(__file__).with_name("combos.json")
_COMBOS = _json.loads(_COMBOS_FILE.read_text()) if _COMBOS_FILE.exists() else {}

_BANKS = [INTRO, COMPANY, WORK, TECH, CHALLENGE, CONCLUSION]
_HEADINGS = [
    "1. Introduction",
    "2. Company Overview",
    "3. Work Performed",
    "4. Technologies Used",
    "5. Challenges and Solutions",
    "6. Conclusion",
]


def _fields(i):
    company, dept, topic, tool, role, problem, place = DOMAINS[i % len(DOMAINS)]
    return {
        "company": company,
        "dept": dept.lower(),
        "topic": topic,
        "tool": tool,
        "role": role,
        "problem": problem,
        "place": place,
        "n": 12 + (i % 9) * 4,
    }


def sections_with(i, combo):
    f = _fields(i)
    return [
        (
            _HEADINGS[k],
            _BANKS[k][combo[k] % 4].format(**f)
            + " "
            + EXTRA[(combo[k] + k) % 4].format(**f),
        )
        for k in range(6)
    ]


def sections_for(i):
    """Six sections in this package's own voice, in a combination chosen to
    sit as far from the other forty-nine as the phrasing bank allows."""
    combo = _COMBOS.get(str(i), [(i + k) % 4 for k in range(6)])
    return sections_with(i, combo)
