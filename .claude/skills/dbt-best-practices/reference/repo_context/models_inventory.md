# Existing Models Inventory

**Generated**: 2025-11-18
**Repository**: {dbt_repository}/
**Total Models**: 85 (35 silver_adq + 35 silver_mas + 1 bronze + 14 gold)

---

## Summary

- **Bronze Layer**: 1 model (source_date utility)
- **Silver ADQ Layer**: 35 staging models
- **Silver MAS Layer**: 35 master models
- **Gold Layer**: 14 dimension models
- **Shared Models**: 21 models used by multiple dimensions
- **Dimension-Specific Models**: 64 models

---

## Key Finding: Shared vs Dimension-Specific Models

### Shared Models (Used by Multiple Dimensions)

These models are tagged with multiple `dim_*` tags and should **NOT be regenerated** when migrating a single dimension:

#### Silver ADQ - Shared Models (8 models)

1. **stg_contracts.sql**
   - Tags: `['silver', 'adq', 'contracts', 'incremental', 'dim_contract', 'dim_proposal']`
   - **Shared by**: dim_contract, dim_proposal
   - Materialization: incremental
   - Purpose: Core contract data from EKIP

2. **stg_status.sql**
   - Tags: `['silver', 'adq', 'status', 'reference_data', 'dim_contract', 'dim_proposal']`
   - **Shared by**: dim_contract, dim_proposal
   - Materialization: table
   - Purpose: Status reference data (EKIP + Miles)

3. **stg_status_history.sql**
   - Tags: `['silver', 'adq', 'status_history', 'incremental', 'dim_contract', 'dim_proposal']`
   - **Shared by**: dim_contract, dim_proposal
   - Materialization: incremental
   - Purpose: Status change history

4. **stg_early_terminations.sql**
   - Tags: `['silver', 'adq', 'early_terminations', 'incremental', 'dim_contract', 'dim_proposal']`
   - **Shared by**: dim_contract, dim_proposal
   - Materialization: incremental
   - Purpose: Early termination data

5. **stg_financial_product.sql**
   - Tags: `['silver_adq', 'dim_contract', 'dim_financial_product', 'reference']`
   - **Shared by**: dim_contract, dim_financial_product
   - Materialization: table
   - Purpose: Financial product reference data

6. **stg_miles_product.sql**
   - Tags: `['silver', 'silver_adq', 'dim_financial_product', 'miles']`
   - **Shared by**: dim_financial_product (and referenced by other dimensions)
   - Materialization: table
   - Purpose: Miles product catalog

7. **stg_miles_quotes.sql**
   - Tags: `['silver', 'adq', 'miles_quotes', 'dim_proposal']`
   - **Shared by**: dim_proposal
   - Materialization: table
   - Purpose: Miles quotes data

8. **stg_termination_reasons.sql**
   - Tags: `['silver_adq', 'dim_contract', 'reference']`
   - **Shared by**: dim_contract (reference data)
   - Materialization: table
   - Purpose: Termination reason codes

#### Silver MAS - Shared Models (13 models)

9. **mas_contracts.sql**
   - Tags: `['silver_mas', 'dim_contract']`
   - **Used by**: dim_contract
   - Materialization: incremental

10. **mas_financial_element.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

11. **mas_status.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

12. **mas_miles_user.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

13. **mas_miles_contract.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

14. **mas_guarantee.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

15. **mas_early_terminations.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

16. **mas_contract_score.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

17. **mas_refinancing.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

18. **mas_status_history.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

19. **mas_termination_reasons.sql**
    - Tags: `['silver_mas', 'dim_contract', 'reference']`
    - **Used by**: dim_contract

20. **mas_contract_month_end.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

21. **mas_users.sql**
    - Tags: `['silver_mas', 'dim_contract']`
    - **Used by**: dim_contract

22. **mas_financial_product.sql**
    - Tags: `['silver', 'silver_mas', 'dim_financial_product']`
    - **Used by**: dim_financial_product

23. **mas_miles_product.sql**
    - Tags: `['silver', 'silver_mas', 'dim_financial_product', 'miles']`
    - **Used by**: dim_financial_product

24. **mas_financial_proposals.sql**
    - Tags: `['silver_mas', 'dim_proposal']`
    - **Used by**: dim_proposal

