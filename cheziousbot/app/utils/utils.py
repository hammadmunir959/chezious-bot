"""
utils.py — Helpers for order validation, cart management, and prompt building.
"""

from __future__ import annotations

import difflib
import logging
from functools import lru_cache

from app.schemas.agent import MenuItem
from .knowledge_base import get_all_items

logger = logging.getLogger(__name__)

VALID_PAYMENT_METHODS = {"cash", "card", "online"}

_CRUST_UPGRADES = {"malai crust", "stuffed crust", "crown crust", "thin crust"}


_CITY_ALIASES: dict[str, str] = {
    "lhr": "lahore",
    "isb": "islamabad",
    "rwp": "rawalpindi",
    "pesh": "peshawar",
    "ksr": "kasur",
    "swl": "sahiwal",
    "okr": "okara",
}


def _cart_txt(cart_items: list) -> str:
    parts = []
    for i in cart_items:
        desc = f"{i.quantity}x {i.item}"
        if i.size and i.size.strip().lower() != "no size":
            desc += f" ({i.size})"
        parts.append(desc)
    return ", ".join(parts) or "Empty"


def _resolve_items(raw_items: list[MenuItem], price_map: dict, size_based: set) -> tuple[list[MenuItem], list[str]]:
    """Pre-validate LLM-extracted items against live menu. Returns (resolved, warnings)."""
    resolved: list[MenuItem] = []
    warnings: list[str] = []
    all_keys = list(price_map.keys())

    for mi in raw_items:
        name = (mi.item or "").strip().lower()
        sz   = (mi.size or "").strip().lower()
        if sz in ("no size", "none", "null", ""):
            sz = None
            
        if not name:
            continue

        found_sz = None
        for s in ["small", "regular", "large", "party"]:
            if s in name:
                found_sz = s
                # Strip the size from the name
                name = name.replace(f"({s})", "").replace(s, "").replace("()", "").strip()
                break
        
        if found_sz and not sz:
            sz = found_sz

        if name in _CRUST_UPGRADES:
            warnings.append(
                f"'{mi.item}' is a crust upgrade add-on, not a standalone item. "
                "To add a crust upgrade, please order a pizza first and mention the crust type."
            )
            continue

        # Strip common suffixes for cleaner base name matching
        stripped = name
        for suffix in [" pizza", " burger", " sandwich", " pasta"]:
            if name.endswith(suffix):
                stripped = name[: -len(suffix)].strip()
                break

        # Check if base item is size-based (pizzas etc)
        base = name if (name in size_based) else (stripped if stripped in size_based else None)

        if base:
            # If size is provided, try exact match or fuzzy match valid sizes
            if sz:
                key = f"{base} {sz}"
                if key in price_map:
                    resolved.append(MenuItem(item=base.title(), size=sz.title(), quantity=mi.quantity, price=price_map[key]))
                    continue
                # Try fuzzy matching the size if it's slightly off
                valid_sizes = [k[len(base):].strip() for k in price_map if k.startswith(base + " ")]
                close = difflib.get_close_matches(sz, valid_sizes, n=1, cutoff=0.5)
                if close:
                    corrected_key = f"{base} {close[0]}"
                    warnings.append(f"Size '{sz}' for '{base.title()}' corrected to '{close[0].title()}'.")
                    resolved.append(MenuItem(item=base.title(), size=close[0].title(), quantity=mi.quantity, price=price_map[corrected_key]))
                else:
                    # No size match, keep it as size=None for validation_node to handle
                    resolved.append(MenuItem(item=base.title(), size=None, quantity=mi.quantity, price=0))
            else:
                # No size provided but it's a size-based item
                resolved.append(MenuItem(item=base.title(), size=None, quantity=mi.quantity, price=0))
            continue

        # Flat-price lookup
        found = False
        # 1. Exact or suffixed match
        for lookup in [name, stripped]:
            if lookup in price_map:
                resolved.append(MenuItem(item=lookup.title(), size=None, quantity=mi.quantity, price=price_map[lookup]))
                found = True
                break
        
        # 2. Substring match or Portional recomposition (handles 'baked wings' -> 'Baked Wings (6pc)' or splitting)
        if not found:
            for k, p in price_map.items():
                # Check if name matches base, and sz matches content in parentheses OR name matches base with portion stripped
                base_in_menu = k.split(" (")[0]
                portion_in_menu = k.split("(")[1].split(")")[0] if "(" in k and ")" in k else None
                
                # Match 1: name matches base, sz is None or matches portion
                if (name == base_in_menu or stripped == base_in_menu):
                    if not sz or (portion_in_menu and sz == portion_in_menu.lower()):
                        resolved.append(MenuItem(item=k.title(), size=None, quantity=mi.quantity, price=p))
                        found = True
                        break

        if not found:
            # Fuzzy match the item name since it wasn't a direct hit
            search_key = f"{name} {sz}".strip() if sz else name
            close = difflib.get_close_matches(search_key, all_keys, n=3, cutoff=0.5)
            if close:
                alts = ", ".join(c.title() for c in close)
                warnings.append(f"'{mi.item}' is not on our menu. Did you mean one of these? {alts}")
            else:
                warnings.append(f"'{mi.item}' is not on our menu and has been removed.")

    return resolved, warnings


