# Proyecto de Migración Pentaho a DBT

Sistema automatizado de migración para convertir transformaciones de Pentaho Data Integration (Kettle) en modelos DBT listos para producción.

---

## 🚀 Inicio Rápido

### Probar Mejoras Localmente (AHORA)

```bash
# Probar mejoras sin operaciones git
/improve dim_approval_level
```

Crea modelos de prueba en `tfses-dbt-snowflake-3030-ai/` para comparación.

### Migración de Producción (Después de GitHub)

```bash
# Migración completa con operaciones git y CI/CD
/migrate dim_approval_level
```

Crea rama, hace commit, push y espera validación CI/CD.

### Verificar Estado de Migración

```bash
/migration-status dim_approval_level
```

---

## 📁 Estructura del Proyecto

```
3030-pentaho-dbt/
├── .claude/                           # Configuración de Claude Code
│   ├── agents/                        # Agentes IA para análisis y generación
│   ├── commands/                      # Comandos personalizados (/migrate, /improve)
│   └── skills/                        # Operaciones determinísticas y plantillas
├── config/                            # Archivos de configuración
│   ├── schema_registry.json          # Mapeo de variables y definiciones UDF
│   ├── TABLE_COUNT.csv               # Conteo de filas para optimización
│   └── tables_columns_info.csv       # Metadata de columnas
├── dimensions/                        # Metadata de migración por dimensión
│   └── <dimension>/
│       ├── metadata/                  # Resultados de análisis JSON
│       └── sql/                       # Archivos SQL traducidos
├── docs/                              # Documentación
│   └── GITHUB_CICD_WORKFLOW.md      # Guía de configuración CI/CD
├── pentaho-sources/                           # ENTRADA: Archivos fuente Pentaho
│   └── <dimension>/
│       ├── *.ktr                     # Transformaciones
│       └── *.kjb                     # Jobs
├── tfses-dbt-snowflake-3030/         # SALIDA: Repositorio DBT de producción
│   └── models/                        # Modelos DBT generados
├── archive/                           # Archivos antiguos archivados (limpieza)
└── Archivos de documentación principales
    ├── README.md                      # Este archivo
    ├── README_ES.md                   # Versión en español
    ├── CLAUDE.md                      # Contexto para Claude Code
    ├── MIGRATION_WORKFLOW.md          # Flujo de trabajo detallado
    └── SYSTEM_OVERVIEW.md             # Vista general de la arquitectura
```

---

## 📖 Documentación

- **[Guía del Flujo de Migración](MIGRATION_WORKFLOW.md)** - Guía completa paso a paso
- **[Vista General del Sistema](SYSTEM_OVERVIEW_ES.md)** - Arquitectura y componentes
- **[Contexto de Claude](CLAUDE.md)** - Contexto para Claude Code
- **[Guía CI/CD de GitHub](docs/GITHUB_CICD_WORKFLOW.md)** - Instrucciones de configuración CI/CD

---

## 🏗️ Arquitectura del Sistema

### Dos Flujos de Trabajo de Migración

| Comando | Propósito | Operaciones Git | Ubicación Salida | Cuándo Usar |
|---------|-----------|-----------------|------------------|-------------|
| `/improve` | Probar mejoras localmente | ❌ No | `tfses-dbt-snowflake-3030-ai/` | Antes de confirmar cambios |
| `/migrate` | Migración de producción | ✅ Sí | `tfses-dbt-snowflake-3030/` | Después de configurar GitHub |

### Flujo del Pipeline (7 Pasos)

```
Paso 0:   Configuración Git (crear rama o copiar repo)    ← ¡NUEVO!
Paso 0.5: Análisis del Repositorio (escanear existente)   ← ¡NUEVO!
Paso 1:   Parsear Archivos Pentaho
Paso 2:   Analizar Transformaciones
Paso 3:   Construir Dependencias
Paso 4:   Traducir SQL
Paso 5:   Generar Modelos DBT
Paso 6:   Validar y Push (si /migrate)
```

