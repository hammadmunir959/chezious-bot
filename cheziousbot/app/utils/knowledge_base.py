"""
app/utils/knowledge_base.py
"""

import difflib
from typing import Any, Dict, List, Optional, Union

# ── Data ──────────────────────────────────────────────────────────────────────

MENU: Dict[str, List[Dict]] = {
    "pizzas": [
        {"name": "Tikka Pizza",        "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Tikka pizza."},
        {"name": "Fajita Pizza",       "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Fajita pizza."},
        {"name": "Lover Pizza",        "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Lover pizza."},
        {"name": "Tandoori Pizza",     "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Tandoori pizza."},
        {"name": "Spicy Pizza",        "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Spicy pizza."},
        {"name": "Veg Pizza",          "sizes": {"Small": 690, "Regular": 1250, "Large": 1650, "Party": 2700}, "description": "Local flavor: Veg pizza."},
        {"name": "Supreme Pizza",      "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Supreme pizza."},
        {"name": "Black Pepper Pizza", "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Black Pepper pizza."},
        {"name": "Sausage Pizza",      "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Sausage pizza."},
        {"name": "Cheese Pizza",       "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Cheese pizza."},
        {"name": "Pepperoni Pizza",    "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Pepperoni pizza."},
        {"name": "Mushroom Pizza",     "sizes": {"Small": 690, "Regular": 1350, "Large": 1750, "Party": 2850}, "description": "Sooper flavor: Mushroom pizza."},
        {"name": "Special Pizza",      "sizes": {"Small": 790, "Regular": 1550, "Large": 2050, "Party": 3200}, "description": "Cheezy Treat: Special pizza."},
        {"name": "Behari Pizza",       "sizes": {"Small": 790, "Regular": 1550, "Large": 2050, "Party": 3200}, "description": "Cheezy Treat: Behari pizza."},
        {"name": "Extreme Pizza",      "sizes": {"Small": 790, "Regular": 1550, "Large": 2050, "Party": 3200}, "description": "Cheezy Treat: Extreme pizza."},
        {"name": "Malai Crust",        "price": 1200, "description": "Crust upgrade for Regular/Large."},
        {"name": "Stuffed Crust",      "price": 1450, "description": "Crust upgrade for Regular/Large."},
        {"name": "Crown Crust",        "price": 1550, "description": "Crust upgrade for Regular/Large."},
        {"name": "Thin Crust",         "price": 1550, "description": "Crust upgrade for Regular/Large."},
    ],
    "burgers": [
        {"name": "Reggy Burger",    "price": 390,  "description": "Regular burger."},
        {"name": "Bazinga Burger",  "price": 560,  "description": "Bazinga burger."},
        {"name": "Bazooka Burger",  "price": 630,  "description": "Bazooka burger."},
        {"name": "Supreme Burger",  "price": 730,  "description": "Supreme burger."},
        {"name": "Mexican Sandwich","price": 600,  "description": "Mexican sandwich."},
        {"name": "Euro Sandwich",   "price": 920,  "description": "Euro sandwich."},
        {"name": "Pizza Stacker",   "price": 920,  "description": "Pizza stacker."},
    ],
    "sides": [
        {"name": "Baked Wings (6pc)",  "price": 600,  "description": "Baked chicken wings."},
        {"name": "Flaming Wings (6pc)","price": 650,  "description": "Flaming chicken wings."},
        {"name": "Sticks",             "price": 630,  "description": "Chicken sticks."},
        {"name": "Calzone",            "price": 1150, "description": "Cheezy calzone."},
        {"name": "Rolls",              "price": 690,  "description": "Rolls."},
        {"name": "Nuggets (5pc)",      "price": 450,  "description": "Chicken nuggets."},
        {"name": "Fries",              "price": 220,  "description": "Regular fries."},
    ],
    "pastas": [
        {"name": "Alfredo Pasta", "price": 1050, "description": "Alfredo pasta."},
        {"name": "Crunchy Pasta", "price": 950,  "description": "Crunchy pasta."},
    ],
}

