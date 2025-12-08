# Custom UDFs (User-Defined Functions)

## Overview

This project uses custom Snowflake UDFs that must be preserved during SQL translation and properly referenced in DBT models.

---

## GETENUMML Function

### Purpose
Retrieves multilanguage translations for system enumerations from the MILES system.

### Function Signature

```sql
TFSES_ANALYTICS.TFS_SILVER.GETENUMML(ENUMERATIONID NUMBER, MULTILANGUAGEID NUMBER)
RETURNS VARCHAR
```

### Parameters

1. **ENUMERATIONID** (NUMBER): The enumeration ID from `MILES_SYSENUMERATION.SYSENUMERATION_ID`
2. **MULTILANGUAGEID** (NUMBER): The language ID (4 = default language, typically English/French)

### Implementation Location

**File:** `GETENUMML_function.sql` (project root)

**Schema:** `TFSES_ANALYTICS.TFS_SILVER`

### Function Logic

```sql
CREATE OR REPLACE FUNCTION TFSES_ANALYTICS.TFS_SILVER.GETENUMML("ENUMERATIONID" NUMBER(38,0), "MULTILANGUAGEID" NUMBER(38,0))
RETURNS VARCHAR
LANGUAGE SQL
AS '
SELECT COALESCE(
    (SELECT t.translation
     FROM TFS_BRONZE.MILES_TRANSLATEDSTRING t
     WHERE t.language_id = MultilanguageId
       AND t.multilanguagestring_id = s.description_mlid
     LIMIT 1),
    (SELECT t.translation
     FROM TFS_BRONZE.MILES_LANGUAGE l
     JOIN TFS_BRONZE.MILES_TRANSLATEDSTRING t
       ON l.parentlanguage_id = t.language_id
     WHERE l.language_id = MultilanguageId
       AND t.multilanguagestring_id = s.description_mlid
     LIMIT 1),
    s.description
)
FROM TFS_BRONZE.MILES_SYSENUMERATION s
WHERE s.sysenumeration_id = EnumerationId
LIMIT 1
';
```

### How It Works

1. First attempts to find a translation in the requested language
2. If not found, tries the parent language
3. Falls back to the default description if no translation exists

### Usage in DBT Models

**Example from `stg_status.sql`:**

```sql
miles_status as (
    select
        cast(sysenumeration_id as varchar(100)) as status_id,
        name as status_desc,
        groupname as group_id,
        TFSES_ANALYTICS.TFS_SILVER.GETENUMML(group_enumid, 4) as group_desc,
        'Miles' as source_system,
        'contract' as related_object_type
    from {{ source('miles', 'MILES_DM_CONTRACTSTATE_DIM') }} s
)
```

### Alternative: Inline CTE Approach

If you prefer not to use the UDF (for better DBT lineage tracking), use this CTE pattern:

```sql
enum_translations as (
    select
        s.sysenumeration_id,
        coalesce(
            t1.translation,
            t2.translation,
            s.description
        ) as description_ml
    from {{ source('miles', 'MILES_SYSENUMERATION') }} s
    left join {{ source('miles', 'MILES_TRANSLATEDSTRING') }} t1
        on t1.language_id = 4
       and t1.multilanguagestring_id = s.description_mlid
    left join {{ source('miles', 'MILES_LANGUAGE') }} l
        on l.language_id = 4
    left join {{ source('miles', 'MILES_TRANSLATEDSTRING') }} t2
        on l.parentlanguage_id = t2.language_id
       and t2.multilanguagestring_id = s.description_mlid
)
```

### Required Source Tables

The function depends on these bronze layer tables:
- `MILES_SYSENUMERATION`
- `MILES_TRANSLATEDSTRING`
- `MILES_LANGUAGE`

Ensure these are defined in `models/bronze/_sources.yml`.

---

## Agent Guidelines

### When Translating SQL

1. **Preserve UDF calls** - Do NOT translate `GETENUMML` to standard SQL
2. **Use full schema path:** `TFSES_ANALYTICS.TFS_SILVER.GETENUMML(...)`
3. **Do NOT use:** `MILES.GETENUMML(...)` (incorrect schema)

### When Generating DBT Models

1. **Document UDF dependency** in model comments:
   ```sql
   {#
       Dependencies: Custom UDF TFSES_ANALYTICS.TFS_SILVER.GETENUMML
   #}
   ```

2. **Add to validation warnings** if UDF is used:
   - "Model uses custom UDF GETENUMML - must be deployed to Snowflake before execution"

3. **Offer alternative** in documentation:
   - Mention that the inline CTE approach can be used for better lineage tracking

### Variables

Use DBT variable for language ID:
```sql
TFSES_ANALYTICS.TFS_SILVER.GETENUMML(group_enumid, {{ var('default_language_id') }})
```

In `dbt_project.yml`:
```yaml
vars:
  default_language_id: 4
```

---

## Future Custom UDFs

When adding new custom UDFs to `config/schema_registry.json`:

```json
{
  "custom_functions": [
    {
      "name": "GETENUMML",
      "schema": "TFSES_ANALYTICS.TFS_SILVER",
      "preserve": true,
      "deployment_required": true,
      "description": "Multilanguage enumeration translation",
      "parameters": ["ENUMERATIONID NUMBER", "MULTILANGUAGEID NUMBER"],
      "return_type": "VARCHAR"
    }
  ]
}
```

---

## Deployment Checklist

Before running DBT models that use custom UDFs:

- [ ] Function deployed to Snowflake
- [ ] Schema path is correct (`TFSES_ANALYTICS.TFS_SILVER`)
- [ ] Source tables exist in bronze layer
- [ ] DBT variables configured (e.g., `default_language_id`)
- [ ] Documentation includes UDF dependency note

---

## Troubleshooting

**Error: "Unknown function GETENUMML"**
- Solution: Deploy function from `GETENUMML_function.sql`

**Error: "SQL compilation error: invalid identifier 'MILES.GETENUMML'"**
- Solution: Use full schema path `TFSES_ANALYTICS.TFS_SILVER.GETENUMML`

**Empty translations returned**
- Check: Source tables `MILES_SYSENUMERATION`, `MILES_TRANSLATEDSTRING`, `MILES_LANGUAGE` have data
- Check: Language ID is valid (4 = default)

---

**Reference File:** `GETENUMML_function.sql` (project root)
