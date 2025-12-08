{{
    config(
        materialized='table',
        tags=['silver', '<SOURCE_SYSTEM>']
    )
}}

{#
    Intermediate Model Template - Silver Layer

    Purpose: Apply business logic and transformations to staging data
    Layer: Silver (intermediate__)
    Source: Pentaho mas_* files

    Guidelines:
    - Use {{ ref() }} macro for dependencies
    - Apply business logic and calculations
    - Join multiple staging models if needed
    - Use descriptive CTE names for each transformation step
    - Add comments for complex business rules
    - Filter out invalid/unwanted records
    - Standardize data formats

    Example Usage:
    - mas_contracts.ktr → intermediate__contracts.sql
    - mas_status_history.ktr → intermediate__status_history.sql
#}

with staging_data as (

    select * from {{ ref('staging__<TABLE_NAME>') }}

),

{#
    Import additional dependencies if joining multiple sources
#}
additional_source as (

    select * from {{ ref('staging__<RELATED_TABLE>') }}

),

{#
    Apply business rules and filters
#}
apply_business_rules as (

    select
        *,

        -- Business calculations
        case
            when <condition_1> then '<value_1>'
            when <condition_2> then '<value_2>'
            else '<default_value>'
        end as <derived_column>,

        -- Date calculations
        datediff(month, start_date, end_date) as duration_months,

        -- Flags
        case
            when status = 'A' then true
            else false
        end as is_active

    from staging_data
    where <filter_condition>  -- Apply data quality filters

),

{#
    If joining multiple sources
#}
joined as (

    select
        sd.<pk_column>,
        sd.<column_1>,
        sd.<column_2>,

        -- From related table
        rt.<related_column_1>,
        rt.<related_column_2>

    from apply_business_rules sd
    left join additional_source rt
        on sd.<fk_column> = rt.<pk_column>

),

{#
    Add calculated fields and business logic
#}
add_calculations as (

    select
        *,

        -- Complex calculations
        <column_1> * coalesce(<column_2>, 1) as <calculated_value>,

        -- Conditional logic
        iff(<condition>, <true_value>, <false_value>) as <derived_flag>,

        -- String manipulations
        upper(trim(<string_column>)) as <standardized_string>,

        -- Aggregations (if needed with window functions)
        sum(<amount>) over (partition by <group_column>) as <total_by_group>

    from joined  {# or from apply_business_rules if no join #}

),

{#
    Apply final filters and data quality checks
#}
data_quality as (

    select *
    from add_calculations

    where 1=1
        -- Data quality filters
        and <pk_column> is not null
        and <required_column> is not null
        -- Business filters
        and <date_column> >= '{{ var("history_start_date", "2020-01-01") }}'

),

final as (

    select
        -- Explicitly list columns in desired order
        <pk_column>,
        <fk_column_1>,
        <fk_column_2>,

        -- Attributes
        <attribute_1>,
        <attribute_2>,

        -- Calculated fields
        <calculated_value>,
        <derived_flag>,

        -- Dates
        <date_column>,
        <timestamp_column>,

        -- Metadata
        _loaded_at,
        _source_system

    from data_quality

)

select * from final