25. **mas_miles_quotes.sql**
    - Tags: `['silver_mas', 'dim_proposal']`
    - **Used by**: dim_proposal

---

## Bronze Layer (1 model)

### Infrastructure Models - DO NOT REGENERATE

**source_date.sql**
- Tags: None (infrastructure)
- Materialization: table
- Purpose: Date dimension/calendar table
- **Status**: Shared infrastructure - never regenerate

---

## Silver ADQ Layer (35 models)

All models in this layer are staging models with prefix `stg_*`.

**Default Configuration**:
- Materialization: `table` (default) or `incremental` (for large tables)
- Schema: `silver`
- Tags: `['silver', 'adq', ...]`

### Complete List (Alphabetical)

1. stg_3cx_user.sql
2. stg_approval_level.sql
3. stg_catalog.sql
4. stg_contract_dealers.sql
5. stg_contract_month_end.sql
6. stg_contracts.sql - **SHARED** (dim_contract, dim_proposal)
7. stg_customers.sql
8. stg_customers_groups.sql
9. stg_dbrisk_customers.sql
10. stg_dealer.sql
11. stg_early_terminations.sql - **SHARED** (dim_contract, dim_proposal)
12. stg_ekip_contract_score.sql
13. stg_financial_element.sql
14. stg_financial_product.sql - **SHARED** (dim_contract, dim_financial_product)
15. stg_financial_proposals.sql
16. stg_guarantee.sql
17. stg_lrt_customers.sql
18. stg_miles_businesspartner.sql
19. stg_miles_contract.sql
20. stg_miles_product.sql - **SHARED** (dim_financial_product)
21. stg_miles_quotes.sql - **SHARED** (dim_proposal)
22. stg_miles_salesman.sql
23. stg_miles_user.sql
24. stg_refinancing.sql
25. stg_salesman.sql
26. stg_status.sql - **SHARED** (dim_contract, dim_proposal)
27. stg_status_history.sql - **SHARED** (dim_contract, dim_proposal)
28. stg_stock_dealers.sql
29. stg_termination_reasons.sql - **SHARED** (dim_contract)
30. stg_tes_catalog.sql
31. stg_tes_customer.sql
32. stg_tes_dealer.sql
33. stg_tes_sales.sql
34. stg_tes_salesman.sql
35. stg_users.sql

---

## Silver MAS Layer (35 models)

All models in this layer are master models with prefix `mas_*`.

**Default Configuration**:
- Materialization: `table` (default) or `incremental` (for large tables)
- Schema: `silver`
- Tags: `['silver_mas', ...]`

### Complete List (Alphabetical)

1. mas_3cx_user.sql
2. mas_approval_level.sql
3. mas_catalog.sql
4. mas_cc_call_detail.sql
5. mas_contract_dealers.sql
6. mas_contract_month_end.sql - **SHARED** (dim_contract)
7. mas_contract_score.sql - **SHARED** (dim_contract)
8. mas_contracts.sql - **SHARED** (dim_contract)
9. mas_customers.sql
10. mas_customers_groups.sql
11. mas_dealer.sql
12. mas_early_terminations.sql - **SHARED** (dim_contract)
13. mas_financial_element.sql - **SHARED** (dim_contract)
14. mas_financial_product.sql - **SHARED** (dim_financial_product)
15. mas_financial_proposals.sql - **SHARED** (dim_proposal)
16. mas_guarantee.sql - **SHARED** (dim_contract)
17. mas_miles_businesspartner.sql
18. mas_miles_contract.sql - **SHARED** (dim_contract)
19. mas_miles_product.sql - **SHARED** (dim_financial_product)
20. mas_miles_quotes.sql - **SHARED** (dim_proposal)
21. mas_miles_salesman.sql
22. mas_miles_user.sql - **SHARED** (dim_contract)
23. mas_refinancing.sql - **SHARED** (dim_contract)
24. mas_risk_interveners.sql
25. mas_salesman.sql
26. mas_status.sql - **SHARED** (dim_contract)
27. mas_status_history.sql - **SHARED** (dim_contract)
28. mas_stock_dealers.sql
29. mas_termination_reasons.sql - **SHARED** (dim_contract)
30. mas_tes_catalog.sql
31. mas_tes_customer.sql
32. mas_tes_dealer.sql
33. mas_tes_installation.sql
34. mas_tes_salesman.sql
35. mas_users.sql - **SHARED** (dim_contract)