### Relaciones entre Agentes

```
                    repo-analyzer (¡NUEVO!)
                         ↓
                [Crea archivos de contexto]
                         ↓
pentaho-parser → pentaho-analyzer → dependency-graph-builder
       ↓                ↓                      ↓
              sql-translator (lee todo)
                         ↓
            dbt-model-generator (evita duplicados)
                         ↓
            quality-validator (ops git si /migrate)
```

### Componentes

**Agentes del Flujo Principal** (Razonamiento impulsado por IA):
1. `repo-analyzer` - Escanea repo DBT, identifica modelos compartidos ← ¡NUEVO!
2. `pentaho-analyzer` - Resuelve variables, clasifica tablas
3. `dependency-graph-builder` - Detecta dependencias circulares
4. `sql-translator` - Oracle → Snowflake con expansión UDF
5. `dbt-model-generator` - Crea modelos, omite compartidos existentes
6. `quality-validator` - Validación estática + manejo git/CI/CD

**Agentes Auxiliares** (Solucionadores de problemas - bajo demanda):
- `dependency-resolver` - Corrige dependencias circulares
- `pentaho-deep-analyzer` - Análisis profundo de XML Pentaho
- `pentaho-cross-reference` - Encuentra patrones similares
- `sql-function-lookup` - Investiga funciones desconocidas
- `dbt-validator-fixer` - Auto-corrige errores DBT

Ver [docs/HELPER_AGENTS.md](docs/HELPER_AGENTS.md) para cuándo usar agentes auxiliares.

**Skills** (Operaciones determinísticas):
- `pentaho-parser` - Extrae metadata de XML Pentaho
- `oracle-snowflake-rules` - Patrones de traducción SQL
- `dbt-best-practices` - Plantillas y convenciones de nombres

**Comandos** (Orquestadores de flujo de trabajo):
- `/improve <dimension>` - Prueba mejoras localmente
- `/migrate <dimension>` - Migración de producción con git
- `/migration-status [dimension]` - Verificar progreso

---

## 🎯 Prerrequisitos

### Requeridos
- Claude Code instalado
- Python 3.8+ (para skill pentaho-parser)

### Opcionales (para validación completa)
- DBT instalado localmente
- Conexión a Snowflake configurada
- Cuenta GitHub (para CI/CD)

---

## 🔧 Configuración

### 1. Clonar Repositorio DBT (para /migrate)

```bash
git clone https://github.com/tu-org/tfses-dbt-snowflake-3030.git
```

### 2. Configurar Mapeo de Variables

Editar `config/schema_registry.json`:

```json
{
  "variables": {
    "EKIP_SCHEMA": {
      "snowflake_name": "EKIP",
      "type": "external",
      "layer": "bronze"
    }
  }
}
```

### 3. Agregar Archivos Pentaho

Colocar archivos `.ktr` y `.kjb` en `pentaho-sources/<dimension>/`

---

## 🏃 Flujo de Trabajo de Migración

### Migración Automática

```bash
/migrate dim_approval_level
```

Ejecuta el pipeline completo de 6 pasos automáticamente.

### Ejecución Manual Paso a Paso

Ejecutar cada paso individualmente para más control:

```bash
# Paso 1: Parsear
/pentaho-parser dim_approval_level

# Paso 2: Analizar
[Pedir a Claude ejecutar agente pentaho-analyzer]

# Paso 3: Construir gráfico de dependencias
[Pedir a Claude ejecutar agente dependency-graph-builder]

# Paso 4: Traducir SQL
[Pedir a Claude ejecutar agente sql-translator]

# Paso 5: Generar modelos DBT
[Pedir a Claude ejecutar agente dbt-model-generator]

# Paso 6: Validar
[Pedir a Claude ejecutar agente quality-validator]
```

