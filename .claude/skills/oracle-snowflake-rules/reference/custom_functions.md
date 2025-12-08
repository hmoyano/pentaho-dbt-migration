# Custom Snowflake Functions

This document lists project-specific Snowflake UDFs (User-Defined Functions) that must be preserved during translation.

## ⚠️ CRITICAL RULE

**NEVER translate custom functions.** These functions are already defined in Snowflake and must be used exactly as they appear in the Oracle queries.

---

## Known Custom Functions

### GETENNUML / GETENUMML ⚠️ BROKEN - MUST REPLACE

**Type:** ~~User-Defined Function (UDF)~~ **BROKEN UDF - MUST BE REPLACED**
**Purpose:** Multilingual enum translation (enum_id + language_id → translated description)
**Status:** ⚠️ **NOT WORKING CORRECTLY IN SNOWFLAKE** - Replace with explicit JOINs

**⚠️ CRITICAL: DO NOT PRESERVE THIS FUNCTION - ALWAYS REPLACE**

**Usage in Oracle/Pentaho:**
```sql
SELECT TFSES_ANALYTICS.TFS_SILVER.GETENUMML(enum_column, 4) as description
FROM table;
```

**Translation to Snowflake - MANDATORY REPLACEMENT PATTERN:**

```sql
-- Step 1: Add source CTEs (only if not already present)
source_sysenumeration as (
    select * from {{ source('bronze', 'MILES_SYSENUMERATION') }}
),
source_translatedstring as (
    select * from {{ source('bronze', 'MILES_TRANSLATEDSTRING') }}
),
source_language as (
    select * from {{ source('bronze', 'MILES_LANGUAGE') }}
),

-- Step 2: Add enum_translations CTE
enum_translations as (
    select
        s.sysenumeration_id,
        coalesce(t1.translation, t2.translation, s.description) as description_ml
    from source_sysenumeration s
    left join source_translatedstring t1
        on t1.language_id = 4 and t1.multilanguagestring_id = s.description_mlid
    left join source_language l on l.language_id = 4
    left join source_translatedstring t2
        on l.parentlanguage_id = t2.language_id
        and t2.multilanguagestring_id = s.description_mlid
),

-- Step 3: In SELECT, replace GETENUMML(...) with enum_alias.description_ml
-- BEFORE: GETENUMML(ls1.Insurance_TC, 4) as insurance_desc
-- AFTER:  enum_ins.description_ml as insurance_desc

-- Step 4: In main query, add LEFT JOIN
left join enum_translations enum_ins
    on enum_ins.sysenumeration_id = ls1.Insurance_TC
```

**Notes:**
- UDF exists but produces incorrect results - must be replaced with explicit JOINs
- language_id = 4 is typically French in MILES schema
- Each GETENUMML call needs its own LEFT JOIN with unique alias (enum_ins, enum_fuel, etc.)
- Fallback chain: direct translation → parent language → base description
- **Reference**: `{dbt_repository}/models/silver/silver_adq/stg_miles_product.sql:53-73`
- **Reference**: `{dbt_repository}/models/silver/silver_adq/stg_miles_contract.sql:126-348`

---

## How to Identify Custom Functions

1. **Check schema_registry.json**: Look for UDF definitions
2. **Look for non-standard Oracle functions**: If a function doesn't appear in standard Oracle documentation, it's likely custom
3. **Check Snowflake schema**: Query `INFORMATION_SCHEMA.FUNCTIONS` to see all UDFs
4. **Ask if uncertain**: Better to preserve than incorrectly translate

---

## Verification Query

To list all UDFs in your Snowflake environment:

```sql
SELECT
  function_name,
  function_schema,
  function_definition,
  argument_signature
FROM INFORMATION_SCHEMA.FUNCTIONS
WHERE function_schema IN ('ODS_SCHEMA', 'EKIP_SCHEMA', /* add your schemas */)
  AND function_language = 'SQL'
ORDER BY function_name;
```

---

## Adding New Custom Functions

If you discover a new custom function during migration:

1. **Document it here** with:
   - Function name
   - Purpose/description
   - Example usage
   - Source schema

2. **Add to schema_registry.json** if applicable

3. **Verify it exists in Snowflake** before marking as "custom"

---

## Template for New Entries

```markdown
### FUNCTION_NAME

**Type:** User-Defined Function (UDF)
**Purpose:** Brief description of what it does
**Location:** Schema name in Snowflake

**Usage in Oracle/Pentaho:**
```sql
SELECT FUNCTION_NAME(param1, param2) FROM table;
```

**Translation to Snowflake:**
```sql
-- DO NOT TRANSLATE - Keep as-is
SELECT FUNCTION_NAME(param1, param2) FROM table;
```

**Notes:**
- Any special considerations
- Parameter types
- Return type
```

