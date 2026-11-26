# SPDX-License-Identifier: MIT
"""Deterministic broadsheet renderer for Thursday 26 November 2026 world news.

Builds a 1024x1024 editorial infographic front page with 45 dated stories
across 9 regions and 19 fields, 13 bespoke high-contrast inline-SVG vector
scenes, a smooth vector world map with collision-free numbered pins and a
framed GLOBAL / SPACE inset, KPI strip, and DATE CHECK audit footer.
"""

from collections import Counter
import html
import math
import pathlib
import subprocess
import tempfile
from PIL import Image

REPO = pathlib.Path(__file__).resolve().parent

REGIONS = [
    ("East & SE Asia", "E. & SE Asia", "#196658"),
    ("Middle East", "Middle East", "#B3501A"),
    ("Europe", "Europe", "#235380"),
    ("North America", "N. America", "#9E2A2B"),
    ("Oceania", "Oceania", "#3E6B8C"),
    ("Africa", "Africa", "#876715"),
    ("Latin America", "Lat. Am.", "#C2532C"),
    ("South Asia", "S. Asia", "#456B2A"),
    ("Global & Space", "Global", "#444D57"),
]
REGION_COLOR = {r[0]: r[2] for r in REGIONS}
REGION_SHORT = {r[0]: r[1] for r in REGIONS}

HEROES = [
    {
        "id": 1,
        "region": "East & SE Asia",
        "location": "SEOUL",
        "field": "Economy",
        "certainty": "OFFICIAL",
        "headline": "Bank of Korea hikes rate to 3.25%, lifts 2026 GDP outlook to 3.9%",
        "summary": "Third hike of 2026 (+25 bps) curbs inflation as AI chip exports lift 2026 growth forecast from 3.3% to 3.9% and 2027 to 4.1%.",
        "why": "Chip export boom drives growth while higher borrowing costs squeeze households",
        "lon": 127.0,
        "lat": 37.5,
        "scene": "bok_hike",
    },
    {
        "id": 2,
        "region": "East & SE Asia",
        "location": "PYONGYANG",
        "field": "Security",
        "certainty": "REPORTED",
        "headline": "Kim Jong Un orders wider deployment of tactical nuclear arms",
        "summary": "Inspecting nuclear material sites, state media KCNA quotes Kim calling nuclear status 'inviolable' and pushing multi-domain rollout.",
        "why": "Signals broader tactical nuclear posture across East Asian flashpoints",
        "lon": 125.7,
        "lat": 39.0,
        "scene": "nk_nukes",
    },
    {
        "id": 3,
        "region": "Middle East",
        "location": "RIYADH · SANAA",
        "field": "Conflict",
        "certainty": "OFFICIAL",
        "headline": "Saudi coalition downs 2 Houthi missiles over Riyadh; blast hits Sanaa",
        "summary": "Air defenses destroy both ballistic missiles after midnight alert; blast rocks Sanaa airport area; UKMTO logs tanker blast off Dubai.",
        "why": "Red Sea and Gulf conflict widens across regional capitals and sea lanes",
        "lon": 46.7,
        "lat": 24.7,
        "scene": "riyadh_missiles",
    },
]

SECONDARY = [
    {
        "id": 4,
        "region": "North America",
        "location": "NEW YORK",
        "field": "Weather",
        "pill": "1ST IN 100 YRS",
        "headline": "Nor'easter moves Macy's 100th parade to Saturday",
        "summary": "65 mph gusts & flood alerts hit 80m US travelers as NYC shifts march. (AFP)",
        "lon": -74.0,
        "lat": 40.7,
        "scene": "macys_storm",
    },
    {
        "id": 5,
        "region": "Middle East",
        "location": "GENEVA · GAZA",
        "field": "Justice",
        "pill": "UN TRIBUNAL",
        "headline": "UN tribunal faults sacking of Gaza aid staff",
        "summary": "Ruling doubts claims of Hamas links; Oxfam calls Gaza 'toxic wasteland'. (Guardian)",
        "lon": 34.4,
        "lat": 31.5,
        "scene": "un_gaza",
    },
    {
        "id": 6,
        "region": "Europe",
        "location": "BRUSSELS",
        "field": "Diplomacy",
        "pill": "€70B KYIV AID",
        "headline": "Special EU Council & Euro Summit open",
        "summary": "Leaders convene under Costa on EU budget and €70bn 2027 Kyiv aid. (EU Council)",
        "lon": 4.35,
        "lat": 50.85,
        "scene": "eu_summit",
    },
    {
        "id": 7,
        "region": "East & SE Asia",
        "location": "JAKARTA",
        "field": "Business",
        "pill": "$50 BILLION",
        "headline": "China consortium signs $50bn Indonesia pact",
        "summary": "Initial deal with sovereign wealth fund targets 10 smart-city zones. (SCMP)",
        "lon": 106.8,
        "lat": -6.2,
        "scene": "indonesia_50b",
    },
    {
        "id": 8,
        "region": "East & SE Asia",
        "location": "TOKYO",
        "field": "Business",
        "pill": "$125B ROE PLAN",
        "headline": "Japan's Mitsui unveils $125bn asset overhaul",
        "summary": "Trading giant plans sweeping portfolio shake-up to lift returns. (Nikkei)",
        "lon": 139.7,
        "lat": 35.7,
        "scene": "mitsui_tokyo",
    },
    {
        "id": 9,
        "region": "Africa",
        "location": "LUSAKA",
        "field": "Politics",
        "pill": "PROTEST BAN",
        "headline": "Zambia bans rally against term-limit bid",
        "summary": "Police block opposition march while senior critics stay jailed. (Al Jazeera)",
        "lon": 28.3,
        "lat": -15.4,
        "scene": "zambia_ban",
    },
    {
        "id": 10,
        "region": "Oceania",
        "location": "CANBERRA",
        "field": "Economy",
        "pill": "4.9% CPI SHOCK",
        "headline": "Australia Labor hit over seniors' rebate cuts",
        "summary": "After 3-year high 4.9% CPI, Labor-Greens trim rebates; MP defects. (SBS)",
        "lon": 149.1,
        "lat": -35.3,
        "scene": "aus_cpi",
    },
    {
        "id": 11,
        "region": "Europe",
        "location": "LONDON",
        "field": "Climate",
        "pill": "MET OFFICE",
        "headline": "UK Met Office warns seasons are shifting",
        "summary": "Fewer frosts and hotter summer spikes disrupt UK crops & wildlife. (BBC)",
        "lon": -0.1,
        "lat": 51.5,
        "scene": "uk_climate",
    },
    {
        "id": 12,
        "region": "Latin America",
        "location": "SÃO PAULO",
        "field": "Markets",
        "pill": "1-YEAR LOW",
        "headline": "LatAm stocks hit 1-year low on rate fears",
        "summary": "MSCI LatAm drops 0.86% and FX falls 1.5% in 4th weekly slide. (GMT Eight)",
        "lon": -46.6,
        "lat": -23.5,
        "scene": "latam_low",
    },
    {
        "id": 13,
        "region": "Global & Space",
        "location": "DIMORPHOS",
        "field": "Space",
        "pill": "DART CRATER",
        "headline": "New views reveal NASA DART asteroid scar",
        "summary": "Sharp images expose crater from planetary-defense impact test. (ESA / ST)",
        "lon": 0.0,
        "lat": 0.0,
        "inset": True,
        "scene": "dart_crater",
    },
]

