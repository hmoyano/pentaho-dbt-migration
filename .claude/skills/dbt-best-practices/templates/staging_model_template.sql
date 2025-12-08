{{
    config(
        materialized='table',
        tags=['bronze', '<SOURCE_SYSTEM>']
    )
}}

{#
    Staging Model Template - Bronze Layer

    Purpose: Extract raw data from source systems with minimal transformation
    Layer: Bronze (staging__)
    Source: Pentaho adq_* files

    Guidelines:
    - Use {{ source() }} macro for source tables
    - Rename columns to standard naming (lowercase_with_underscores)
    - Cast data types if necessary for consistency
    - Do NOT apply business logic here (save for intermediate layer)
    - Add source system metadata (load_timestamp, source_system, etc.)
    - Keep transformations minimal and focused on standardization

    Example Usage:
    - adq_ekip_contracts.ktr → staging__ekip_contracts.sql
    - adq_status.ktr → staging__status.sql
#}

with source_data as (

    select * from {{ source('<SOURCE_SCHEMA>', '<SOURCE_TABLE>') }}

    {#
        If source has date filters or incremental logic from Pentaho:

        {% if var('incremental_date', none) %}
            where created_date >= '{{ var("incremental_date") }}'
        {% endif %}
    #}

),

renamed as (

    select
        -- Primary Key
        <ORIGINAL_PK_COLUMN> as <standard_pk_name>,

        -- Foreign Keys
        <original_fk_column> as <standard_fk_name>,

        -- Attributes
        <original_column_1> as <standard_column_1>,
        <original_column_2> as <standard_column_2>,
        <original_column_3> as <standard_column_3>,

        -- Dates (cast if needed for consistency)
        <original_date_column>::date as <standard_date_column>,
        <original_timestamp_column>::timestamp_ntz as <standard_timestamp_column>,

        -- Status/Flags
        <original_status> as status,

        -- Metadata
        current_timestamp() as _loaded_at,
        '<SOURCE_SYSTEM>' as _source_system

    from source_data

),

{#
    Optional: Add data quality filters if needed

filtered as (

    select *
    from renamed
    where <standard_pk_name> is not null  -- Remove invalid records
        and status is not null             -- Business requirement

),
#}

final as (

    select * from renamed
    {# or select * from filtered if using filter CTE #}

)

select * from final