---

## Gold Layer (14 models)

All models in this layer are dimension models with prefix `d_*`.

**Default Configuration**:
- Materialization: `table` (default) or `incremental` (for SCD2)
- Schema: `gold`
- Tags: `['gold', 'dimension', '<dimension_name>']`

### Active Dimensions (12 models)

1. **d_approval_level.sql**
   - Tags: `['gold', 'dimension', 'approval_level']`
   - Materialization: table
   - SCD: Type 1
   - Depends on: mas_approval_level

2. **d_company.sql**
   - Tags: `['gold', 'dimension', 'company']`
   - Materialization: table
   - SCD: Type 1
   - Depends on: seed

3. **d_contract.sql**
   - Tags: `['gold', 'dimension', 'contract', 'scd2']`
   - Materialization: incremental
   - SCD: Type 2
   - Depends on: Multiple mas_* models

4. **d_customer.sql**
   - Tags: `['gold', 'dimension', 'customer', 'scd2']`
   - Materialization: incremental
   - SCD: Type 2
   - Depends on: mas_customers, mas_customers_groups, etc.

5. **d_date.sql**
   - Tags: `['gold', 'dimension', 'date']`
   - Materialization: table
   - SCD: Type 1
   - Depends on: source_date

6. **d_dealer.sql**
   - Tags: `['gold', 'dimension', 'dealer']`
   - Materialization: table
   - SCD: Type 1
   - Depends on: mas_dealer

7. **d_financial_product.sql**
   - Tags: `['gold', 'dimension', 'financial_product']`
   - Materialization: table
   - SCD: Type 1
   - Depends on: mas_financial_product, mas_miles_product

8. **d_financial_proposal.sql**
   - Tags: `['gold', 'dimension', 'financial_proposal']`
   - Materialization: table
   - SCD: Type 1
   - Depends on: mas_financial_proposals, mas_miles_quotes

9. **d_salesman.sql**
   - Tags: `['gold', 'dimension', 'salesman']`
   - Materialization: table
   - SCD: Type 1
   - Depends on: mas_salesman, mas_miles_salesman

10. **d_salesman_role.sql**
    - Tags: `['gold', 'dimension', 'salesman_role']`
    - Materialization: table
    - SCD: Type 1
    - Depends on: Hard-coded reference data

11. **d_termination_reason.sql**
    - Tags: `['gold', 'dimension', 'termination_reason']`
    - Materialization: table
    - SCD: Type 1
    - Depends on: mas_termination_reasons

12. **d_user.sql**
    - Tags: `['gold', 'dimension', 'user']`
    - Materialization: table
    - SCD: Type 1
    - Depends on: mas_users, mas_miles_user, mas_3cx_user

### Deprecated/Old Models (2 models)

13. **d_approval_level_old.sql** - Deprecated (use d_approval_level.sql)
14. **d_date_old.sql** - Deprecated (use d_date.sql)

---

## Dimension Ownership Map

This map shows which dimensions "own" which models (based on tags):

### dim_approval_level
- stg_approval_level.sql
- mas_approval_level.sql
- d_approval_level.sql

### dim_contract
- stg_contracts.sql (SHARED with dim_proposal)
- stg_contract_month_end.sql
- stg_ekip_contract_score.sql
- stg_financial_element.sql
- stg_financial_product.sql (SHARED with dim_financial_product)
- stg_guarantee.sql
- stg_miles_contract.sql
- stg_miles_user.sql
- stg_refinancing.sql
- stg_status.sql (SHARED with dim_proposal)
- stg_status_history.sql (SHARED with dim_proposal)
- stg_termination_reasons.sql
- stg_users.sql
- stg_early_terminations.sql (SHARED with dim_proposal)
- mas_contracts.sql
- mas_contract_month_end.sql
- mas_contract_score.sql
- mas_early_terminations.sql
- mas_financial_element.sql
- mas_guarantee.sql
- mas_miles_contract.sql
- mas_miles_user.sql
- mas_refinancing.sql
- mas_status.sql
- mas_status_history.sql
- mas_termination_reasons.sql
- mas_users.sql
- d_contract.sql

### dim_customer
- stg_customers.sql
- stg_customers_groups.sql
- stg_dbrisk_customers.sql
- stg_lrt_customers.sql
- stg_miles_businesspartner.sql
- stg_tes_customer.sql
- mas_customers.sql
- mas_customers_groups.sql
- mas_miles_businesspartner.sql
- mas_risk_interveners.sql
- mas_tes_customer.sql
- d_customer.sql

