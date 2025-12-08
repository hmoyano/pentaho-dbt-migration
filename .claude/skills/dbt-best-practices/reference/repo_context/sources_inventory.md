# Existing Sources

**Generated**: 2025-11-20
**Repository**: {dbt_repository}/
**Source File**: models/bronze/sources.yml

---

## Source Configuration

**Source Name**: bronze
**Database**: TFSES_ANALYTICS
**Schema**: TFS_BRONZE
**Description**: Raw source data from AWS Glue → S3 → Snowflake

---

## Source Systems Overview

Total tables defined: **110 tables**

- **EKIP**: 57 tables (Core contract and customer system)
- **MILES**: 42 tables (Business partner and contract management)
- **TES**: 12 tables (Toyota España sales and catalog)
- **TFSLINE**: 9 tables (Asset and financial data)
- **TFSADMIN**: 3 tables (Promotional data)
- **PROFINANCE**: 9 tables (Dealer credit lines and regions)
- **CISCO**: 1 table (Legacy call center - replaced by 3CX)
- **3CX**: 1 table (Current call center system)
- **DBRISK**: 1 table (Risk database)
- **EDIASA**: 1 table (EDIASA customer data)
- **SEED**: 1 table (Reference data from seeds)

---

## EKIP Source System (57 tables)

### Core Business Tables
- EKIP_AFFAIRE - Contratos registrados en EKIP, contienen información de producto, cliente y estado
- EKIP_TIERS - Datos maestros de clientes EKIP
- EKIP_ELEMENT - Elementos físicos o lógicos asociados a los contratos
- EKIP_IMMOB - Información de activos inmovilizados (vehículos)
- EKIP_ELTIMM - Elementos de inmovilización asociados a los contratos

### Reference and Catalog Tables
- EKIP_ACODIFS - Catálogo maestro de códigos y valores de referencia en EKIP
- EKIP_LIB_ACODIFS - Catálogo de códigos y descripciones utilizadas en EKIP

### Financial and Accounting Tables
- EKIP_ARRAFF - Cierres mensuales de contratos en EKIP
- EKIP_DETARRLOY - Detalles contables de liquidaciones y terminaciones anticipadas en EKIP
- EKIP_TABECH - Tabla de planificación de cuotas (échéances) de contratos EKIP
- EKIP_SIMUL - Datos de simulaciones financieras de contratos EKIP
- EKIP_TABSIMUL - Simulaciones de condiciones financieras asociadas a contratos EKIP
- EKIP_PALLOY - Información de pagos o lotes de contratos en EKIP

### History and Tracking Tables
- EKIP_HISTOSTAT - Histórico de cambios de estado en EKIP
- EKIP_HIST_REGRTIERS - Histórico de relación cliente-grupo en EKIP
- EKIP_DETTIERS - Histórico de creación y modificaciones de clientes EKIP
- EKIP_HISTIEVEND - Histórico de cambios en EKIP
- EKIP_HISTIEREGEXT - Histórico de cambios en EKIP

### Dealer and Network Tables
- EKIP_TIERS_RESEAU - Datos maestros de clientes EKIP
- EKIP_REGRTIERS - Grupos de clientes EKIP
- EKIP_TIEDOSADM - Relaciones entre contratos EKIP y usuarios administrativos o comerciales
- EKIP_DISTREG - Tabla de EKIP
- EKIP_REGEEXT - Tabla de Ekip

### Address and Contact Tables
- EKIP_ADRESSE - Direcciones de clientes EKIP asociadas a los registros de TIERS
- EKIP_REFCOMM - Referencias de contacto de clientes EKIP

### Vehicle and Asset Tables
- EKIP_MATIMMA - Datos de matriculación e inmovilización de vehículos EKIP
- EKIP_PHOTOELEMENT - Instantáneas (fotografías) de elementos de contrato en EKIP
- EKIP_UMESSIMUL - Unidades de medida y parámetros utilizados en simulaciones EKIP
- EKIP_MAS_FUEL - Datos de combustible de vehículos EKIP
- EKIP_MAS_TFS_BODYWORK_TYPE - Datos de combustible de vehículos EKIP