Ver [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md) para instrucciones detalladas.

---

## ✅ Validación y Pruebas

Después de que la migración complete:

### 1. Verificar Estado de Validación

```bash
/migration-status dim_approval_level
```

### 2. Revisar Reporte de Validación

```bash
cat dimensions/dim_approval_level/metadata/validation_report.json | jq
```

### 3. Para /migrate: Esperar CI/CD

Después del push, el sistema mostrará:

```
🔄 GitHub Actions CI/CD está ejecutándose...

📋 Próximos pasos:
1. Esperar 2-5 minutos para que CI/CD complete
2. Dime el resultado:
   - Di 'CI passed' si todos los checks ✅
   - Di 'CI failed' si los checks fallan ❌

¡Manejaré cualquier error automáticamente!
```

### 4. Para /improve: Comparar Resultados

```bash
# Comparación visual (VSCode)
code --diff tfses-dbt-snowflake-3030 tfses-dbt-snowflake-3030-ai

# Comparación línea de comandos
diff -r tfses-dbt-snowflake-3030/models tfses-dbt-snowflake-3030-ai/models
```

---

## 📊 Archivos de Salida

### Metadata (Por Dimensión)

Ubicada en `dimensions/<dimension>/metadata/`:

| Archivo | Fuente | Contiene |
|---------|--------|----------|
| `pentaho_raw.json` | pentaho-parser | Metadata Pentaho parseada |
| `pentaho_analyzed.json` | pentaho-analyzer | Resolución de variables, complejidad |
| `dependency_graph.json` | dependency-graph-builder | Dependencias, orden de ejecución |
| `translation_metadata.json` | sql-translator | Detalles de traducción SQL |
| `dbt_generation_report.json` | dbt-model-generator | Resumen de modelos generados |
| `validation_report.json` | quality-validator | Resultados de validación de calidad |

### Modelos DBT

Ubicados en `tfses-dbt-snowflake-3030/models/` (o `-ai/` para /improve):

| Capa | Directorio | Patrón de Archivo | Ejemplo |
|------|------------|-------------------|---------|
| Bronze | `bronze/` | `_sources.yml` | Definiciones de fuentes |
| Silver ADQ | `silver/silver_adq/` | `stg_*.sql` | `stg_contracts.sql` |
| Silver MAS | `silver/silver_mas/` | `mas_*.sql` | `mas_contracts.sql` |
| Gold | `gold/` | `d_*.sql`, `f_*.sql` | `d_approval_level.sql` |

---

## 🚨 Solución de Problemas

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| "Variable no encontrada" | Variable no en registry | Agregar a `schema_registry.json` |
| "Dependencia circular" | Ciclo en transformaciones | Usar agente `dependency-resolver` |
| "Función desconocida" | UDF personalizada | Agregar a `schema_registry.json` |
| "CI/CD falla" | Error en modelo DBT | Decir "CI failed", agente lo arreglará |

### Agentes Auxiliares

Cuando el flujo principal encuentra problemas:

```bash
# Ejemplo: Función SQL desconocida
Task(
    subagent_type="sql-function-lookup",
    prompt="Investigar función CUSTOM_CALC"
)
```

Ver [docs/HELPER_AGENTS.md](docs/HELPER_AGENTS.md) para lista completa.

---

## 📈 Métricas de Éxito

- ✅ 100% variables resueltas
- ✅ 100% modelos documentados
- ✅ 100% cobertura de pruebas
- ✅ Validación estática PASSED
- ✅ CI/CD todos los checks verdes

---

## 🤝 Contribuir

1. Crear rama desde `main`
2. Hacer cambios
3. Probar con `/improve`
4. Crear PR cuando esté listo

---

## 📄 Licencia

Proyecto interno - Equipo de Ingeniería de Datos

---

**Versión**: 2.0
**Actualizado**: 2025-10-25
**Mantenido por**: Equipo de Ingeniería de Datos