# ---------------------------------------------------------------------------
# Price map
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def build_price_map() -> tuple[dict[str, int], set[str]]:
    """Return (price_map, size_based_keys) from the live menu KB."""
    flat_menu = get_all_items()
    price_map: dict[str, int] = {}
    size_based: set[str] = set()

    for name, value in flat_menu.items():
        name_lower = name.strip().lower()
        if name_lower in _CRUST_UPGRADES:
            continue

        aliases = [name_lower]
        for suffix in [" pizza", " burger", " sandwich", " pasta"]:
            if name_lower.endswith(suffix):
                aliases.append(name_lower[: -len(suffix)].strip())

        if isinstance(value, int):
            for alias in aliases:
                price_map[alias] = value
        elif isinstance(value, dict):
            for alias in aliases:
                size_based.add(alias)
                for size, price in value.items():
                    key = f"{alias} {size.strip().lower()}"
                    try:
                        price_map[key] = int(price)
                    except (TypeError, ValueError):
                        continue

    return price_map, size_based


# ---------------------------------------------------------------------------
# Cart validation & merging
# ---------------------------------------------------------------------------

def merge_items(items: list[MenuItem]) -> list[MenuItem]:
    """Merge duplicate items (case-insensitive name + size match)."""
    merged: dict[tuple[str, str], MenuItem] = {}
    for mi in items:
        if not mi.item:
            continue
        name = mi.item.strip().lower()
        sz   = (getattr(mi, "size", None) or "").strip().lower()
        key  = (name, sz)
        if key in merged:
            merged[key].quantity += mi.quantity
        else:
            merged[key] = MenuItem(
                item=mi.item.strip().title(),
                size=mi.size.strip().title() if getattr(mi, "size", None) else None,
                quantity=mi.quantity,
                price=getattr(mi, "price", 0),
            )
    return list(merged.values())


def validate_cart(
    order_items: list[MenuItem],
    price_map: dict[str, int],
    size_based: set[str],
) -> tuple[list[str], list[MenuItem]]:
    """Validate cart items against the KB price map."""
    errors: list[str] = []
    valid_items: list[MenuItem] = []

    # Issue #3 fix: catch empty cart early
    if not order_items:
        return ["Your cart is empty. Please tell me what you'd like to order."], []

    for mi in order_items:
        item_name = (mi.item or "").strip()
        if not item_name:
            errors.append("One or more cart items has an empty name.")
            continue

        if mi.quantity < 1:
            errors.append(f"'{item_name}': quantity must be at least 1.")
            continue

        if item_name.lower() in _CRUST_UPGRADES:
            errors.append(
                f"'{item_name}' is a crust upgrade add-on, not a standalone item. "
                "Please order a pizza and specify the crust type."
            )
            continue

        sz = (getattr(mi, "size", None) or "").strip().lower()
        if sz in ("null", "none"):
            sz = ""

        lookup          = item_name.lower().replace("  ", " ")
        combined_lookup = f"{lookup} {sz}".strip()
        kb_price        = price_map.get(combined_lookup)

        if kb_price is None:
            if lookup in size_based:
                all_sizes = sorted({
                    k[len(lookup):].strip().title()
                    for k in price_map if k.startswith(lookup + " ")
                })
                errors.append(f"'{item_name}' requires a size. Available: {', '.join(all_sizes)}.")
                continue

            stripped = lookup
            for suffix in [" pizza", " burger", " sandwich", " pasta"]:
                if lookup.endswith(suffix):
                    stripped = lookup[: -len(suffix)].strip()
                    break

            stripped_combined = f"{stripped} {sz}".strip()
            if stripped_combined != combined_lookup and stripped_combined in price_map:
                kb_price        = price_map[stripped_combined]
                lookup          = stripped
                combined_lookup = stripped_combined
            elif stripped in size_based:
                all_sizes = sorted({
                    k[len(stripped):].strip().title()
                    for k in price_map if k.startswith(stripped + " ")
                })
                errors.append(f"'{item_name}' requires a size. Available: {', '.join(all_sizes)}.")
                continue

        if kb_price is None:
            search_str    = f"{lookup} {sz}".strip() if sz else lookup
            close_matches = difflib.get_close_matches(search_str, price_map.keys(), n=2, cutoff=0.5)
            if close_matches:
                suggestions = " or ".join(m.title() for m in close_matches)
                errors.append(f"'{item_name}' not found. Did you mean '{suggestions}'?")
            else:
                errors.append(f"'{item_name}' was not found in the menu.")
            continue

        valid_items.append(MenuItem(
            item=lookup.title(),
            size=sz.title() if sz else None,
            quantity=mi.quantity,
            price=kb_price,
        ))

    return errors, merge_items(valid_items)