# Concise single-line verified briefs (16 + 16 = 32) so every single brief fits cleanly on 1 line.
BRIEFS = [
    # Column 1 (#14–#29)
    {"id": 14, "region": "East & SE Asia", "field": "Justice", "loc": "Seoul", "text": "Judges issue first joint protest calling impeachment unconstitutional", "claim": False, "lon": 128.8, "lat": 35.8},
    {"id": 15, "region": "East & SE Asia", "field": "Justice", "loc": "Seoul", "text": "Supreme Court set to rule Thursday on ex-President Yoon's perjury case", "claim": False, "lon": 127.4, "lat": 36.2},
    {"id": 16, "region": "East & SE Asia", "field": "Markets", "loc": "Seoul", "text": "Kospi opens higher Thursday in tentative bounce after AI chip sell-off", "claim": False, "lon": 129.1, "lat": 35.1},
    {"id": 17, "region": "East & SE Asia", "field": "Trade", "loc": "Hanoi", "text": "Vietnam pushes to close US trade deal urgently after 35% tariff threat", "claim": False, "lon": 105.8, "lat": 21.0},
    {"id": 18, "region": "East & SE Asia", "field": "Security", "loc": "Manila", "text": "Military confirms tracking Chinese H-6 bomber 170 nm off Metro Manila", "claim": False, "lon": 121.0, "lat": 14.6},
    {"id": 19, "region": "East & SE Asia", "field": "Tech", "loc": "Tokyo", "text": "Researchers unveil wearable leg-support robot synced to user's steps", "claim": False, "lon": 135.5, "lat": 34.7},
    {"id": 20, "region": "Middle East", "field": "Conflict", "loc": "Hasakah", "text": "ISIL suicide attack kills 2 Syrian security staff; 4 attackers die", "claim": False, "lon": 40.7, "lat": 36.5},
    {"id": 21, "region": "Middle East", "field": "Conflict", "loc": "Gaza City", "text": "Israeli drone strike in eastern Gaza City kills 3 Palestinians", "claim": False, "lon": 34.5, "lat": 31.5},
    {"id": 22, "region": "Middle East", "field": "Diplomacy", "loc": "Tel Aviv", "text": "US envoy Kushner urges Israel to pivot from wartime to economic ties", "claim": False, "lon": 34.8, "lat": 32.1},
    {"id": 23, "region": "Middle East", "field": "Politics", "loc": "Jerusalem", "text": "Knesset advances bill repealing Karhi's disputed broadcast overhaul", "claim": False, "lon": 35.2, "lat": 31.8},
    {"id": 24, "region": "Europe", "field": "Diplomacy", "loc": "Berlin", "text": "Chancellor Merz defends Kyiv aid: 'Russia wants more than Ukraine'", "claim": False, "lon": 13.4, "lat": 52.5},
    {"id": 25, "region": "Europe", "field": "Justice", "loc": "London", "text": "UK plans new stalking law dropping requirement to prove distress", "claim": False, "lon": -1.5, "lat": 52.9},
    {"id": 26, "region": "Europe", "field": "Politics", "loc": "Madrid", "text": "Spain heads into Sunday snap vote as Feijóo challenges Socialist rule", "claim": False, "lon": -3.7, "lat": 40.4},
    {"id": 27, "region": "Europe", "field": "Culture", "loc": "London", "text": "Patrick Radden Keefe's 'London Falling' wins Waterstones Book of Year", "claim": False, "lon": -2.6, "lat": 51.4},
    {"id": 28, "region": "Europe", "field": "Science", "loc": "Dublin", "text": "Giant deer bones push human arrival in Ireland back 1,000 years", "claim": False, "lon": -6.3, "lat": 53.3},
    {"id": 29, "region": "North America", "field": "Politics", "loc": "Washington", "text": "Sen. Van Hollen gains backing to challenge Schumer as Senate leader", "claim": False, "lon": -77.0, "lat": 38.9},
    # Column 2 (#30–#45)
    {"id": 30, "region": "North America", "field": "Health", "loc": "Atlanta", "text": "US CDC logs 9 measles deaths in 2026 as cases hit 35-year high", "claim": False, "lon": -84.4, "lat": 33.7},
    {"id": 31, "region": "North America", "field": "Sport", "loc": "Pittsburgh", "text": "Steelers waive QB Aaron Rodgers after blast at coach McCarthy", "claim": False, "lon": -80.0, "lat": 40.4},
    {"id": 32, "region": "North America", "field": "Sport", "loc": "Detroit", "text": "MLB Tigers agree to 1-year, $25m deal with RHP Kevin Gausman", "claim": False, "lon": -83.0, "lat": 42.3},
    {"id": 33, "region": "North America", "field": "Culture", "loc": "Los Angeles", "text": "Brad Pitt and Angelina Jolie settle French winery suit out of court", "claim": False, "lon": -118.2, "lat": 34.0},
    {"id": 34, "region": "Oceania", "field": "Energy", "loc": "Southland", "text": "Meridian invests $30m in Datagrid with 140 MW data-center option", "claim": False, "lon": 168.3, "lat": -46.4},
    {"id": 35, "region": "Oceania", "field": "Sport", "loc": "Suva", "text": "World Rugby suspends Oceania Rugby from Council amid audit", "claim": False, "lon": 178.4, "lat": -18.1},
    {"id": 36, "region": "Oceania", "field": "Health", "loc": "Wellington", "text": "NZ exercise body warns weight-loss drugs risk frailty and fractures", "claim": False, "lon": 174.8, "lat": -41.3},
    {"id": 37, "region": "Oceania", "field": "Rights", "loc": "Port Moresby", "text": "PNG condemns alleged killing of 5 women over sorcery", "claim": True, "lon": 147.2, "lat": -9.4},
    {"id": 38, "region": "Africa", "field": "Energy", "loc": "Nairobi", "text": "Kenya Power warns ending electricity monopoly strains subsidies", "claim": False, "lon": 36.8, "lat": -1.3},
    {"id": 39, "region": "Africa", "field": "Weather", "loc": "Cape Town", "text": "SA Weather Service issues extreme fire & 36°C heat alerts", "claim": False, "lon": 18.4, "lat": -33.9},
    {"id": 40, "region": "Africa", "field": "Economy", "loc": "Johannesburg", "text": "Ramaphosa leads MSME summit; NCOP reviews 66 municipalities", "claim": False, "lon": 28.0, "lat": -26.2},
    {"id": 41, "region": "Latin America", "field": "Diplomacy", "loc": "Santiago", "text": "Polish President Nawrocki addresses UN ECLAC on S. America trip", "claim": False, "lon": -70.6, "lat": -33.4},
    {"id": 42, "region": "Latin America", "field": "Rights", "loc": "Mexico City", "text": "UN praises Sheinbaum government's gender-violence prevention", "claim": False, "lon": -99.1, "lat": 19.4},
    {"id": 43, "region": "South Asia", "field": "Security", "loc": "New Delhi", "text": "NHAI launches 1033-linked rapid crash-response highway teams", "claim": False, "lon": 77.2, "lat": 28.6},
    {"id": 44, "region": "South Asia", "field": "Business", "loc": "Mumbai", "text": "Actor Ajay Devgn sues food regulator over cardamom ad ban", "claim": False, "lon": 72.9, "lat": 19.1},
    {"id": 45, "region": "Global & Space", "field": "Climate", "loc": "UN / Global", "text": "EU carbon border levy (CBAM) & farm climate aid lead talks", "claim": False, "lon": 0.0, "lat": 0.0, "inset": True},
]

ALL_STORIES = HEROES + SECONDARY + BRIEFS
assert len(ALL_STORIES) == 45, f"Expected 45 stories, got {len(ALL_STORIES)}"