LOCATIONS: Dict[str, List[str]] = {
    "lahore":     ["Shahdrah", "Valencia Town", "Iqbal Town", "Faisal Town", "Gulberg", "DHA (Defence Housing Authority)", "Johar Town"],
    "islamabad":  ["F-10 Sector", "F-7 Sector", "E-11 Sector", "G-13 Sector", "I-8 Sector", "Bahria Town Islamabad", "DHA Islamabad"],
    "rawalpindi": ["Saddar", "Commercial Market", "Chandni Chowk", "Bahria Town Rawalpindi"],
    "other":      ["Peshawar (PEW)", "Kasur (KSR)", "Sahiwal (SWL)", "Okara (OKR)"],
}

POLICIES: Dict[str, str] = {
    "delivery":           "Delivery takes ~30-45 mins and is Free.",
    "returns_and_refunds":"If the food is cold or incorrect, please complain within 30 minutes of delivery for a replacement or a full refund.",
    "hours":              "Mon-Thu: 11AM-3AM | Fri: 2PM-3AM | Sat-Sun: 11AM-3AM",
    "contact":            "UAN: 111-44-66-99 | Web: cheezious.com",
}

ESSENTIAL_INFO: Dict[str, Any] = {
    "hours": POLICIES["hours"],
    "contact": POLICIES["contact"],
    "delivery": POLICIES["delivery"],
    "locations": {
        "cities": list(LOCATIONS.keys()),
        "summary": "We have multiple branches in Lahore, Islamabad, and Rawalpindi."
    },
    "menu_categories": list(MENU.keys()),
    "menu_info": "We serve different types of Pizzas, Burgers, Sides, and Pastas. Ask me for the menu to see all items."
}

# ── Search ────────────────────────────────────────────────────────────────────

_KB = {"menu": MENU, "locations": LOCATIONS, "policies": POLICIES}

def get_all_items() -> Dict[str, Union[int, Dict[str, int]]]:
    """Flatten the menu into a single dict mapping item names to prices or size dicts."""
    flat: Dict[str, Union[int, Dict[str, int]]] = {}
    for category, items in MENU.items():
        for item in items:
            if isinstance(item, dict) and "name" in item:
                name = item["name"]
                if "price" in item:
                    flat[name] = item["price"]
                elif "sizes" in item:
                    flat[name] = item["sizes"]
    return flat

def get_menu_by_category() -> Dict[str, List[Dict]]:
    """Return the menu grouped by category."""
    return MENU

def search(category: Optional[str] = None, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Search the knowledge base and ALWAYS return ESSENTIAL_INFO.
    Returns: {"results": Any, "essential_info": Dict}
    """
    # Canonicalize category
    category = category.lower() if category else None
    
    # Robustness: If query is just the category name or 'all', treat as None
    if query and query.lower() in ["menu", "locations", "policies", "branches", "all", "everything"]:
        query = None

    results = None
    
    # If both are None, results stay None (ESSENTIAL_INFO is returned anyway)
    if category or query:
        # If category is specified, search within that category; otherwise search across all
        sources = {category: _KB[category]} if category and category in _KB else dict(_KB)
        
        if not query:
            results = next(iter(sources.values())) if len(sources) == 1 else sources
        else:
            # Normalize query and search
            q = query.lower().replace("-", " ").strip()
            txt = lambda v: ((" ".join(txt(x) for x in v.values()) if isinstance(v, dict) else " ".join(txt(x) for x in v)) if isinstance(v, (dict, list)) else str(v).lower().replace("-", " "))
            name = lambda i: (i.get("name", "") if isinstance(i, dict) else str(i)).lower().replace("-", " ")
            fuzzy = lambda a, b: difflib.SequenceMatcher(None, a, b).ratio() > 0.6

            search_hits = {}
            for src, data in sources.items():
                for subcat, items in (data.items() if isinstance(data, dict) else {src: data}.items()):
                    if isinstance(items, list):
                        matched = (
                            items if (subcat == q or subcat.startswith(q)) else
                            [i for i in items if name(i) == q or name(i).startswith(q)] or
                            [i for i in items if q in txt(i)] or
                            [i for i in items if fuzzy(q, name(i))]
                        )
                        if matched:
                            search_hits.setdefault(src, {})[subcat] = matched
                    elif isinstance(items, str) and (q in subcat or q in items.lower()):
                        search_hits.setdefault(src, {})[subcat] = items

            if search_hits:
                flat = {k: (next(iter(v.values())) if len(v) == 1 else v) for k, v in search_hits.items()}
                results = next(iter(flat.values())) if len(flat) == 1 else flat

    return {
        "results": results,
        "essential_info": ESSENTIAL_INFO
    }

