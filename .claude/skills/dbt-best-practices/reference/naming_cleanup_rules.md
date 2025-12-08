# Naming Cleanup Rules

Simple rules to clean Pentaho filenames for DBT models.

## Problem

Pentaho files have numeric prefixes and extra qualifiers:
- `adq_ekip_01_status_history.ktr` → Should be `stg_status_history.sql`
- `adq_ekip_1_contract_month_end.ktr` → Should be `stg_contract_month_end.sql`
- `adq_ekip_contracts.ktr` → Should be `stg_contracts.sql`

## Simple Cleanup Steps

**Step 1: Remove adq_ prefix**
```
adq_ekip_01_status_history → ekip_01_status_history
```

**Step 2: Remove numeric prefixes (_01, _1, _001, etc.)**
```
ekip_01_status_history → ekip_status_history
ekip_1_contract_month_end → ekip_contract_month_end
```
Pattern: Remove `_\d+_` (underscore + digits + underscore)

**Step 3: Remove source system prefix for common entities**
```
ekip_status_history → status_history
ekip_contract_month_end → contract_month_end
ekip_contracts → contracts
```

Keep source prefix if:
- Multiple sources have same entity (e.g., miles_businesspartner, tes_customer)
- Ambiguous without it

**Step 4: Add stg_ prefix**
```
status_history → stg_status_history
contract_month_end → stg_contract_month_end
contracts → stg_contracts
```

---

## Complete Examples

| Pentaho File | Step 1 | Step 2 | Step 3 | Final |
|--------------|--------|--------|--------|-------|
| adq_ekip_01_status_history.ktr | ekip_01_status_history | ekip_status_history | status_history | stg_status_history |
| adq_ekip_1_contract_month_end.ktr | ekip_1_contract_month_end | ekip_contract_month_end | contract_month_end | stg_contract_month_end |
| adq_ekip_1_early_terminations.ktr | ekip_1_early_terminations | ekip_early_terminations | early_terminations | stg_early_terminations |
| adq_ekip_contracts.ktr | ekip_contracts | ekip_contracts | contracts | stg_contracts |
| adq_status.ktr | status | status | status | stg_status |
| adq_miles_businesspartner.ktr | miles_businesspartner | miles_businesspartner | miles_businesspartner | stg_miles_businesspartner |
| adq_tes_customer.ktr | tes_customer | tes_customer | tes_customer | stg_tes_customer |

---

## Code Pattern (Regex)

```python
def cleanup_adq_name(pentaho_file):
    name = pentaho_file.replace('.ktr', '').replace('.kjb', '')

    # Step 1: Remove adq_ or mas_ prefix
    if name.startswith('adq_'):
        name = name[4:]  # Remove 'adq_'

    # Step 2: Remove numeric prefixes like _01_, _1_, _001_
    import re
    name = re.sub(r'_\d+_', '_', name)

    # Step 3: Remove ekip_ prefix for common entities
    common_entities = ['contracts', 'customers', 'status', 'early_terminations',
                       'contract_month_end', 'contract_dealers', 'dealer']

    for entity in common_entities:
        if name.endswith('_' + entity) or name == 'ekip_' + entity:
            name = name.replace('ekip_', '')
            break

    # Step 4: Add stg_ prefix
    if not name.startswith('stg_'):
        name = 'stg_' + name

    return name + '.sql'

# Examples
cleanup_adq_name('adq_ekip_01_status_history.ktr')  # → stg_status_history.sql
cleanup_adq_name('adq_ekip_1_contract_month_end.ktr')  # → stg_contract_month_end.sql
cleanup_adq_name('adq_miles_businesspartner.ktr')  # → stg_miles_businesspartner.sql
```

---

## MAS Files

MAS files are simpler - just remove numeric prefix:

| Pentaho File | Cleanup | Final |
|--------------|---------|-------|
| mas_1_status_history.kjb | mas_status_history | mas_status_history |
| mas_contracts.kjb | mas_contracts | mas_contracts |
| mas_early_terminations.kjb | mas_early_terminations | mas_early_terminations |

Pattern: Remove `_\d+` after mas_

---

## Gold Files

Gold files keep their names:

| Pentaho File | Final |
|--------------|-------|
| d_approval_level.ktr | d_approval_level.sql |
| d_customer.ktr | d_customer.sql |
| d_date.ktr | d_date.sql |
| f_sales.ktr | f_sales.sql |

No cleanup needed!
