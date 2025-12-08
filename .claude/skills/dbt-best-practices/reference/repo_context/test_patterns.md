# Test Patterns Used

Generated: 2025-10-27
Repository: {dbt_repository} (from project.config.json)

## Current Test Status

**Tests Defined**: 0 model-level tests found in YAML documentation
**Testing Strategy**: Currently relying on model logic and data quality flags

## Common DBT Test Patterns (Recommended)

Based on the model structures analyzed, these are recommended test patterns for this project:

### 1. Primary Key Tests

**Usage**: Every dimension and fact should test primary key uniqueness and not_null

**Pattern**:
```yaml
models:
  - name: d_customer
    columns:
      - name: CUSTOMER_NK
        tests:
          - unique
          - not_null
```

**Apply to**:
- d_customer: CUSTOMER_NK
- d_dealer: DEALER_NK
- d_approval_level: APPROVAL_LEVEL_NK
- mas_contracts: CONTRACT_ID_EKIP (with incremental consideration)
- stg_contracts: CONTRACT_ID_EKIP (with incremental consideration)

### 2. Foreign Key Relationship Tests

**Usage**: Validate relationships between models

**Pattern**:
```yaml
models:
  - name: mas_contracts
    columns:
      - name: CUSTOMER_ID
        tests:
          - relationships:
              to: ref('mas_customers')
              field: CUSTOMER_ID
```

**Recommended Relationships**:
- mas_contracts.CUSTOMER_ID → mas_customers.CUSTOMER_ID
- mas_contracts.STATUS_ID → mas_status.STATUS_ID
- mas_contract_dealers.CONTRACT_ID_EKIP → mas_contracts.CONTRACT_ID_EKIP
- mas_contract_dealers.DEALER → mas_dealer.DEALER_ID
- d_customer references → mas_customers
- d_dealer references → mas_dealer

### 3. Accepted Values Tests

**Usage**: Validate enumerated fields

**Pattern**:
```yaml
models:
  - name: mas_contracts
    columns:
      - name: ACCOUNTING_STATUS
        tests:
          - accepted_values:
              values: ['EXPL', 'IRRM', 'RELO', 'MELO']
```

**Apply to**:
- mas_contracts.DIGITAL_SIGNATURE: ['Y', 'N']
- stg_status.SOURCE_SYSTEM: ['EKIP', 'MILES']
- mas_customers.RESIDENT: [expected values]
- mas_customers.GENDER: [expected values]

### 4. Data Quality Flag Tests

**Usage**: Models with is_valid_* flags should test they're not all false

**Pattern**:
```yaml
models:
  - name: stg_status
    tests:
      - dbt_utils.expression_is_true:
          expression: "sum(case when is_valid_status_id then 1 else 0 end) > 0"
```

**Apply to**:
- stg_status: is_valid_status_id, is_valid_status_desc

### 5. Date Logic Tests

**Usage**: Validate date ranges and ordering

**Pattern**:
```yaml
models:
  - name: mas_contracts
    tests:
      - dbt_utils.expression_is_true:
          expression: "START_DATE <= END_DATE or END_DATE is null"
      - dbt_utils.expression_is_true:
          expression: "DATE_CREATION <= APPROVAL_DATE or APPROVAL_DATE is null"
```

**Apply to**:
- mas_contracts: START_DATE ≤ END_DATE, DATE_CREATION ≤ APPROVAL_DATE
- d_customer: DATE_FROM < DATE_TO
- d_dealer: DATE_FROM < DATE_TO, START_DATE ≤ END_DATE
- source_date: No future dates beyond reasonable range

### 6. Incremental Model Tests

**Usage**: Validate incremental loads don't create duplicates

**Pattern**:
```yaml
models:
  - name: stg_contracts
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - CONTRACT_ID_EKIP
```

**Apply to**:
- stg_contracts (incremental merge)
- mas_contracts (incremental merge)
- stg_status_history (incremental merge)
- stg_early_terminations (incremental merge)
- d_customer (incremental merge)
- d_dealer (incremental merge)

### 7. Source Freshness Tests

**Usage**: Ensure source data is being updated

**Pattern**:
```yaml
sources:
  - name: bronze
    tables:
      - name: EKIP_AFFAIRE
        freshness:
          warn_after: {count: 24, period: hour}
          error_after: {count: 48, period: hour}
        loaded_at_field: updated_at
```