# ---------------------------------------------------------------------------
# Order-level field validation
# ---------------------------------------------------------------------------

def normalize_address(address: str) -> str:
    """Expand known city abbreviations in an address string."""
    if not address:
        return address
    addr_lower = address.lower()
    for alias, full in _CITY_ALIASES.items():
        # Match whole word only (avoid replacing "rwp" inside longer words)
        import re
        addr_lower = re.sub(rf'\b{re.escape(alias)}\b', full, addr_lower)
    # Re-apply original casing for non-city parts, return normalized
    # Simple approach: rebuild with title-cased words
    return ", ".join(part.strip().title() for part in addr_lower.split(","))


def validate_order_fields(delivery_address: str, payment_method: str) -> list[str]:
    """Validate delivery address and payment method. Returns a list of errors."""
    from .knowledge_base import LOCATIONS
    errors: list[str] = []

    addr = normalize_address((delivery_address or "").strip())

    if len(addr) < 5:
        from app.agent.prompts.prompts import VALIDATE_ADDRESS_MISSING_MSG
        errors.append(VALIDATE_ADDRESS_MISSING_MSG)
    else:
        addr_lower = addr.lower()
        all_areas  = [a.lower() for areas in LOCATIONS.values() for a in areas]
        if not any(city in addr_lower for city in LOCATIONS) and \
           not any(area in addr_lower for area in all_areas):
            from app.agent.prompts.prompts import VALIDATE_LOCATION_UNSUPPORTED_MSG
            errors.append(VALIDATE_LOCATION_UNSUPPORTED_MSG)

    # Fuzzy payment matching: handle typos like "caesh" → "cash"
    raw_payment = (payment_method or "").strip().lower()
    if raw_payment and raw_payment not in VALID_PAYMENT_METHODS:
        close = difflib.get_close_matches(raw_payment, list(VALID_PAYMENT_METHODS), n=1, cutoff=0.5)
        if not close:
            from app.agent.prompts.prompts import VALIDATE_PAYMENT_INVALID_MSG
            errors.append(VALIDATE_PAYMENT_INVALID_MSG)
        # If fuzzy match found, we let it pass — extract will have set a valid value

    elif not raw_payment:
        from app.agent.prompts.prompts import VALIDATE_PAYMENT_INVALID_MSG
        errors.append(VALIDATE_PAYMENT_INVALID_MSG)

    return errors


# ---------------------------------------------------------------------------
# Total
# ---------------------------------------------------------------------------

def compute_total(items: list[MenuItem]) -> int:
    return sum(mi.price * mi.quantity for mi in items)


# ---------------------------------------------------------------------------
# Menu summary for extraction prompt
# ---------------------------------------------------------------------------

def build_menu_summary() -> str:
    """Render a compact, LLM-readable menu grouped by category."""
    from .knowledge_base import get_menu_by_category
    menu  = get_menu_by_category()
    lines: list[str] = []
    for category, items in menu.items():
        lines.append(f"\n{category.upper()}:")
        for item in items:
            name = item["name"]
            if name.lower() in _CRUST_UPGRADES:
                lines.append(f"  - {name}: ₨{item['price']} [CRUST ADD-ON — not a standalone item]")
            elif "price" in item:
                lines.append(f"  - {name}: ₨{item['price']}")
            elif "sizes" in item:
                sizes = ", ".join(item["sizes"].keys())
                lines.append(f"  - {name} [Sizes: {sizes}]")
    return "\n".join(lines).strip()# ---------------------------------------------------------------------------