### dim_dealer
- stg_dealer.sql
- stg_contract_dealers.sql
- stg_stock_dealers.sql
- stg_tes_dealer.sql
- mas_dealer.sql
- mas_contract_dealers.sql
- mas_stock_dealers.sql
- mas_tes_dealer.sql
- d_dealer.sql

### dim_financial_product
- stg_financial_product.sql (SHARED with dim_contract)
- stg_miles_product.sql
- mas_financial_product.sql
- mas_miles_product.sql
- d_financial_product.sql

### dim_proposal
- stg_contracts.sql (SHARED with dim_contract)
- stg_early_terminations.sql (SHARED with dim_contract)
- stg_financial_proposals.sql
- stg_miles_quotes.sql
- stg_status.sql (SHARED with dim_contract)
- stg_status_history.sql (SHARED with dim_contract)
- mas_financial_proposals.sql
- mas_miles_quotes.sql
- d_financial_proposal.sql

### dim_salesman
- stg_salesman.sql
- stg_miles_salesman.sql
- stg_tes_salesman.sql
- mas_salesman.sql
- mas_miles_salesman.sql
- mas_tes_salesman.sql
- d_salesman.sql

---

## Important Patterns

### Materialization Strategy

**Silver ADQ** (Staging):
- Default: `table`
- Incremental for large/frequently updated tables:
  - stg_contracts (incremental)
  - stg_status_history (incremental)
  - stg_early_terminations (incremental)

**Silver MAS** (Master):
- Default: `table`
- Incremental with merge strategy:
  - mas_approval_level (incremental, unique_key='approval_level_nk')
  - mas_contracts (incremental)

**Gold** (Dimensions):
- Default: `table`
- Incremental for SCD Type 2:
  - d_contract (incremental, scd2)
  - d_customer (incremental, scd2)

### Naming Conventions

**Silver ADQ**: `stg_<entity>.sql`
- Prefix: `stg_` (staging)
- Examples: stg_contracts, stg_customers, stg_dealer

**Silver MAS**: `mas_<entity>.sql`
- Prefix: `mas_` (master)
- Examples: mas_contracts, mas_customers, mas_dealer

**Gold**: `d_<entity>.sql` or `f_<entity>.sql`
- Prefix: `d_` (dimension) or `f_` (fact)
- Examples: d_contract, d_customer, d_date

### Tag Patterns

**Layer tags**: `silver`, `silver_adq`, `silver_mas`, `gold`
**Type tags**: `dimension`, `incremental`, `reference_data`, `scd2`
**Dimension tags**: `dim_<name>` (e.g., dim_contract, dim_customer)

Multiple `dim_*` tags indicate shared models!

---

## Critical Warnings for Migration Agents

### DO NOT REGENERATE These Models

**Infrastructure Models** (not dimension-specific):
- bronze/source_date.sql

**Shared Models** (multiple dimensions depend on them):
- Any model with multiple `dim_*` tags (see list above)
- 21 models marked as SHARED in this document

### When Migrating a New Dimension

1. **Check existing models first** - Search for models with your dimension tag
2. **Reuse shared models** - Use `{{ ref() }}` to existing stg_*/mas_* models
3. **Only create new models** - If functionality doesn't exist yet
4. **Add dimension tag** - To existing shared models if needed

### Example: Migrating dim_product

**Before creating models**, check:
- Does stg_product already exist? → Yes, reuse it
- Does mas_product already exist? → Yes, reuse it
- Does d_product exist? → No, create it

**Only generate**: `d_product.sql`
**Reference existing**: stg_product, mas_product

---

## Model Documentation

**Documentation files**:
- `models/silver/silver_adq/_models.yml` - Documents silver ADQ models
- `models/gold/_models.yml` - Documents gold models
- No _models.yml for silver_mas yet

**Documentation includes**:
- Model descriptions
- Column descriptions
- Tests (not_null, unique, relationships)
- Business logic notes

---

**Last Updated**: 2025-11-18
**Total Models**: 85 (bronze: 1, silver_adq: 35, silver_mas: 35, gold: 14)
**Shared Models**: 21 (DO NOT regenerate without careful analysis)