**Recommended for critical sources**:
- EKIP_AFFAIRE
- EKIP_TIERS
- MILES_CONTRACT

## Test Coverage by Layer

### Bronze Layer
- source_date: No tests currently (infrastructure model)
- Recommended: Test for no gaps in date sequence

### Silver ADQ Layer
**Current**: 0 tests
**Recommended**:
- Primary key tests on all staging models
- Not null tests on key fields
- Accepted values for status fields
- Average 3-5 tests per model

### Silver MAS Layer
**Current**: 0 tests
**Recommended**:
- Relationship tests to upstream stg_ models
- Primary key tests
- Date logic validation tests
- Average 4-6 tests per model

### Gold Layer
**Current**: 0 tests
**Recommended**:
- Unique tests on NK fields
- Not null tests on NK fields
- Relationship tests to MAS layer
- SCD Type 2 validation (DATE_FROM < DATE_TO)
- Average 5-8 tests per model

## Custom Test Patterns

### Julian Date Conversion Validation

Since many models use convert_from_julian macro, validate results:

```yaml
models:
  - name: stg_contracts
    tests:
      - dbt_utils.expression_is_true:
          expression: "DATE_CREATION between '1900-01-01' and '2199-12-31'"
```

### Surrogate Key Pattern Validation

For models using row_number() for surrogate keys:

```yaml
models:
  - name: d_approval_level
    columns:
      - name: APPROVAL_LEVEL_ID
        tests:
          - unique
          - not_null
```

### Special Row Validation

Models with default rows (UNK, N/A):

```yaml
models:
  - name: d_approval_level
    tests:
      - dbt_utils.expression_is_true:
          expression: "count(*) filter (where APPROVAL_LEVEL_NK = 'UNK') = 1"
      - dbt_utils.expression_is_true:
          expression: "count(*) filter (where APPROVAL_LEVEL_NK = 'N/A') = 1"
```

## Testing Strategy Recommendations

### Phase 1: Critical Tests (Immediate)
1. Primary key uniqueness on all gold dimensions
2. Not null on all NK fields
3. Relationship tests between gold → MAS → ADQ layers

### Phase 2: Data Quality Tests (Short-term)
1. Accepted values for enumerated fields
2. Date logic validation
3. Data quality flag validation

### Phase 3: Comprehensive Coverage (Long-term)
1. Source freshness checks
2. Custom business rule tests
3. Incremental model validation
4. Cross-model consistency tests

## Test Organization

### Recommended File Structure

```
models/
├── bronze/
│   └── _models.yml          # source_date tests
├── silver/
│   ├── silver_adq/
│   │   └── _models.yml      # All stg_ model tests
│   └── silver_mas/
│       └── _models.yml      # All mas_ model tests
└── gold/
    └── _models.yml          # All dimension tests
```

### Test Execution Strategy

**Daily**:
- Primary key uniqueness
- Not null on critical fields
- Source freshness

**Weekly**:
- Relationship tests
- Data quality validation
- Date logic tests

**Monthly**:
- Full test suite
- Custom business rule tests

## DBT Utils Test Functions Available

If dbt_utils package is installed, these test functions are available:

1. **unique_combination_of_columns**: Test uniqueness of column combinations
2. **expression_is_true**: Test custom SQL expressions
3. **relationships_where**: Conditional relationship tests
4. **at_least_one**: Ensure at least one non-null value
5. **not_null_proportion**: Ensure % of non-null values

## Current State Assessment

**Status**: No formal tests currently defined
**Impact**: High risk - no automated validation of data quality
**Priority**: HIGH - Implement Phase 1 tests immediately

**Estimated Effort**:
- Phase 1 (Critical): 4-6 hours
- Phase 2 (Quality): 8-10 hours
- Phase 3 (Comprehensive): 12-16 hours

## Testing Integration with Migration

When generating new models, the dbt-model-generator agent should:

1. **Generate basic tests** for all new models (unique, not_null on PKs)
2. **Add relationship tests** for known foreign keys
3. **Include accepted_values** for enumerated fields
4. **Document test rationale** in model YAML

## Notes

- All test recommendations based on model structure analysis
- No existing test files found to use as templates
- Test patterns follow DBT best practices
- Custom tests may be needed for complex business rules
- Integration with CI/CD should run tests before deployment