def hero_svg(kind: str) -> str:
    """Three high-contrast wide vector scenes forming a cohesive triptych at 300px."""
    if kind == "bok_hike":
        # Rich deep emerald-teal panel matching dark contrast weight of #2 & #3,
        # with accurate 3rd hike stepping UP right at NOV 26 and honest 0-based GDP bars.
        return """
        <svg viewBox="0 0 310 94" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <rect width="310" height="94" fill="#10362F"/>
          <!-- Grid lines -->
          <line x1="16" y1="74" x2="188" y2="74" stroke="#2D665B" stroke-width="1"/>
          <line x1="16" y1="54" x2="188" y2="54" stroke="#214E45" stroke-width="0.8" stroke-dasharray="3,2"/>
          <line x1="16" y1="34" x2="188" y2="34" stroke="#214E45" stroke-width="0.8" stroke-dasharray="3,2"/>
          <!-- Accurate BOK 2026 path: H1 2.50 -> JUL 2.75 -> AUG 3.00 -> OCT hold 3.00 -> NOV 26 HIKE 3.25 -->
          <polyline points="18,68 48,68 48,57 86,57 86,46 156,46 156,31 184,31" fill="none" stroke="#62E3B7" stroke-width="3.2" stroke-linejoin="miter"/>
          <circle cx="156" cy="31" r="4.6" fill="#F2C94C" stroke="#9E2A2B" stroke-width="2"/>
          <text x="18" y="85" font-family="Liberation Sans, sans-serif" font-size="7.4" fill="#A5CFC4" font-weight="700">H1</text>
          <text x="45" y="85" font-family="Liberation Sans, sans-serif" font-size="7.4" fill="#A5CFC4" font-weight="700">JUL</text>
          <text x="82" y="85" font-family="Liberation Sans, sans-serif" font-size="7.4" fill="#A5CFC4" font-weight="700">AUG</text>
          <text x="118" y="85" font-family="Liberation Sans, sans-serif" font-size="7.4" fill="#8BB5AA" font-weight="700">OCT</text>
          <text x="150" y="85" font-family="Liberation Sans, sans-serif" font-size="7.6" fill="#F2C94C" font-weight="700">NOV 26</text>
          <!-- Top badges -->
          <rect x="16" y="7" width="84" height="16" rx="2" fill="#1D5C4F" stroke="#62E3B7" stroke-width="0.9"/>
          <text x="58" y="18" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="8.6" fill="#FFFFFF" font-weight="700">BOK RATE 3.25%</text>
          <rect x="105" y="7" width="46" height="16" rx="2" fill="#C43839"/>
          <text x="128" y="18" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="8.4" fill="#FFFFFF" font-weight="700">+25 bps</text>
          <!-- Right panel: 0-based GDP forecast bars (2026: 3.9%, 2027: 4.1% on 0..5% scale) -->
          <rect x="200" y="7" width="100" height="80" rx="3" fill="#0B2520" stroke="#2D665B" stroke-width="1"/>
          <text x="250" y="18" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="7.4" fill="#9FD6C8" font-weight="700">GDP OUTLOOK</text>
          <line x1="210" y1="73" x2="290" y2="73" stroke="#39786C" stroke-width="1"/>
          <!-- 3.9% -> height 35.1px, 4.1% -> height 36.9px from y=73 (0% baseline) -->
          <rect x="218" y="37.9" width="24" height="35.1" fill="#46B89A"/>
          <text x="230" y="34" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="9" fill="#FFFFFF" font-weight="700">3.9%</text>
          <text x="230" y="83" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="7.4" fill="#B5DCD2" font-weight="700">2026</text>
          <rect x="258" y="36.1" width="24" height="36.9" fill="#F2C94C"/>
          <text x="270" y="32" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="9" fill="#F2C94C" font-weight="700">4.1%</text>
          <text x="270" y="83" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="7.4" fill="#B5DCD2" font-weight="700">2027</text>
        </svg>"""
    if kind == "nk_nukes":
        return """
        <svg viewBox="0 0 310 94" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <rect width="310" height="94" fill="#141923"/>
          <circle cx="94" cy="51" r="34" fill="none" stroke="#2D394E" stroke-width="1.1"/>
          <circle cx="94" cy="51" r="22" fill="none" stroke="#2D394E" stroke-width="0.9"/>
          <circle cx="94" cy="51" r="11" fill="none" stroke="#3C4D68" stroke-width="0.9"/>
          <line x1="56" y1="51" x2="132" y2="51" stroke="#2D394E" stroke-width="0.8"/>
          <line x1="94" y1="13" x2="94" y2="89" stroke="#2D394E" stroke-width="0.8"/>
          <!-- Radiation trefoil -->
          <path d="M94,51 L83,33 A21,21 0 0,1 105,33 Z" fill="#F0B442"/>
          <path d="M94,51 L115,51 A21,21 0 0,1 104,69 Z" fill="#F0B442"/>
          <path d="M94,51 L84,69 A21,21 0 0,1 73,51 Z" fill="#F0B442"/>
          <circle cx="94" cy="51" r="7" fill="#141923"/>
          <circle cx="94" cy="51" r="4.2" fill="#F0B442"/>
          <!-- Multi-domain trajectories -->
          <path d="M130,72 Q178,16 230,32" fill="none" stroke="#E85353" stroke-width="2.2" stroke-dasharray="4,2"/>
          <path d="M130,72 Q184,45 244,55" fill="none" stroke="#F5BE4F" stroke-width="2" stroke-dasharray="4,2"/>
          <path d="M130,72 Q190,71 254,78" fill="none" stroke="#64B5F6" stroke-width="2" stroke-dasharray="4,2"/>
          <polygon points="233,33 224,29 226,37" fill="#E85353"/>
          <polygon points="247,56 238,52 240,60" fill="#F5BE4F"/>
          <polygon points="257,79 248,75 250,83" fill="#64B5F6"/>
          <rect x="176" y="7" width="122" height="16" rx="2" fill="#B52B2B"/>
          <text x="237" y="18" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="8.2" fill="#FFFFFF" font-weight="700">MULTI-DOMAIN TACTICAL</text>
          <text x="242" y="36" font-family="Liberation Sans, sans-serif" font-size="8.2" fill="#F7A1A1" font-weight="700">AIR</text>
          <text x="253" y="58" font-family="Liberation Sans, sans-serif" font-size="8.2" fill="#FAD789" font-weight="700">LAND</text>
          <text x="263" y="81" font-family="Liberation Sans, sans-serif" font-size="8.2" fill="#9ED3FF" font-weight="700">SEA</text>
          <text x="12" y="17" font-family="Liberation Sans, sans-serif" font-size="7.6" fill="#AEBCD1" font-weight="700">KCNA · 26 NOV</text>
        </svg>"""
    return """
    <svg viewBox="0 0 310 94" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="310" height="94" fill="#182A4A"/>
      <rect x="0" y="72" width="310" height="22" fill="#0F1B30"/>
      <!-- Higher-contrast Riyadh skyline -->
      <rect x="16" y="54" width="15" height="18" fill="#466596"/>
      <rect x="36" y="42" width="16" height="30" fill="#5478B0"/>
      <path d="M60,72 L60,28 L68,28 L69,38 L73,38 L74,28 L82,28 L82,72 Z" fill="#6D94CF"/>
      <polygon points="94,72 102,38 110,72" fill="#5478B0"/>
      <rect x="118" y="50" width="18" height="22" fill="#466596"/>
      <rect x="142" y="58" width="16" height="14" fill="#3B5785"/>
      <!-- Incoming missiles -->
      <path d="M294,68 Q222,14 148,30" fill="none" stroke="#F06D5B" stroke-width="2.2" stroke-dasharray="4,2"/>
      <path d="M286,78 Q228,34 176,46" fill="none" stroke="#F06D5B" stroke-width="2.2" stroke-dasharray="4,2"/>
      <!-- Interceptors -->
      <line x1="71" y1="64" x2="146" y2="31" stroke="#7AE0FF" stroke-width="1.9"/>
      <line x1="102" y1="64" x2="174" y2="47" stroke="#7AE0FF" stroke-width="1.9"/>
      <!-- Golden bursts -->
      <polygon points="147,20 150,28 158,27 152,32 155,40 147,35 139,40 142,32 136,27 144,28" fill="#FFC847"/>
      <polygon points="175,37 178,44 185,43 180,48 183,55 175,50 167,55 170,48 165,43 172,44" fill="#FFC847"/>
      <!-- Crisp badges -->
      <rect x="12" y="7" width="98" height="16" rx="2" fill="#C2551B"/>
      <text x="61" y="18" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="8.2" fill="#FFFFFF" font-weight="700">2 MISSILES DOWNED</text>
      <rect x="196" y="7" width="102" height="16" rx="2" fill="#2A4470" stroke="#85AEE8" stroke-width="1"/>
      <text x="247" y="18" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="7.5" fill="#FFFFFF" font-weight="700">SANAA &amp; GULF ALERTS</text>
      <text x="24" y="86" font-family="Liberation Sans, sans-serif" font-size="7.8" fill="#DCE8FA" font-weight="700">RIYADH SKYLINE</text>
      <text x="200" y="86" font-family="Liberation Sans, sans-serif" font-size="7.6" fill="#FFC2B4" font-weight="700">DUBAI TANKER: 50 NM</text>
    </svg>"""