### Administrative Tables
- EKIP_DOSADM - Cabeceras de expedientes administrativos en EKIP
- EKIP_DOSSMOD - Modificaciones y versiones de contratos EKIP
- EKIP_COMMANDE - Criterios y atributos asociados a objetos de negocio (contratos,clientes) en EKIP
- EKIP_CRITOBJ - Criterios y atributos asociados a objetos de negocio (contratos,clientes) en EKIP
- EKIP_SPECDATAOBJ_AFF - Datos específicos de contratos en EKIP (objetos AFF)
- EKIP_PERIODE - Catálogo de periodos contables y su estado de cierre en EKIP
- EKIP_UTILIS - Master table of EKIP users and their profiles
- EKIP_PROFILS_UTILISATEUR - User profiles and permissions in EKIP system
- EKIP_GAREXT - External guarantees associated with EKIP contracts

### TES Migration Tables (EKIP prefix but from TES system)
- EKIP_TFS_CRITOBJ_HIST_0TES - Tabla fuente proveniente del sistema Ekip
- EKIP_TFS_DEMANDES_0TES - Tabla fuente proveniente del sistema Ekip
- EKIP_TFS_OLD_DEMANDES_0TES - Historical credit requests/applications from TFS credit scoring system
- EKIP_TFS_OLD_HISTO_STAT_DEM_0TES - Historical status change tracking for credit requests in TFS system
- EKIP_TFS_OLD_SCO_DATA_RESPONSE_0TES - Historical credit score responses from TFS credit scoring system
- EKIP_TFS_PROVINCIAS_0TES - Tabla fuente proveniente del sistema Ekip
- EKIP_TFS_REGISTRATION_ACT_0TES - Tabla fuente proveniente del sistema Ekip
- EKIP_TFS_SPECDATAOBJ_AFF_HIST_0TES - Tabla fuente proveniente del sistema Ekip
- EKIP_TFS_SPECDATAOBJ_TIE_HIST_0TES - Tabla fuente proveniente del sistema Ekip
- EKIP_TFS_REMA_AFF_0TES - Refinancing data from EKIP for contract modifications
- EKIP_TFS_SCO_DATA_RESPONSE_0TES - Current credit score responses from TFS credit scoring system (GEN04_SCORE field)

---

## MILES Source System (42 tables)

### Business Partner Tables
- MILES_BUSINESSPARTNER - Socios de negocio (Business Partner) en MILES
- MILES_BUSINESSUNIT - Unidades de negocio asociadas a cada Business Partner en MILES
- MILES_D_BUSINESSPARTNER - Dimensión de business partners en MILES
- MILES_CUSTOMER - Clientes de MILES
- MILES_D_CUSTOMER - Dimensión de customers en MILES

### Contact Management Tables
- MILES_CONTACT - Contactos asociados a cada unidad de negocio en MILES
- MILES_CONTACTADDRESS - Contactos asociados a direcciones en cada unidad de negocio en MILES
- MILES_CONTACTCONTACTROLE - Relaciones entre contactos y sus roles dentro de MILES
- MILES_CONTACTROLE - Roles que puede asumir un contacto (Primary, Secondary, etc.) en MILES
- MILES_PERSON - Datos personales asociados a contactos del sistema MILES
- MILES_EMPLOYMENTHISTORY - Historico de empleados en MILES
- MILES_ADDRESS - Direcciones en MILES

### Contract Tables
- MILES_CONTRACT - Contratos registrados en el sistema MILES
- MILES_CONTRACTVERSION - Versiones de contrato y su vigencia en MILES
- MILES_DM_CONTRACTSTATE_DIM - Dimensión de estados de contrato en MILES
- MILES_LIFECYCLE - Lifecycle states and transitions in MILES
- MILES_LEASESERVICE - Miles lease service master table
- MILES_D_LEASESERVICE - Lease service dimension table in MILES
- MILES_LEASESERVICECOMPONENT - Lease service components and details in MILES

### Reference and Translation Tables
- MILES_SYSENUMERATION - Enumeraciones y catálogos del sistema MILES
- MILES_TRANSLATEDSTRING - Traducciones de textos multilingües en MILES
- MILES_LANGUAGE - Catálogo de idiomas disponibles en MILES
- MILES_GETENUMML - Tabla fuente proveniente del sistema Miles
- MILES_ISICCODE - Códigos de clasificación industrial (CNAE/ISIC) utilizados en MILES
- MILES_VATSETTING - VAT settings and tariff configuration in MILES

### Product and Catalog Tables
- MILES_PRODUCT - Miles product master table
- MILES_MAKE - Make in MILES
- MILES_MODEL - Models in MILES
- MILES_CATALOGVEHICLE - Vehicle catalog data in MILES
- MILES_CONFIGVEHICLE - Configured vehicles in MILES
- MILES_D_CONFIGVEHICLE - Configured vehicle dimension table in MILES
- MILES_CONFIGOPTION - Configuration options for vehicles in MILES
- MILES_CONFIGDISCOUNT - Configuration discounts for vehicles in MILES