# Extraction Node Helpers (Separation of Concerns)
# ---------------------------------------------------------------------------

def prepare_extraction_inputs(state: dict, cart_txt: str, analysis: dict, errors: list, pending: str, menu_summary: str) -> dict:
    """Prepares structured inputs (context & history) for the extraction LLM."""
    from langchain_core.messages import AIMessage, HumanMessage
    from app.core.config import settings
    
    # Identify turn metadata
    decision = analysis.get("decision") if isinstance(analysis, dict) else getattr(analysis, "decision", None)
    mods     = analysis.get("modifications") if isinstance(analysis, dict) else getattr(analysis, "modifications", None)
    is_edit  = (decision == "edit")

    # 1. Build Context String
    ctx = []
    if state.get("summary"):          ctx.append(f"Conversation summary: {state['summary']}")
    if cart_txt != "Empty":           ctx.append(f"Current cart: {cart_txt}")
    if state.get("delivery_address"): ctx.append(f"Current delivery address: {state['delivery_address']}")
    if state.get("payment_method"):   ctx.append(f"Current payment method: {state['payment_method']}")
    
    if errors:
        ctx.append("Validation errors to fix:")
        ctx.extend(f"  • {e}" for e in errors)
    elif is_edit and mods:
        ctx.append(f"Requested change: {mods}")

    # 2. Build History Messages
    msgs = state.get("messages", [])
    if errors: # Repair loop
        _last_human = msgs[-1].content if msgs and hasattr(msgs[-1], 'content') else ""
        history = [
            AIMessage(content=f"Current cart: {cart_txt}"),
            AIMessage(content="User is correcting the validation errors mentioned."),
            HumanMessage(content=_last_human)
        ]
    elif is_edit: # Edit from confirmation
        history = [
            AIMessage(content=f"Current cart: {cart_txt}"),
            AIMessage(content=f"Requested change: {mods}"),
            HumanMessage(content=msgs[-1].content if msgs else "")
        ]
    else: # Fresh turn
        token_limit = settings.RECENT_CONTEXT_MESSAGES
        recent = msgs[-token_limit:] if msgs else []
        history = [m for m in recent if not ("SUCCESS" in (getattr(m, "content", "") or "") and "Order" in (getattr(m, "content", "") or ""))]

    return {
        "menu":    menu_summary,
        "context": "\n".join(ctx),
        "history": history,
    }


def format_extraction_result(state: dict, extraction: any, pending: str) -> dict:
    """Resolves items, normalizes address, and commits turn to history."""
    from langchain_core.messages import AIMessage, HumanMessage
    
    # 1. Resolve Items against Menu
    pm, sb = build_price_map()
    resolved_items, warnings = _resolve_items(extraction.items or [], pm, sb)

    # 2. Commit History (Human message + System warnings)
    history_update = []
    if pending:
        history_update.append(HumanMessage(content=pending))
    if warnings:
        history_update.extend([AIMessage(content=f"System: {w}") for w in warnings])

    # 3. Address Normalization
    raw_addr = (extraction.delivery_address or "").strip()
    norm_addr = normalize_address(raw_addr) if raw_addr else normalize_address(state.get("delivery_address") or "")

    # 4. Payment Normalization (fuzzy match typos like "caesh" → "cash")
    raw_payment = (extraction.payment_method or "").strip().lower()
    if raw_payment and raw_payment not in VALID_PAYMENT_METHODS:
        close = difflib.get_close_matches(raw_payment, list(VALID_PAYMENT_METHODS), n=1, cutoff=0.5)
        norm_payment = close[0] if close else None
    elif raw_payment:
        norm_payment = raw_payment
    else:
        norm_payment = state.get("payment_method")

    return {
        "items":               merge_items(resolved_items),
        "delivery_address":    norm_addr or None,
        "payment_method":      norm_payment,
        "messages":            history_update,
        "pending_user_input":  "",
        "validation_errors":   [], 
        "valid":               False, 
        "last_analysis":       None,
    }