def secondary_svg(kind: str, pill: str) -> str:
    """Ten bold flat-vector editorial illustrations tuned for clarity at 1024px and 300px."""
    art = ""
    bg = "#E8EEF2"
    pill_bg = "#111827"
    pill_border = "none"
    if kind == "macys_storm":
        bg = "#1E3046"
        art = """
          <!-- Manhattan skyline base -->
          <rect x="0" y="42" width="188" height="12" fill="#121E2E"/>
          <rect x="14" y="34" width="12" height="10" fill="#2F4969"/>
          <rect x="30" y="28" width="10" height="16" fill="#3A597E"/>
          <rect x="148" y="30" width="12" height="14" fill="#2F4969"/>
          <rect x="164" y="24" width="12" height="20" fill="#3A597E"/>
          <!-- Strong wind gusts -->
          <path d="M18,26 L70,26 M63,22 L70,26 L63,30" stroke="#8BD1FA" stroke-width="2.2" fill="none"/>
          <path d="M26,36 L82,36 M75,32 L82,36 L75,40" stroke="#8BD1FA" stroke-width="2.2" fill="none"/>
          <!-- Iconic Macy's star parade balloon tied down on ropes -->
          <polygon points="118,12 123,22 135,23 126,30 129,41 118,35 107,41 110,30 101,23 113,22" fill="#E04646" stroke="#FFD670" stroke-width="1.3"/>
          <line x1="112" y1="38" x2="102" y2="50" stroke="#FFD670" stroke-width="1.4"/>
          <line x1="124" y1="38" x2="134" y2="50" stroke="#FFD670" stroke-width="1.4"/>
          <text x="16" y="51" font-family="Liberation Sans, sans-serif" font-size="8.2" fill="#FFD670" font-weight="700">65 MPH GUSTS</text>
        """
    elif kind == "un_gaza":
        bg = "#203D5C"
        art = """
          <!-- White dismissal dossier with bold red UNPROVEN stamp -->
          <rect x="20" y="20" width="54" height="30" rx="2" fill="#F8F5EE" stroke="#99B6D6" stroke-width="1.2"/>
          <line x1="27" y1="28" x2="66" y2="28" stroke="#98A6B5" stroke-width="2"/>
          <line x1="27" y1="35" x2="60" y2="35" stroke="#98A6B5" stroke-width="2"/>
          <rect x="24" y="38" width="46" height="9" rx="1.5" fill="#B82D2E"/>
          <text x="47" y="45" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="6.8" fill="#FFFFFF" font-weight="700">UNPROVEN</text>
          <!-- Bright gold scales of justice -->
          <line x1="132" y1="12" x2="132" y2="48" stroke="#F2C94C" stroke-width="2.6"/>
          <line x1="104" y1="20" x2="160" y2="20" stroke="#F2C94C" stroke-width="2.2"/>
          <path d="M104,20 L95,36 L113,36 Z" fill="#8CC5F2"/>
          <path d="M160,20 L151,36 L169,36 Z" fill="#8CC5F2"/>
          <rect x="118" y="47" width="28" height="4" fill="#F2C94C"/>
        """
    elif kind == "eu_summit":
        bg = "#17376B"
        stars = []
        for i in range(12):
            ang = i * math.pi / 6
            cx = 52 + 16 * math.cos(ang)
            cy = 32 + 16 * math.sin(ang)
            stars.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.1" fill="#F5CC4C"/>')
        art = "".join(stars) + """
          <text x="52" y="36" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="10" fill="#FFFFFF" font-weight="700">EU</text>
          <rect x="92" y="18" width="82" height="28" rx="3" fill="#275091" stroke="#7BA4E0" stroke-width="1.1"/>
          <text x="133" y="30" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="8.5" fill="#F5CC4C" font-weight="700">EURO SUMMIT</text>
          <text x="133" y="41" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="7.6" fill="#FFFFFF" font-weight="700">26–27 NOV</text>
        """
    elif kind == "indonesia_50b":
        bg = "#13473E"
        art = """
          <rect x="0" y="43" width="188" height="11" fill="#0C2E28"/>
          <rect x="18" y="25" width="14" height="18" fill="#3FA68E"/>
          <rect x="36" y="18" width="16" height="25" fill="#63CFB5"/>
          <rect x="56" y="28" width="12" height="15" fill="#3FA68E"/>
          <rect x="72" y="14" width="18" height="29" fill="#F2C94C"/>
          <rect x="94" y="23" width="14" height="20" fill="#63CFB5"/>
          <rect x="112" y="27" width="12" height="16" fill="#3FA68E"/>
          <path d="M25,25 Q54,8 81,14" fill="none" stroke="#FFD670" stroke-width="1.6" stroke-dasharray="3,2"/>
          <text x="154" y="32" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="14" fill="#FFFFFF" font-weight="700">10</text>
          <text x="154" y="42" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="7.4" fill="#9AE3D0" font-weight="700">CITIES</text>
        """
    elif kind == "mitsui_tokyo":
        bg = "#2A2420"
        art = """
          <!-- Placed below pill (y>=21) so zero collision with pill -->
          <rect x="20" y="37" width="22" height="13" fill="#6FA89B"/>
          <rect x="48" y="30" width="22" height="20" fill="#46B89A"/>
          <rect x="76" y="23" width="22" height="27" fill="#F2C94C"/>
          <path d="M26,33 L56,26 L88,18" fill="none" stroke="#F06D5B" stroke-width="2.4"/>
          <polygon points="93,17 85,15 88,22" fill="#F06D5B"/>
          <!-- Tokyo Tower silhouette -->
          <polygon points="142,50 151,14 160,50" fill="none" stroke="#E87B48" stroke-width="2.4"/>
          <line x1="145" y1="34" x2="157" y2="34" stroke="#E87B48" stroke-width="2.2"/>
          <line x1="143" y1="42" x2="159" y2="42" stroke="#E87B48" stroke-width="2.2"/>
        """
    elif kind == "zambia_ban":
        bg = "#3A2F19"
        art = """
          <rect x="20" y="24" width="44" height="24" rx="2" fill="#C49A2C" stroke="#F7DF8D" stroke-width="1"/>
          <rect x="31" y="19" width="22" height="5" fill="#7D5F13"/>
          <text x="42" y="39" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="8" fill="#1C160A" font-weight="700">TERMS</text>
          <!-- Bold megaphone under crimson ban circle -->
          <polygon points="106,33 138,20 138,46" fill="#F4EFE2"/>
          <rect x="98" y="30" width="10" height="8" fill="#F4EFE2"/>
          <circle cx="122" cy="33" r="17" fill="none" stroke="#E54343" stroke-width="3.6"/>
          <line x1="110" y1="21" x2="134" y2="45" stroke="#E54343" stroke-width="3.6"/>
        """
    elif kind == "aus_cpi":
        bg = "#182E42"
        pill_bg = "#274461"
        pill_border = "#6B96BD"
        art = """
          <line x1="16" y1="48" x2="174" y2="48" stroke="#3B5B78" stroke-width="1"/>
          <polyline points="20,44 54,41 84,35 114,20" fill="none" stroke="#F06856" stroke-width="3.2"/>
          <circle cx="84" cy="35" r="3.4" fill="#7AC7F5"/>
          <circle cx="114" cy="20" r="4.5" fill="#F5CC4C" stroke="#F06856" stroke-width="1.8"/>
          <text x="66" y="46" font-family="Liberation Sans, sans-serif" font-size="7.8" fill="#A8D4F5" font-weight="700">4.3%</text>
          <text x="123" y="25" font-family="Liberation Sans, sans-serif" font-size="12.2" fill="#F5CC4C" font-weight="700">4.9%</text>
          <text x="123" y="36" font-family="Liberation Sans, sans-serif" font-size="7.4" fill="#D4E6F5" font-weight="700">3-YR HIGH</text>
        """
    elif kind == "uk_climate":
        bg = "#1A2F42"
        pill_bg = "#274461"
        pill_border = "#6B96BD"
        art = """
          <rect x="28" y="21" width="9" height="20" rx="4.5" fill="#DCE8F2" stroke="#76A4CC" stroke-width="1.4"/>
          <circle cx="32.5" cy="43" r="7" fill="#E84F3C"/>
          <rect x="30.3" y="25" width="4.4" height="18" fill="#E84F3C"/>
          <circle cx="148" cy="29" r="10.5" fill="#F5B83D"/>
          <line x1="148" y1="13" x2="148" y2="17" stroke="#F5B83D" stroke-width="2.2"/>
          <line x1="148" y1="41" x2="148" y2="45" stroke="#F5B83D" stroke-width="2.2"/>
          <line x1="132" y1="29" x2="136" y2="29" stroke="#F5B83D" stroke-width="2.2"/>
          <line x1="160" y1="29" x2="164" y2="29" stroke="#F5B83D" stroke-width="2.2"/>
          <text x="89" y="30" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="8.6" fill="#99D3FF" font-weight="700">LESS FROST</text>
          <text x="89" y="43" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="8.6" fill="#FFD17A" font-weight="700">HOTTER DAYS</text>
        """
    elif kind == "latam_low":
        bg = "#1B212B"
        pill_bg = "#2A3444"
        pill_border = "#7689A6"
        art = """
          <line x1="86" y1="46" x2="178" y2="46" stroke="#47556E" stroke-width="1" stroke-dasharray="2,2"/>
          <!-- Area fill under plunging curve for bright 300px punch -->
          <polygon points="86,16 106,22 122,19 138,31 154,36 174,45 174,46 86,46" fill="#F06856" opacity="0.24"/>
          <text x="10" y="33" font-family="Liberation Sans, sans-serif" font-size="8.6" fill="#FFA69E" font-weight="700">MSCI -0.86%</text>
          <text x="10" y="46" font-family="Liberation Sans, sans-serif" font-size="9.6" fill="#F5CC4C" font-weight="700">FX -1.5%</text>
          <polyline points="86,16 106,22 122,19 138,31 154,36 174,45" fill="none" stroke="#FF6B57" stroke-width="3.0"/>
          <circle cx="174" cy="45" r="4.2" fill="#F5CC4C" stroke="#FF6B57" stroke-width="1.6"/>
        """
    else:  # dart_crater
        bg = "#0E1626"
        pill_bg = "#1E2D47"
        pill_border = "#6B92C4"
        art = """
          <circle cx="24" cy="46" r="1.2" fill="#FFFFFF"/>
          <circle cx="164" cy="14" r="1.3" fill="#FFFFFF"/>
          <circle cx="150" cy="46" r="1" fill="#FFFFFF"/>
          <ellipse cx="64" cy="34" rx="26" ry="18" fill="#878076" stroke="#B5AEA4" stroke-width="1.3"/>
          <ellipse cx="72" cy="32" rx="8.5" ry="6.5" fill="#36322D" stroke="#F0C66B" stroke-width="1.7"/>
          <polygon points="78,32 134,21 134,37" fill="#6ED6FF" opacity="0.25"/>
          <rect x="134" y="24" width="13" height="10" fill="#E3EEFF"/>
          <rect x="130" y="14" width="21" height="5" fill="#4692C4"/>
          <rect x="130" y="38" width="21" height="5" fill="#4692C4"/>
        """
    pw = max(46, len(pill) * 5.3 + 10)
    b_attr = f' stroke="{pill_border}" stroke-width="0.9"' if pill_border != "none" else ""
    return f"""
    <svg viewBox="0 0 188 54" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="188" height="54" fill="{bg}"/>
      {art}
      <rect x="5" y="4" width="{pw:.0f}" height="12.5" rx="2" fill="{pill_bg}" fill-opacity="0.92"{b_attr}/>
      <text x="{5 + pw/2:.1f}" y="12.6" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="7.3" fill="#FFFFFF" font-weight="700">{html.escape(pill)}</text>
    </svg>"""