### Fleet and Vehicle Management
- MILES_FLEETVEHICLE - Fleet vehicle master data in MILES
- MILES_VEHICLEORDER - Vehicle order details in MILES
- MILES_VEHICLEUSAGE - Vehicle usage tracking in MILES
- MILES_DELIVERYCOSTCOMPONENT - Delivery cost components for vehicles in MILES

### Quote and Order Management
- MILES_QUOTE - Miles quote master table
- MILES_DM_QUOTESTATUS_DIM - Dimensión de estados de cotización en MILES
- MILES_QUOTATIONTEMPLATE - Quotation templates master table in MILES
- MILES_ORDERITEM - Order line items in MILES
- MILES_ORDERS - Orders master table in MILES

### Credit and Risk Management
- MILES_CREDITSCORE - Credit score data for customers in MILES
- MILES_CREDITSCOREQUOTE - Credit score quotes for contracts in MILES

### Billing and Invoicing
- MILES_BILLINGITEM - Billing items for contracts in MILES
- MILES_OILBILLINGITEM - Oil billing items associated with billing items in MILES
- MILES_OUTGOINGINVOICE - Outgoing invoices master table in MILES
- MILES_OUTGOINGINVOICELINE - Outgoing invoice line items in MILES

### User and Account Management
- MILES_USERACCOUNT - User accounts and authentication data in MILES
- MILES_ACCOUNTMANAGER - Account managers assigned to business partners in MILES
- MILES_CUSTOMERACCOUNTMANAGER - Relationship between customers and account managers in MILES

### Relationship Management
- MILES_RELOBJECT - Relationship objects in MILES

---

## TES Source System (12 tables)

### Dimension Tables
- TES_DIMENSION_CUSTOMER - Tabla de Tes
- TES_DIMENSION_DEALERS - Tabla de Tes
- TES_DIMENSION_EMPLOYEES - Tabla de Tes
- TES_DIMENSION_INTERMEDIARIOS - Tabla de Tes
- TES_DIMENSION_PRODUCT - Tabla de Tes

### Fact Tables
- TES_FACT_SALE - Tabla de Tes

### Catalog Tables
- TES_CATALOG - Tabla de Tes
- TES_BODYWORK - Tabla de Tes
- TES_MAKE - Tabla de Tes
- TES_MODEL - Tabla de Tes

### Configuration Tables
- TES_GEARBOX - Tabla de Tes
- TES_GEARBOX_TYPE - Tabla de Tes

### Control Tables
- TES_LAST_DATA_LOADED - Tabla de Tes

---

## TFSLINE Source System (9 tables)

### Asset Tables
- TFSLINE_POS_ASSET - Información de activos físicos o vehículos vinculados a contratos TFSLine
- TFSLINE_POS_TESCAR_DATA - Datos complementarios del vehículo (TESCar) en TFSLine

### Financial Tables
- TFSLINE_POS_FINANCIAL - Datos financieros asociados a contratos y activos TFSLine
- TFSLINE_POS_FINANCIAL_DELETED - Datos financieros eliminados (soft-delete) en TFSLine

### Dealer Tables
- TFSLINE_POS_DEALERSHIP - Información de activos físicos o vehículos vinculados a contratos TFSLine

### History Tables
- TFSLINE_POS_HISTOSTAT - Historial de estados para contratos TFSLine

### User Tables
- TFSLINE_POS_USER - Información de usuarios y agentes en TFSLine

---

## TFSADMIN Source System (3 tables)

### Promotional Tables
- TFSADMIN_POS_X_I_PROMO - Tabla maestra de promociones en TFSADMIN
- TFSADMIN_POS_X_I_PROMO_PROP - Tabla de promociones de propuestas en TFSADMIN
- TFSADMIN_POS_X_I_PROMO_ELEMENT - Elementos de promociones en TFSADMIN

---

## PROFINANCE Source System (9 tables)

### Credit and Regional Tables
- PROFINANCE_LIGNE_DE_CREDIT - Tabla de profinance
- PROFINANCE_REGION_INT - Tabla de profinance
- PROFINANCE_REGION_EXT - Tabla de profinance
- PROFINANCE_FRANCHISE - Tabla de profinance
- PROFINANCE_ACTEUR - Tabla de profinance