---

## Common Patterns for Custom Functions

### Pattern 1: Lookup Functions

Custom functions that perform value lookups or transformations:

```sql
-- Example: GETENNUML
SELECT GETENNUML(status_code) as status_description
FROM contracts;
```

**Do NOT translate to:**
```sql
-- WRONG - Do not do this
SELECT CASE
  WHEN status_code = 'A' THEN 'Active'
  WHEN status_code = 'I' THEN 'Inactive'
  ...
END as status_description
FROM contracts;
```

**Keep as-is:**
```sql
-- CORRECT
SELECT GETENNUML(status_code) as status_description
FROM contracts;
```

### Pattern 2: Business Logic Functions

Functions that encapsulate complex business logic:

```sql
-- If you find something like:
SELECT CALCULATE_COMMISSION(sales_amount, employee_level) as commission
FROM sales;

-- DO NOT try to reverse-engineer the logic
-- Keep the function call as-is
```

### Pattern 3: Date/String Formatting Functions

Custom formatting that goes beyond standard functions:

```sql
-- Example
SELECT FORMAT_PHONE(phone_number) as formatted_phone
FROM customers;

-- Keep as-is, don't try to replicate with SUBSTR/CONCAT
```

---

## Translation Strategy

When encountering an unknown function:

1. **Check standard Oracle functions first**
   - Refer to function_mappings.md
   - Check Oracle documentation

2. **If not found in standard functions:**
   - Mark as potential custom function
   - Check schema_registry.json
   - Query Snowflake INFORMATION_SCHEMA
   - Preserve the function call as-is

3. **Document the function:**
   - Add to this file
   - Note where it was found
   - Add example usage

4. **Validate in Snowflake:**
   - Test that the function exists
   - Verify parameter signature matches
   - Confirm return type

---

## Functions That Look Custom But Aren't

Some Oracle functions might look custom but are actually standard:

### STANDARD Oracle Package Functions

These are built-in Oracle package functions that need translation:

```sql
-- DBMS_RANDOM.VALUE - Standard Oracle
SELECT DBMS_RANDOM.VALUE(1, 100) FROM dual;

-- Snowflake equivalent
SELECT UNIFORM(1, 100, RANDOM());
```

```sql
-- UTL_RAW.CAST_TO_RAW - Standard Oracle
SELECT UTL_RAW.CAST_TO_RAW('text') FROM dual;

-- Snowflake equivalent
SELECT TO_BINARY('text', 'UTF-8');
```

**Rule:** If it starts with a package name (DBMS_, UTL_, etc.), it's likely a standard Oracle function that needs translation, NOT a custom function.

---

## Schema-Specific Functions

Some functions might be defined in specific schemas:

```sql
-- If you see:
SELECT ODS_SCHEMA.CUSTOM_FUNC(value) FROM table;

-- Preserve schema qualification:
SELECT ODS_SCHEMA.CUSTOM_FUNC(value) FROM table;
```

---

## Testing Custom Functions

After migration, test custom functions:

```sql
-- Test function exists
SELECT GETENNUML('TEST_CODE');

-- Test with actual data
SELECT
  code_value,
  GETENNUML(code_value) as description
FROM table
LIMIT 10;
```

---

## Troubleshooting

### Function Not Found Error

If Snowflake reports "Function not found":

1. **Check schema qualification:**
   ```sql
   -- Wrong
   SELECT GETENNUML(code);

   -- Right
   SELECT ODS_SCHEMA.GETENNUML(code);
   ```

2. **Check function name case:**
   ```sql
   -- Try uppercase
   SELECT GETENNUML(code);

   -- Try lowercase
   SELECT getennuml(code);
   ```

3. **Verify function exists:**
   ```sql
   SHOW FUNCTIONS LIKE 'GETENNUML';
   ```

### Parameter Mismatch Error

If parameter types don't match:

1. **Check function signature:**
   ```sql
   DESCRIBE FUNCTION GETENNUML;
   ```

2. **Cast parameters if needed:**
   ```sql
   SELECT GETENNUML(CAST(code AS VARCHAR));
   ```

---

## Summary

**Key Points:**
- ✅ **DO** preserve custom functions exactly as-is
- ✅ **DO** document new custom functions you discover
- ✅ **DO** verify functions exist in Snowflake
- ❌ **DON'T** translate custom functions
- ❌ **DON'T** try to reverse-engineer custom logic
- ❌ **DON'T** assume a function is custom without checking

**When in doubt:**
1. Check function_mappings.md first
2. Check Oracle documentation
3. Check INFORMATION_SCHEMA.FUNCTIONS in Snowflake
4. If still unsure, preserve the function and flag for review