def world_map_svg() -> str:
    """Vector world map with crisp continents, collision-free numbered pins, and GLOBAL/SPACE inset."""
    w, h = 324, 212

    def proj(lon: float, lat: float) -> tuple[float, float]:
        x = (lon + 180.0) / 360.0 * w
        y = (78.0 - lat) / 136.0 * h
        return max(9.0, min(w - 9.0, x)), max(9.0, min(h - 9.0, y))

    # Cleaner, higher-detail original continent coastlines
    continents = [
        # North & Central America
        [(-167, 65), (-155, 71), (-132, 69), (-110, 68), (-94, 62), (-80, 62), (-64, 58), (-55, 51),
         (-64, 44), (-71, 41), (-76, 35), (-81, 25), (-83, 30), (-95, 29), (-97, 22), (-88, 21),
         (-84, 10), (-78, 8), (-85, 11), (-93, 15), (-105, 19), (-110, 24), (-117, 32), (-124, 41),
         (-130, 54), (-148, 60)],
        # Greenland
        [(-53, 60), (-48, 72), (-32, 81), (-18, 76), (-24, 68), (-42, 60)],
        # Cuba / Caribbean hint
        [(-84, 22), (-74, 20), (-76, 22)],
        # South America
        [(-78, 9), (-71, 12), (-61, 10), (-50, 1), (-35, -6), (-39, -18), (-43, -23), (-53, -34),
         (-63, -41), (-68, -55), (-74, -50), (-72, -35), (-71, -18), (-81, -5), (-80, 2)],
        # Continental Europe
        [(-9, 37), (-9, 43), (-2, 43), (-4, 48), (2, 51), (8, 54), (10, 58), (6, 61), (18, 69),
         (30, 70), (42, 66), (48, 54), (40, 47), (34, 45), (28, 41), (22, 37), (18, 40), (13, 45),
         (8, 44), (3, 42), (-5, 36)],
        # Great Britain & Ireland
        [(-6, 50), (-5, 58), (-1, 58), (2, 52), (-1, 50)],
        [(-10, 51.5), (-9.5, 55), (-6, 55), (-6.5, 51.5)],
        # Africa
        [(-17, 15), (-14, 28), (-6, 36), (10, 37), (15, 32), (25, 32), (33, 31), (42, 13), (51, 11),
         (44, 1), (40, -10), (35, -24), (27, -33), (18, -35), (14, -22), (12, -6), (9, 4), (2, 6), (-8, 5)],
        # Madagascar
        [(44, -25), (49, -13), (50, -16), (46, -25)],
        # Asia
        [(27, 41), (36, 42), (46, 45), (53, 52), (65, 68), (95, 74), (135, 72), (170, 66), (160, 55),
         (142, 53), (135, 43), (129, 35), (125, 39), (120, 35), (122, 30), (114, 22), (108, 16),
         (104, 10), (101, 14), (103, 2), (98, 8), (96, 17), (89, 22), (80, 10), (76, 8), (72, 21),
         (66, 25), (56, 26), (50, 29), (58, 22), (44, 13), (35, 29), (35, 36)],
        # Japan
        [(130, 31), (135, 34), (140, 36), (145, 44), (141, 45), (138, 39), (131, 33)],
        # Taiwan & Philippines
        [(120, 22), (122, 25), (121, 25), (120, 23)],
        [(120, 18), (125, 13), (126, 7), (122, 7), (120, 14)],
        # Indonesia
        [(96, 5), (104, -5), (114, -8), (122, -8), (120, -6), (105, -2), (98, 4)],
        [(109, 2), (118, 5), (118, -3), (111, -3)],
        # Papua New Guinea
        [(133, -2), (141, -3), (150, -9), (146, -10), (136, -5)],
        # Australia
        [(114, -22), (123, -16), (131, -12), (136, -12), (143, -11), (153, -27), (150, -37),
         (140, -38), (131, -32), (115, -34)],
        # New Zealand
        [(167, -46), (171, -42), (175, -41), (178, -36), (174, -35), (173, -39), (166, -45)],
    ]

    poly_svg = []
    for pts in continents:
        pstr = " ".join(f"{proj(lon, lat)[0]:.1f},{proj(lon, lat)[1]:.1f}" for lon, lat in pts)
        poly_svg.append(f'<polygon points="{pstr}" fill="#CFC6B6" stroke="#ABA18E" stroke-width="0.65"/>')

    grid = [
        f'<line x1="0" y1="{proj(0, 0)[1]:.1f}" x2="{w}" y2="{proj(0, 0)[1]:.1f}" stroke="#B8CAD8" stroke-width="0.6" stroke-dasharray="3,3"/>',
        f'<line x1="0" y1="{proj(0, 30)[1]:.1f}" x2="{w}" y2="{proj(0, 30)[1]:.1f}" stroke="#C8D7E2" stroke-width="0.5"/>',
        f'<line x1="0" y1="{proj(0, -30)[1]:.1f}" x2="{w}" y2="{proj(0, -30)[1]:.1f}" stroke="#C8D7E2" stroke-width="0.5"/>',
    ]

    # Plot brief dots (excluding inset items)
    brief_dots = []
    for b in BRIEFS:
        if b.get("inset"):
            continue
        x, y = proj(b["lon"], b["lat"])
        col = REGION_COLOR[b["region"]]
        brief_dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.8" fill="{col}" stroke="#FFFFFF" stroke-width="0.85"/>')

    # Carefully resolved coordinates for numbered pins 1-12 so ZERO pins touch or overlap (>=14px apart)
    # Leader lines connect offset pins back to exact geographic location.
    pin_offsets = {
        1: (-2, 11),   # Seoul shifted south-slightly below Korea
        2: (-11, -9),  # Pyongyang shifted north-west cleanly clear of #1
        8: (12, -2),   # Tokyo shifted east in Pacific cleanly clear of #1/#2
        6: (10, 4),    # Brussels shifted east cleanly clear of #11
        11: (-10, -5), # London shifted north-west cleanly clear of #6
        5: (-4, -6),   # Gaza shifted slightly NW
        3: (6, 5),     # Riyadh shifted slightly SE
    }

    placed_pins = []
    pins_svg = []
    for s in HEROES + SECONDARY:
        if s.get("inset"):
            continue
        tx, ty = proj(s["lon"], s["lat"])
        dx, dy = pin_offsets.get(s["id"], (0, 0))
        px, py = max(9.0, min(w - 9.0, tx + dx)), max(9.0, min(h - 9.0, ty + dy))
        col = REGION_COLOR[s["region"]]
        # Check minimum pairwise distance against previously placed pins
        for oid, ox, oy in placed_pins:
            dist = math.hypot(px - ox, py - oy)
            assert dist >= 13.0, f"Map pins {s['id']} and {oid} too close: {dist:.1f}px"
        placed_pins.append((s["id"], px, py))
        if abs(dx) + abs(dy) > 3:
            pins_svg.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="{col}" stroke-width="1.1"/>')
            pins_svg.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="1.8" fill="{col}"/>')
        pins_svg.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6.8" fill="{col}" stroke="#FFFFFF" stroke-width="1.2"/>'
            f'<text x="{px:.1f}" y="{py+2.6:.1f}" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="7.6" fill="#FFFFFF" font-weight="700">{s["id"]}</text>'
        )

    # Dedicated framed GLOBAL & SPACE inset box in bottom-left Pacific corner
    gcol = REGION_COLOR["Global & Space"]
    inset_svg = f"""
      <rect x="6" y="164" width="92" height="42" rx="3" fill="#141E2E" fill-opacity="0.93" stroke="#6F86A3" stroke-width="1"/>
      <text x="52" y="175" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="7.0" fill="#DCE8FA" font-weight="700">GLOBAL &amp; SPACE</text>
      <circle cx="23" cy="192" r="6.8" fill="{gcol}" stroke="#FFFFFF" stroke-width="1.2"/>
      <text x="23" y="194.6" text-anchor="middle" font-family="Liberation Sans, sans-serif" font-size="7.5" fill="#FFFFFF" font-weight="700">13</text>
      <text x="34" y="190" font-family="Liberation Sans, sans-serif" font-size="6.8" fill="#FFFFFF" font-weight="700">DART Crater</text>
      <circle cx="37" cy="199" r="2.6" fill="#9AA6B2" stroke="#FFFFFF" stroke-width="0.75"/>
      <text x="43" y="201.3" font-family="Liberation Sans, sans-serif" font-size="6.6" fill="#C7D4E5">#45 CBAM</text>
    """

    return f"""
    <svg viewBox="0 0 {w} {h}" width="100%" height="{h}" xmlns="http://www.w3.org/2000/svg" style="display:block;border:1px solid #B8B0A0;border-radius:2px;">
      <rect width="{w}" height="{h}" fill="#D6E3EE"/>
      {''.join(grid)}
      {''.join(poly_svg)}
      {''.join(brief_dots)}
      {''.join(pins_svg)}
      {inset_svg}
    </svg>"""