### Product and Model Tables
- PROFINANCE_CATEGORIE_MODELE - Tabla de profinance
- PROFINANCE_MODELE_BIEN - Tabla de profinance
- PROFINANCE_SERIE_MARQUE - Tabla de profinance
- PROFINANCE_TU_ENERGIE - Tabla de profinance
- PROFINANCE_TU_MODELE_BIEN_AUTO - Tabla de profinance

---

## Other Source Systems

### CISCO (1 table - Legacy)
- CISCO_MAS_CC_CALL_DETAIL - Tabla que contiene el histórico de los datos de usuario Cisco. Este sistema fue reemplazado por c3x

### 3CX (1 table - Current)
- C3X_USERS - User data from 3CX phone system

### DBRISK (1 table)
- DBRISK_CLIENTES - Tabla que proviene de una base de datos access de riesgos

### EDIASA (1 table)
- EDIASA_CLIENTES - Tabla de cliente que proviene del sistema ediasa

### SEED (1 table - Reference Data)
- SEED_D_COMPANY - Company dimension reference data (loaded from seeds/d_company.csv)

---

## Usage in Models

### Most Referenced Sources

**EKIP_AFFAIRE** - Referenced in:
- stg_contracts (primary source)
- mas_contracts
- Multiple dealer and proposal models

**EKIP_TIERS** - Referenced in:
- stg_customers (primary source)
- mas_customers
- Multiple dimension models

**EKIP_ACODIFS & EKIP_LIB_ACODIFS** - Referenced in:
- stg_status (primary sources)
- stg_financial_product
- All models needing EKIP reference data lookups

**MILES_SYSENUMERATION & MILES_TRANSLATEDSTRING** - Referenced in:
- stg_status
- stg_miles_product
- Models needing Miles multilingual translations
- **DO NOT use with GETENUMML UDF** (broken - use explicit JOIN pattern instead)

**MILES_CONTRACT** - Referenced in:
- stg_miles_contract
- mas_miles_contract
- d_contract

**TES_DIMENSION_DEALERS** - Referenced in:
- stg_tes_dealer
- mas_tes_dealer
- d_dealer

---

## CRITICAL NOTES FOR AGENTS

### For dbt-model-generator Agent

When generating or modifying bronze/_sources.yml or models/bronze/sources.yml:

1. **FILE ALREADY EXISTS**: models/bronze/sources.yml contains all 110 tables
2. **USE APPEND MODE ONLY**: Never regenerate this file from scratch
3. **CHECK THIS INVENTORY FIRST**: Always verify table doesn't exist before adding
4. **PRESERVE DESCRIPTIONS**: Existing tables have Spanish/English descriptions - keep them
5. **SAME FORMAT**: Follow existing YAML structure (version: 2, sources list format)
6. **MAINTAIN ORDER**: Keep tables grouped by source system

### Source Reference Pattern

In models, always use:
```sql
{{ source('bronze', 'TABLE_NAME') }}
```

Never hardcode:
```sql
-- BAD - Never do this
TFSES_ANALYTICS.TFS_BRONZE.TABLE_NAME

-- GOOD - Always use source reference
{{ source('bronze', 'TABLE_NAME') }}
```

### Adding New Sources

If a new dimension requires additional source tables not in this list:

1. **Check this inventory first** - Table might already exist (110 tables defined!)
2. **Add to existing sources.yml** - Don't create new file
3. **Follow naming convention**:
   - EKIP_ prefix for EKIP tables
   - MILES_ prefix for Miles tables
   - TES_ prefix for TES tables
   - TFSLINE_ prefix for TFSLine tables
   - And so on...
4. **Add description** - Spanish or English, following existing pattern
5. **Maintain alphabetical order** within each source system group

### Source Documentation Status

Current documentation level:
- **EKIP**: 57/57 tables documented (mostly Spanish descriptions)
- **MILES**: 42/42 tables documented (mixed Spanish/English)
- **TES**: 12/12 tables documented (mostly generic "Tabla de Tes" - needs improvement)
- **TFSLINE**: 9/9 tables documented (Spanish descriptions)
- **TFSADMIN**: 3/3 tables documented (Spanish descriptions)
- **PROFINANCE**: 9/9 tables documented (generic "Tabla de profinance")
- **Other systems**: 5/5 tables documented

---

## Source Table Count: 110 TOTAL

This is the definitive list as of 2025-11-20. Any model generation should reference these sources, not create new source definitions unless absolutely necessary for new external tables not in this list.

**Key Takeaway**: Before adding ANY source table, check this list first. 99% of needed tables are already defined.
