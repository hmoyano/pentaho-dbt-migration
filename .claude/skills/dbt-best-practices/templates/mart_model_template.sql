{{
    config(
        materialized='incremental',
        unique_key='<PK_COLUMN>',
        tags=['gold', '<DIMENSION_OR_FACT>'],
        cluster_by=['<KEY_COLUMN>']  -- Optional: for large tables
    )
}}

{#
    Mart Model Template - Gold Layer (Dimension or Fact)

    Purpose: Final analytical model for consumption by BI tools
    Layer: Gold (dim_* or fact_*)
    Source: Pentaho d_* or f_* files

    Guidelines:
    - Use incremental materialization for large tables (>1M rows)
    - Always specify unique_key for incremental models
    - Add comprehensive documentation
    - Include data quality tests
    - Use clustering for frequently filtered columns
    - Add surrogate keys for dimensions (if SCD Type 2)

    Example Usage:
    - d_approval_level.ktr → dim_approval_level.sql
    - d_customer.ktr → dim_customer.sql (with SCD Type 2 if needed)
    - f_sales.ktr → fact_sales.sql
#}

with source_data as (

    select * from {{ ref('intermediate__<TABLE_NAME>') }}

    {#
        For incremental models, filter to new/changed records only
    #}
    {% if is_incremental() %}
        where <updated_at_column> > (select max(<updated_at_column>) from {{ this }})
        {# Alternative: Use a configured incremental strategy
           - merge: Update existing and insert new (requires unique_key)
           - append: Only insert new records
           - delete+insert: Delete matching keys and insert
        #}
    {% endif %}

),

{#
    For dimensions: Add slowly changing dimension logic (SCD Type 2)
#}
{% if '<DIMENSION_OR_FACT>' == 'dimension' %}

add_scd_columns as (

    select
        {# Surrogate key (composite of natural key + effective date) #}
        {{ dbt_utils.surrogate_key(['<natural_key>', '<effective_date>']) }} as surrogate_key,

        {# Natural key (business key) #}
        <natural_key>,

        {# Attributes #}
        <attribute_1>,
        <attribute_2>,
        <attribute_3>,

        {# SCD Type 2 metadata #}
        <effective_date> as effective_date,
        coalesce(
            lead(<effective_date>) over (partition by <natural_key> order by <effective_date>),
            '9999-12-31'::date
        ) as end_date,

        case
            when lead(<effective_date>) over (partition by <natural_key> order by <effective_date>) is null
            then true
            else false
        end as is_current

    from source_data

),

final as (

    select * from add_scd_columns

)

{% else %}

{#
    For facts: Add foreign keys and measures
#}
add_metrics as (

    select
        {# Primary key #}
        <fact_pk_column>,

        {# Foreign keys to dimensions #}
        <dim_key_1>,
        <dim_key_2>,
        <dim_key_3>,

        {# Degenerate dimensions (if any) #}
        <transaction_number>,
        <document_number>,

        {# Measures (additive) #}
        <quantity>,
        <amount>,
        <cost>,

        {# Calculated measures #}
        <amount> - <cost> as profit,
        <amount> / nullif(<quantity>, 0) as unit_price,

        {# Semi-additive measures #}
        <balance>,
        <inventory_level>,

        {# Dates #}
        <transaction_date>,
        <posting_date>,

        {# Metadata #}
        _loaded_at,
        _source_system

    from source_data

),

final as (

    select * from add_metrics

)

{% endif %}

select * from final

{#
    Testing Notes:
    - For dimensions: Test unique_key (surrogate_key or natural_key + effective_date)
    - For facts: Test relationships to all dimension foreign keys
    - Test not_null on primary keys
    - Test accepted_values on status/type columns
    - Add custom data quality tests as needed
#}