def build_html() -> str:
    reg_counts = Counter(s["region"] for s in ALL_STORIES)
    field_counts = Counter(s["field"] for s in ALL_STORIES)
    total = len(ALL_STORIES)
    assert sum(reg_counts.values()) == total
    assert sum(field_counts.values()) == total

    # 9-Region proportional ribbon with safe min-width so NO segment ever clips
    ribbon_segs = []
    for full, short, col in REGIONS:
        cnt = reg_counts[full]
        min_w = 56 if cnt <= 2 else (68 if cnt == 3 else 74)
        ribbon_segs.append(
            f'<div class="reg-seg" style="flex:{cnt} 1 {min_w}px;min-width:{min_w}px;background:{col};">{html.escape(short)} ({cnt})</div>'
        )

    sorted_fields = sorted(field_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    fields_str = " · ".join(f"<b>{html.escape(k)}</b> {v}" for k, v in sorted_fields)
    n_fields = len(sorted_fields)

    hero_cards = []
    for h in HEROES:
        col = REGION_COLOR[h["region"]]
        cert_cls = "cert-off" if h["certainty"] == "OFFICIAL" else "cert-rep"
        hero_cards.append(f"""
        <article class="hero-card" style="border-top:3px solid {col};">
          <div class="hero-art">{hero_svg(h['scene'])}</div>
          <div class="hero-body">
            <div class="meta-row">
              <span class="num-dot" style="background:{col};">{h['id']}</span>
              <span class="eyebrow" style="color:{col};">{html.escape(h['location'])} · {html.escape(h['field'].upper())}</span>
              <span class="cert {cert_cls}">{html.escape(h['certainty'])}</span>
            </div>
            <h2 class="hero-hl">{html.escape(h['headline'])}</h2>
            <p class="hero-sum">{html.escape(h['summary'])}</p>
            <div class="why-row"><span class="why-tag">WHY IT MATTERS</span> {html.escape(h['why'])}</div>
          </div>
        </article>""")

    sec_cards = []
    for s in SECONDARY:
        col = REGION_COLOR[s["region"]]
        sec_cards.append(f"""
        <article class="sec-card" style="border-top:2.5px solid {col};">
          <div class="sec-art">{secondary_svg(s['scene'], s['pill'])}</div>
          <div class="sec-body">
            <div class="sec-meta">
              <span class="num-dot sm" style="background:{col};">{s['id']}</span>
              <span class="sec-eye" style="color:{col};">{html.escape(s['location'])} · {html.escape(s['field'].upper())}</span>
            </div>
            <h3 class="sec-hl">{html.escape(s['headline'])}</h3>
            <p class="sec-sum">{html.escape(s['summary'])}</p>
          </div>
        </article>""")

    legend_items = []
    for full, short, col in REGIONS:
        legend_items.append(
            f'<div class="leg-it"><span class="leg-sw" style="background:{col};"></span>{html.escape(short)} ({reg_counts[full]})</div>'
        )

    def render_brief_col(subset):
        rows = []
        for b in subset:
            col = REGION_COLOR[b["region"]]
            cl = ' <span class="claim-pill">CLAIM</span>' if b.get("claim") else ""
            rows.append(
                f'<div class="brief-row">'
                f'<span class="num-dot xs" style="background:{col};">{b["id"]}</span>'
                f'<span class="brief-txt"><b style="color:{col};">{html.escape(b["loc"])}</b> {html.escape(b["text"])}{cl}</span>'
                f'</div>'
            )
        return "\n".join(rows)

    col1_html = render_brief_col(BRIEFS[:16])
    col2_html = render_brief_col(BRIEFS[16:])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Thursday 26 November 2026 — The World in One Day</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: 1024px; height: 1024px; overflow: hidden;
    background: #F7F3E8; color: #161616;
    font-family: "Liberation Sans", "DejaVu Sans", sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .page {{
    width: 1024px; height: 1024px;
    display: flex; flex-direction: column;
    overflow: hidden;
  }}

  /* 1. Top Navy Strap (23px) */
  .top-bar {{
    height: 23px; flex-shrink: 0; background: #16233B; color: #F7F3E8;
    padding: 0 16px; display: flex; align-items: center; justify-content: space-between;
    font-size: 9.2px; font-weight: 700; letter-spacing: 0.5px;
  }}
  .brand {{ color: #F5CC4C; letter-spacing: 1.3px; font-size: 10.2px; }}

  /* 2. Masthead + Deck (62px) */
  .masthead {{
    height: 62px; flex-shrink: 0; padding: 3px 16px 2px; text-align: center;
    border-bottom: 1.5px solid #1E2430;
    display: flex; flex-direction: column; justify-content: center;
  }}
  .masthead h1 {{
    font-family: "Liberation Serif", "DejaVu Serif", Georgia, serif;
    font-size: 39px; font-weight: 700; line-height: 1.02; letter-spacing: -0.6px;
    color: #11141B;
  }}
  .deck {{
    font-family: "Liberation Serif", Georgia, serif;
    font-style: italic; font-weight: 700; font-size: 11.2px; color: #9E2A2B;
    margin-top: 2px; white-space: nowrap; overflow: hidden;
  }}

  /* 3. Taxonomy Ribbons (34px) */
  .tax-wrap {{ flex-shrink: 0; padding: 3.5px 16px 3px; border-bottom: 1px solid #C8C0B0; }}
  .reg-ribbon {{ display: flex; width: 100%; height: 17px; border-radius: 2px; overflow: hidden; }}
  .reg-seg {{
    color: #FFFFFF; font-size: 7.9px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    white-space: nowrap; overflow: hidden; padding: 0 3px;
    border-right: 1px solid rgba(255,255,255,0.32);
  }}
  .reg-seg:last-child {{ border-right: none; }}
  .fields-bar {{
    margin-top: 2.5px; font-size: 7.95px; color: #363C46; text-align: center;
    line-height: 1.15; white-space: nowrap; overflow: hidden;
  }}
  .fields-bar b {{ color: #12151C; }}

  /* 4. Day-in-Numbers KPI Strip (46px) */
  .kpi-strip {{
    height: 46px; flex-shrink: 0; margin: 0 16px;
    display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px;
    border-bottom: 1.5px solid #1E2430; align-items: center;
  }}
  .kpi {{ text-align: center; border-right: 1px solid #D3CBB8; padding: 0 4px; }}
  .kpi:last-child {{ border-right: none; }}
  .kpi-val {{
    font-family: "Liberation Serif", Georgia, serif;
    font-size: 22.5px; font-weight: 700; line-height: 1.0; color: #12151C;
  }}
  .kpi-val.red {{ color: #A62627; }}
  .kpi-cap {{
    font-size: 8.3px; font-weight: 700; color: #3A404A; line-height: 1.12; margin-top: 1.5px;
    white-space: nowrap;
  }}

  /* 5. Tier 1: Three Hero Cards (218px) */
  .hero-grid {{
    height: 218px; flex-shrink: 0; margin: 5px 16px 0;
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
  }}
  .hero-card {{
    background: #FFFDF8; border: 1px solid #D3CCBC; border-radius: 2px;
    display: flex; flex-direction: column; overflow: hidden;
  }}
  .hero-art {{ height: 92px; width: 100%; border-bottom: 1px solid #DDD6C7; flex-shrink: 0; }}
  .hero-body {{ padding: 4.5px 8px 4px; display: flex; flex-direction: column; flex: 1; }}
  .meta-row {{ display: flex; align-items: center; gap: 4px; margin-bottom: 2px; }}
  .num-dot {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 14.5px; height: 14.5px; border-radius: 50%;
    color: #FFFFFF; font-size: 8.3px; font-weight: 700; flex-shrink: 0;
  }}
  .num-dot.sm {{ width: 12.5px; height: 12.5px; font-size: 7.3px; }}
  .num-dot.xs {{ width: 12.5px; height: 12.5px; font-size: 7.0px; flex-shrink: 0; }}
  .eyebrow {{ font-size: 8.0px; font-weight: 700; letter-spacing: 0.3px; flex: 1; white-space: nowrap; overflow: hidden; }}
  .cert {{ font-size: 6.7px; font-weight: 700; padding: 0.5px 4px; border-radius: 2px; letter-spacing: 0.25px; }}
  .cert-off {{ border: 1px solid #235380; color: #235380; background: #EEF4FA; }}
  .cert-rep {{ border: 1px solid #196658; color: #196658; background: #ECF7F4; }}
  .hero-hl {{
    font-family: "Liberation Serif", Georgia, serif;
    font-size: 13.4px; font-weight: 700; line-height: 1.13; color: #111419; margin-bottom: 2.5px;
  }}
  .hero-sum {{ font-size: 9.1px; line-height: 1.2; color: #2B3039; flex: 1; }}
  .why-row {{
    margin-top: 2px; padding-top: 2.5px; border-top: 1px dashed #D6CFC0;
    font-size: 8.3px; line-height: 1.15; color: #1A1F26; font-weight: 700;
  }}
  .why-tag {{ color: #9E2A2B; font-size: 7.4px; letter-spacing: 0.3px; margin-right: 2px; }}

  /* 6. Tier 2: 2x5 Secondary Cards (240px) */
  .sec-grid {{
    height: 240px; flex-shrink: 0; margin: 5px 16px 0;
    display: grid; grid-template-columns: repeat(5, 1fr); grid-template-rows: repeat(2, 1fr);
    gap: 6px 8px;
  }}
  .sec-card {{
    background: #FFFDF8; border: 1px solid #D3CCBC; border-radius: 2px;
    display: flex; flex-direction: column; overflow: hidden;
  }}
  .sec-art {{ height: 50px; width: 100%; border-bottom: 1px solid #DDD6C7; flex-shrink: 0; }}
  .sec-body {{ padding: 3px 5.5px 3px; display: flex; flex-direction: column; flex: 1; }}
  .sec-meta {{ display: flex; align-items: center; gap: 3px; margin-bottom: 1.5px; }}
  .sec-eye {{ font-size: 7.0px; font-weight: 700; letter-spacing: 0.2px; white-space: nowrap; overflow: hidden; }}
  .sec-hl {{
    font-family: "Liberation Serif", Georgia, serif;
    font-size: 10.1px; font-weight: 700; line-height: 1.12; color: #111419; margin-bottom: 2px;
  }}
  .sec-sum {{ font-size: 7.9px; line-height: 1.16; color: #333942; }}

  /* 7. Tier 3: Map + 32 Briefs (fills exact remaining flex height above footer!) */
  .tier3 {{
    flex: 1; min-height: 0; margin: 6px 16px 0; padding-top: 5px;
    border-top: 1.5px solid #1E2430;
    display: grid; grid-template-columns: 324px 1fr; gap: 10px;
    overflow: hidden;
  }}
  .sec-label {{
    font-size: 8.6px; font-weight: 700; letter-spacing: 0.55px; color: #16233B;
    margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;
    flex-shrink: 0;
  }}
  .sec-label span {{ font-weight: 400; color: #545C66; letter-spacing: 0; font-size: 7.6px; }}
  .map-panel {{ display: flex; flex-direction: column; min-height: 0; }}
  .map-legend {{
    margin-top: 5px; padding: 5px 7px; background: #FFFDF8; border: 1px solid #D3CCBC; border-radius: 2px;
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 3.5px 6px;
  }}
  .leg-it {{ display: flex; align-items: center; gap: 4px; font-size: 7.8px; font-weight: 700; color: #262C34; white-space: nowrap; }}
  .leg-sw {{ width: 7.5px; height: 7.5px; border-radius: 50%; flex-shrink: 0; }}
  .map-note {{ margin-top: 4px; font-size: 7.5px; color: #4A515B; line-height: 1.2; }}

  .briefs-panel {{ display: flex; flex-direction: column; min-height: 0; }}
  .briefs-cols {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px; flex: 1; min-height: 0;
  }}
  .brief-col {{
    display: flex; flex-direction: column; justify-content: space-between; min-height: 0;
  }}
  .brief-row {{
    display: flex; align-items: center; gap: 4px; height: 17.5px;
    border-bottom: 0.6px solid #E2DBC9; overflow: hidden;
  }}
  .brief-row:last-child {{ border-bottom: none; }}
  .brief-txt {{
    font-family: "Liberation Sans Narrow", "Liberation Sans", sans-serif;
    font-size: 8.9px; line-height: 1.1; color: #1E232A;
    white-space: nowrap; overflow: hidden;
  }}
  .brief-txt b {{ font-weight: 700; }}
  .claim-pill {{
    display: inline-block; font-size: 6.3px; font-weight: 700; color: #9E2A2B;
    border: 1px solid #9E2A2B; background: #FDF0F0; padding: 0 2.5px; border-radius: 2px;
    vertical-align: middle; margin-left: 2px;
  }}

  /* 8. Refined Broadsheet Audit Footer (45px) */
  .footer {{
    height: 45px; flex-shrink: 0; margin: 6px 16px 8px; padding: 4px 8px;
    background: #EFEADF; border-top: 1.5px solid #1E2430; border-bottom: 1px solid #B8B0A0;
    border-left: 1px solid #D3CCBC; border-right: 1px solid #D3CCBC; border-radius: 2px;
    display: flex; flex-direction: column; justify-content: center; gap: 2.5px;
  }}
  .foot-row {{ font-size: 7.8px; line-height: 1.2; color: #222830; white-space: nowrap; overflow: hidden; }}
  .dc-badge {{
    display: inline-block; background: #9E2A2B; color: #FFFFFF; font-weight: 700;
    font-size: 7.1px; padding: 1px 5px; border-radius: 2px; letter-spacing: 0.35px; margin-right: 4px;
  }}
  .hs-badge {{
    display: inline-block; background: #16233B; color: #FFFFFF; font-weight: 700;
    font-size: 6.9px; padding: 0.5px 4.5px; border-radius: 2px; letter-spacing: 0.3px; margin-right: 4px;
  }}
</style>
</head>
<body>
<div class="page">
  <header class="top-bar">
    <span class="brand">THE WORLD IN ONE DAY</span>
    <span>{total} DATED STORIES · {len(REGIONS)} REGIONS · {n_fields} FIELDS · ALL FIRST REPORTED ON THURSDAY 26 NOVEMBER 2026</span>
  </header>

  <section class="masthead">
    <h1>Thursday 26 November 2026</h1>
    <div class="deck">Bank of Korea hikes rate to 3.25% &amp; lifts GDP view · Kim orders wider tactical nuclear rollout · Saudi defenses intercept 2 missiles over Riyadh</div>
  </section>

  <section class="tax-wrap">
    <div class="reg-ribbon">{''.join(ribbon_segs)}</div>
    <div class="fields-bar">{fields_str}</div>
  </section>

  <section class="kpi-strip">
    <div class="kpi"><div class="kpi-val" style="color:#196658;">3.25%</div><div class="kpi-cap">BOK RATE · 3RD HIKE (#1)</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#196658;">$50B</div><div class="kpi-cap">CHINA–INDONESIA PACT (#7)</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#9E2A2B;">100th</div><div class="kpi-cap">MACY'S PARADE MOVED (#4)</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#B3501A;">2</div><div class="kpi-cap">MISSILES DOWNED · RIYADH (#3)</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#3E6B8C;">4.9%</div><div class="kpi-cap">AUSTRALIA CPI · 3-YR HIGH (#10)</div></div>
  </section>

  <section class="hero-grid">
    {''.join(hero_cards)}
  </section>

  <section class="sec-grid">
    {''.join(sec_cards)}
  </section>

  <section class="tier3">
    <div class="map-panel">
      <div class="sec-label">WHERE IT HAPPENED <span>Pins 1–13 = scenes · Dots = briefs 14–45</span></div>
      {world_map_svg()}
      <div class="map-legend">{''.join(legend_items)}</div>
      <div class="map-note">Region colors link ribbon, cards, map pins and all 32 briefs.</div>
    </div>
    <div class="briefs-panel">
      <div class="sec-label">ALSO ON THURSDAY 26 NOVEMBER <span>32 more dated briefs across all 9 regions</span></div>
      <div class="briefs-cols">
        <div class="brief-col">{col1_html}</div>
        <div class="brief-col">{col2_html}</div>
      </div>
    </div>
  </section>

  <footer class="footer">
    <div class="foot-row">
      <span class="dc-badge">DATE CHECK</span>
      <b>All 45 items occurred or broke Thu 26 Nov 2026.</b> Excluded (Wed 25): US 14-economy tariffs · Kospi −6.2% rout · Shenzhou-24 docking · AU Duty of Care vote · Cairo tanker crash.
    </div>
    <div class="foot-row">
      <span class="hs-badge">HOW SURE</span>
      <b>OFFICIAL</b> authority act/data · <b>REPORTED</b> wire report · <b>CLAIM</b> single-side/alleged ·
      <b>Sources:</b> Yonhap, Reuters, AP, AFP, BBC, Guardian, Al Jazeera, Al Arabiya, Nikkei, SCMP, CNA, ST, SBS, RNZ, ESPN, GMT Eight, EU Council, ESA · Original art.
    </div>
  </footer>
</div>
</body>
</html>"""


def render() -> None:
    html_text = build_html()

    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", encoding="utf-8", delete=False) as hf:
        hf.write(html_text)
        html_path = pathlib.Path(hf.name)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        raw_png = pathlib.Path(tf.name)

    try:
        cmd = [
            "/usr/bin/google-chrome",
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--window-size=1024,1024",
            f"--screenshot={raw_png}",
            f"file://{html_path}",
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        im = Image.open(raw_png).convert("RGB")
        if im.size != (1024, 1024):
            im = im.crop((0, 0, 1024, 1024))
        out_png = REPO / "entry.png"
        im.save(out_png, format="PNG", optimize=True)
        size = out_png.stat().st_size
        print(f"Rendered {out_png}: {im.size[0]}x{im.size[1]}, {size:,} bytes ({size/1024:.1f} KiB)")
        assert size <= 1048576, f"Image too large: {size}"
    finally:
        if html_path.exists():
            html_path.unlink()
        if raw_png.exists():
            raw_png.unlink()


if __name__ == "__main__":
    render()
